# app/seguranca.py
"""
Configuração de segurança do AvaliaAi UnB (issue #110).

Uso, dentro de create_app(), depois de criar o Flask e ANTES de registrar os blueprints:

    from app.seguranca import configurar_seguranca
    configurar_seguranca(app)

O que isso faz:
  1. SECRET_KEY vem do ambiente; em produção a aplicação não sobe sem ela.
  2. Cookies (sessão do Flask e os do Supabase) com Secure, HttpOnly e SameSite.
  3. Headers de segurança em toda resposta.
  4. Proteção CSRF em todo POST/PUT/PATCH/DELETE (Flask-WTF).
  5. Limite de requisições (Flask-Limiter), aplicado nas rotas via os decoradores abaixo.
"""
import logging
import os
import secrets

from urllib.parse import urlparse, urljoin
from flask import jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFError, CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

log = logging.getLogger(__name__)

csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)

TAMANHO_MINIMO_CHAVE = 32
CHAVES_FRACAS = {"changeme", "secret", "dev", "development", "test", "senha", "password"}

# Content-Security-Policy restritiva: só recursos do próprio domínio.
# Se algum template usar CDN (Bootstrap, Google Fonts...) ou <script>/<style> inline,
# o navegador vai bloquear e o console mostra o motivo; ajuste aqui ou via config CSP.
CSP_PADRAO = "; ".join([
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self'",
    "img-src 'self' data:",
    "font-src 'self'",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])


# --------------------------------------------------------------------------- limites
def chave_usuario_ou_ip():
    """Chave de limite por usuário logado (IPs da UnB são compartilhados); IP se anônimo."""
    from app.controllers.session_controller import obter_usuario_atual  # evita import circular
    usuario = obter_usuario_atual()
    return f"usuario:{usuario['id']}" if usuario else get_remote_address()


# Só POST é limitado: renderizar o formulário (GET) não é o alvo de abuso.
limitar_login_por_ip = limiter.limit("10 per minute;50 per hour", methods=["POST"], scope="login-ip")
limitar_cadastro = limiter.limit("5 per hour", methods=["POST"], scope="cadastro")
limitar_avaliacao = limiter.limit("20 per hour", key_func=chave_usuario_ou_ip,
                                  methods=["POST"], scope="avaliacao")


# --------------------------------------------------------------------------- configuração
def _verdadeiro(valor):
    return str(valor or "").strip().lower() in {"1", "true", "yes", "on", "sim"}


def _configurar_secret_key(app):
    chave = app.config.get("SECRET_KEY") or os.environ.get("SECRET_KEY", "").strip()
    desenvolvimento = app.debug or app.testing

    if not chave:
        if not desenvolvimento:
            raise RuntimeError(
                "SECRET_KEY não definida. Em produção ela é obrigatória. "
                'Gere uma com: python -c "import secrets; print(secrets.token_hex(32))" '
                "e defina a variável de ambiente SECRET_KEY."
            )
        # Só em dev/testes: chave aleatória por processo (sessões caem ao reiniciar).
        chave = secrets.token_hex(32)
        log.warning("SECRET_KEY ausente: usando chave temporária (apenas desenvolvimento).")
    elif not desenvolvimento and (len(chave) < TAMANHO_MINIMO_CHAVE
                                  or chave.lower() in CHAVES_FRACAS):
        raise RuntimeError(
            f"SECRET_KEY fraca: use pelo menos {TAMANHO_MINIMO_CHAVE} caracteres aleatórios."
        )
    app.config["SECRET_KEY"] = chave


def _configurar_cookies(app):
    # Secure exige HTTPS; só relaxamos em desenvolvimento local (http://localhost).
    seguro = not app.debug
    app.config.update(
        SESSION_COOKIE_SECURE=seguro,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        COOKIE_SECURE=seguro,   # lido por session_controller para os cookies do Supabase
    )


def _configurar_headers(app):
    app.config.setdefault("CSP", CSP_PADRAO)

    @app.after_request
    def _headers_de_seguranca(response):
        response.headers.setdefault("Content-Security-Policy", app.config["CSP"])
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy",
                                    "camera=(), microphone=(), geolocation=()")
        if request.is_secure and not app.debug:
            response.headers.setdefault("Strict-Transport-Security",
                                        "max-age=31536000; includeSubDomains")
        return response


def _configurar_csrf(app):
    app.config.setdefault("WTF_CSRF_TIME_LIMIT", 12 * 60 * 60)  # igual à duração do login
    csrf.init_app(app)

    @app.errorhandler(CSRFError)
    def _csrf_invalido(erro):
        if request.accept_mimetypes.best == "application/json":
            return jsonify({"erro": "Token CSRF ausente ou inválido."}), 400
        return ("Sua sessão de formulário expirou ou o token CSRF é inválido. "
                "Volte, recarregue a página e tente de novo."), 400


def _configurar_limites(app):
    app.config.setdefault("RATELIMIT_STORAGE_URI",
                          os.environ.get("RATELIMIT_STORAGE_URI", "memory://"))
    app.config.setdefault("RATELIMIT_HEADERS_ENABLED", True)
    if (os.getenv("APP_ENV", "").strip().lower() == "production"
            and app.config["RATELIMIT_STORAGE_URI"].startswith("memory://")):
        raise RuntimeError("Configure RATELIMIT_STORAGE_URI compartilhado em produção.")
    limiter.init_app(app)

    if app.config["RATELIMIT_STORAGE_URI"].startswith("memory://") and not app.debug:
        log.warning("Rate limit em memória: cada worker conta separado. "
                    "Em produção com vários workers, defina RATELIMIT_STORAGE_URI (ex.: Redis).")

    @app.errorhandler(429)
    def _limite_excedido(erro):
        mensagem = "Muitas tentativas. Aguarde um pouco e tente novamente."
        if request.accept_mimetypes.best == "application/json":
            return jsonify({"erro": mensagem}), 429
        return mensagem, 429


def _configurar_proxy(app):
    """Atrás de proxy reverso (Render, Railway, nginx...) o IP real vem em X-Forwarded-For.
    Sem isso todos os usuários teriam o mesmo IP e dividiriam o mesmo limite.
    Defina PROXY_HOPS com o número de proxies confiáveis à frente da app (normalmente 1)."""
    saltos = int(os.environ.get("PROXY_HOPS", "0") or 0)
    if saltos > 0:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=saltos, x_proto=saltos, x_host=saltos)


def configurar_seguranca(app):
    _configurar_proxy(app)
    _configurar_secret_key(app)
    _configurar_cookies(app)
    _configurar_headers(app)
    _configurar_csrf(app)
    _configurar_limites(app)
    return app


def is_safe_url(target):
    """
    Garante que a URL de redirecionamento é segura (mesmo domínio ou caminho relativo),
    prevenindo ataques de Open Redirect e bypass com barra invertida.
    """
    if not target or '\\' in target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc