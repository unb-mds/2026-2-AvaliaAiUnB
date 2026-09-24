# app/controllers/session_controller.py
"""
Controlador de sessão do AvaliaAi UnB.

Responsabilidades (conforme requisitos):
  1. Criação da sessão (após login validado)
  2. Identificação do usuário autenticado (a partir da requisição atual)
  3. Proteção das rotas (decorator @login_required)
  4. Logout (encerramento da sessão)

Estratégia:
  - Sessão NÃO fica só no cookie assinado do Flask. Um token aleatório e
    opaco é gerado, seu HASH (SHA-256) é salvo na tabela `sessoes` do
    SQLite, e o token puro é enviado ao navegador em um cookie httponly.
  - Isso permite: revogar sessões no servidor a qualquer momento (logout
    remoto, "sair de todos os dispositivos", expiração forçada), sem
    depender apenas do que está no cookie.
  - O cookie nunca guarda o token puro em texto "reaproveitável" no banco:
    se o banco vazar, os tokens de sessão continuam inúteis (estão
    hasheados), igual se faz com senhas.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import request, g, jsonify, redirect, url_for

from app.database import get_db_connection

# ---------------------------------------------------------------------------
# Configurações da sessão
# ---------------------------------------------------------------------------

NOME_COOKIE_SESSAO = "avaliaai_session"
DURACAO_SESSAO = timedelta(hours=12)   # tempo de vida do token de sessão


def _hash_token(token: str) -> str:
    """Gera o hash SHA-256 do token (o que é salvo no banco)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# 1. Criação da sessão
# ---------------------------------------------------------------------------

def criar_sessao(usuario_id: int, response):
    """
    Cria uma nova sessão para o usuário autenticado.

    - Gera um token aleatório e seguro (256 bits de entropia).
    - Persiste o hash do token na tabela `sessoes`, com data de expiração.
    - Define o cookie de sessão na resposta HTTP (httponly + samesite).

    Deve ser chamada logo após validar as credenciais no controller de
    login (ex.: após checar a senha com check_password_hash).

    Parâmetros:
        usuario_id: id do usuário que acabou de se autenticar.
        response:   objeto Response do Flask (o cookie é anexado nele).

    Retorna:
        O mesmo objeto `response`, já com o cookie de sessão definido.
    """
    token = secrets.token_hex(32)  # token puro, só existe aqui e no cookie
    token_hash = _hash_token(token)
    expira_em = _agora_utc() + DURACAO_SESSAO

    conexao = get_db_connection()
    try:
        conexao.execute(
            """
            INSERT INTO sessoes (token_hash, usuario_id, expira_em, user_agent, ip_origem)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                token_hash,
                usuario_id,
                expira_em.isoformat(),
                request.headers.get("User-Agent", ""),
                request.remote_addr,
            ),
        )
        conexao.commit()
    finally:
        conexao.close()

    response.set_cookie(
        NOME_COOKIE_SESSAO,
        token,
        httponly=True,       # inacessível via JavaScript (mitiga XSS)
        secure=True,         # só enviado em HTTPS (exigido pelo projeto)
        samesite="Lax",      # mitiga CSRF em navegação normal
        max_age=int(DURACAO_SESSAO.total_seconds()),
    )
    return response


# ---------------------------------------------------------------------------
# 2. Identificação do usuário autenticado
# ---------------------------------------------------------------------------

def obter_usuario_atual():
    """
    Identifica o usuário autenticado na requisição atual, a partir do
    cookie de sessão.

    Retorna:
        um sqlite3.Row com os dados do usuário (id, nome, email — sem a
        senha), ou None se não houver sessão válida (ausente, inválida
        ou expirada).

    O resultado é cacheado em `flask.g` durante a requisição, para que
    chamar essa função várias vezes na mesma request não gere consultas
    repetidas ao banco.
    """
    if hasattr(g, "usuario_atual"):
        return g.usuario_atual

    token = request.cookies.get(NOME_COOKIE_SESSAO)
    if not token:
        g.usuario_atual = None
        return None

    token_hash = _hash_token(token)

    conexao = get_db_connection()
    try:
        sessao = conexao.execute(
            "SELECT * FROM sessoes WHERE token_hash = ?", (token_hash,)
        ).fetchone()

        if sessao is None:
            g.usuario_atual = None
            return None

        expira_em = datetime.fromisoformat(sessao["expira_em"])
        if _agora_utc() > expira_em:
            # sessão expirada: já aproveita para limpar do banco
            conexao.execute("DELETE FROM sessoes WHERE id = ?", (sessao["id"],))
            conexao.commit()
            g.usuario_atual = None
            return None

        # Observação: a tabela `usuarios` do projeto tem apenas
        # id, nome, email, senha — por isso não selecionamos "criado_em"
        # aqui (essa coluna não existe no schema atual).
        usuario = conexao.execute(
            "SELECT id, nome, email FROM usuarios WHERE id = ?",
            (sessao["usuario_id"],),
        ).fetchone()
    finally:
        conexao.close()

    g.usuario_atual = usuario
    return usuario


# ---------------------------------------------------------------------------
# 3. Proteção das rotas
# ---------------------------------------------------------------------------

def login_required(view_func):
    """
    Decorator para proteger rotas que exigem usuário autenticado.

    Uso:
        @app.route("/perfil")
        @login_required
        def perfil():
            usuario = obter_usuario_atual()
            ...

    Comportamento:
        - Se houver sessão válida, chama a view normalmente.
        - Se não houver, responde 401 (para chamadas de API/JSON) ou
          redireciona para a tela de login (para navegação normal),
          conforme o cabeçalho Accept da requisição.
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        usuario = obter_usuario_atual()
        if usuario is None:
            if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
                return jsonify({"erro": "Não autenticado"}), 401
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# 4. Logout
# ---------------------------------------------------------------------------

def encerrar_sessao(response):
    """
    Encerra a sessão do usuário atual (logout).

    - Remove o registro da sessão no banco (revogação real do lado do
      servidor, não só apagar o cookie do navegador).
    - Limpa o cookie de sessão na resposta.

    Parâmetros:
        response: objeto Response do Flask.

    Retorna:
        O mesmo `response`, já sem o cookie de sessão.
    """
    token = request.cookies.get(NOME_COOKIE_SESSAO)
    if token:
        token_hash = _hash_token(token)
        conexao = get_db_connection()
        try:
            conexao.execute("DELETE FROM sessoes WHERE token_hash = ?", (token_hash,))
            conexao.commit()
        finally:
            conexao.close()

    response.delete_cookie(NOME_COOKIE_SESSAO)
    return response


# ---------------------------------------------------------------------------
# Manutenção (opcional, mas recomendado)
# ---------------------------------------------------------------------------

def limpar_sessoes_expiradas() -> int:
    """
    Remove do banco todas as sessões já expiradas.

    Pode ser chamada periodicamente (ex.: um job agendado, ou no início
    de algumas requisições) para manter a tabela `sessoes` enxuta.

    Retorna o número de sessões removidas.
    """
    agora = _agora_utc().isoformat()
    conexao = get_db_connection()
    try:
        cursor = conexao.execute("DELETE FROM sessoes WHERE expira_em < ?", (agora,))
        conexao.commit()
        return cursor.rowcount
    finally:
        conexao.close()