# app/controllers/session_controller.py
"""
Controlador de sessão do AvaliaAi UnB, apoiado no Supabase Auth.

  1. criar_sessao: grava os tokens do Supabase em cookies httponly
  2. obter_usuario_atual: identifica o usuário a partir dos cookies
  3. login_required: protege rotas
  4. encerrar_sessao: logout com revogação no servidor do Supabase

O access token (JWT, validade curta) é validado no Supabase a cada requisição; se
expirou, o refresh token renova a sessão e os cookies novos seguem na resposta.
"""
from datetime import timedelta
from functools import wraps

from flask import g, jsonify, redirect, request, url_for

from app.repositorio import repositorios

COOKIE_ACESSO = "avaliaai_session"
COOKIE_RENOVACAO = "avaliaai_refresh"
DURACAO_COOKIE = timedelta(hours=12)


def _definir_cookies(response, sessao):
    for nome, valor in ((COOKIE_ACESSO, sessao["access_token"]),
                        (COOKIE_RENOVACAO, sessao["refresh_token"])):
        response.set_cookie(
            nome, valor,
            httponly=True,       # inacessível via JavaScript (mitiga XSS)
            secure=True,         # só enviado em HTTPS (exigido pelo projeto)
            samesite="Lax",      # mitiga CSRF em navegação normal
            max_age=int(DURACAO_COOKIE.total_seconds()),
        )
    return response


def criar_sessao(sessao: dict, response):
    """Anexa à resposta os cookies da sessão devolvida por UsuarioRepository.autenticar."""
    return _definir_cookies(response, sessao)


def obter_usuario_atual():
    """Dict com id, nome, email e username do usuário logado, ou None. Cacheado em flask.g."""
    if hasattr(g, "usuario_atual"):
        return g.usuario_atual

    usuarios = repositorios().usuarios
    g.usuario_atual = None
    acesso = request.cookies.get(COOKIE_ACESSO)
    renovacao = request.cookies.get(COOKIE_RENOVACAO)

    if acesso:
        g.usuario_atual = usuarios.usuario_do_token(acesso)
    if g.usuario_atual is None and renovacao:
        nova = usuarios.renovar(renovacao)
        if nova:
            g.usuario_atual = usuarios.usuario_do_token(nova["access_token"])
            if g.usuario_atual:
                g.sessao_renovada = nova   # os cookies novos saem em registrar_renovacao
    return g.usuario_atual


def registrar_renovacao(app):
    @app.after_request
    def _enviar_cookies_renovados(response):
        nova = g.pop("sessao_renovada", None)
        if nova:
            _definir_cookies(response, nova)
        return response


def login_required(view_func):
    """401 JSON para clientes de API ou redirecionamento ao login para navegadores."""
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if obter_usuario_atual() is None:
            if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
                return jsonify({"erro": "Não autenticado"}), 401
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)
    return wrapper


def encerrar_sessao(response):
    """Revoga a sessão no Supabase e apaga os cookies."""
    acesso = request.cookies.get(COOKIE_ACESSO)
    if acesso:
        repositorios().usuarios.encerrar(acesso)
    g.pop("sessao_renovada", None)
    response.delete_cookie(COOKIE_ACESSO)
    response.delete_cookie(COOKIE_RENOVACAO)
    return response
