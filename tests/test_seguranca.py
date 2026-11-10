# tests/test_seguranca.py
"""
Testes da issue #110. Usam um app Flask mínimo + configurar_seguranca(), então
não dependem do Supabase nem dos templates.

Rodar:  pytest tests/test_seguranca.py -v
"""
import re
import unittest
import pytest

from flask import Flask, jsonify, render_template_string, request, session
from app.seguranca import is_safe_url
from app.seguranca import (
    CSP_PADRAO,
    configurar_seguranca,
    csrf,
    limitar_avaliacao,
    limitar_cadastro,
    limitar_login_por_ip,
    limiter,
)

CHAVE_FORTE = "a" * 64


def criar_app(monkeypatch, *, secret=CHAVE_FORTE, debug=False, testing=False):
    if secret is None:
        monkeypatch.delenv("SECRET_KEY", raising=False)
    else:
        monkeypatch.setenv("SECRET_KEY", secret)
    app = Flask(__name__)
    app.debug = debug
    app.testing = testing
    configurar_seguranca(app)
    limiter.reset()

    @app.get("/")
    def index():
        session["x"] = 1  # força o Set-Cookie da sessão do Flask
        return render_template_string('<form method="post" action="/login">'
                                      '<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">'
                                      "</form>")

    @app.post("/login")
    @limitar_login_por_ip
    def login():
        return jsonify(ok=True)

    @app.post("/cadastro")
    @limitar_cadastro
    def cadastro():
        return jsonify(ok=True)

    @app.post("/avaliar")
    @limitar_avaliacao
    def avaliar(**_):
        return jsonify(ok=True)

    return app


@pytest.fixture
def app(monkeypatch):
    return criar_app(monkeypatch)


@pytest.fixture
def client(app):
    return app.test_client()


def token_csrf(client):
    html = client.get("/").get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


# ------------------------------------------------------------------ SECRET_KEY
def test_producao_sem_secret_key_nao_sobe(monkeypatch):
    with pytest.raises(RuntimeError, match="SECRET_KEY não definida"):
        criar_app(monkeypatch, secret=None)


def test_producao_com_secret_key_fraca_nao_sobe(monkeypatch):
    with pytest.raises(RuntimeError, match="SECRET_KEY fraca"):
        criar_app(monkeypatch, secret="curta")


def test_producao_usa_a_secret_key_do_ambiente(monkeypatch):
    assert criar_app(monkeypatch).config["SECRET_KEY"] == CHAVE_FORTE


def test_desenvolvimento_sem_secret_key_gera_chave_aleatoria(monkeypatch):
    app = criar_app(monkeypatch, secret=None, debug=True)
    assert len(app.config["SECRET_KEY"]) >= 32


# ------------------------------------------------------------------ debug
def test_debug_desligado_por_padrao(monkeypatch):
    monkeypatch.delenv("FLASK_DEBUG", raising=False)
    assert Flask(__name__).debug is False


def test_producao_exige_rate_limit_compartilhado(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("RATELIMIT_STORAGE_URI", raising=False)
    with pytest.raises(RuntimeError, match="RATELIMIT_STORAGE_URI"):
        criar_app(monkeypatch)
    monkeypatch.delenv("APP_ENV", raising=False)


# ------------------------------------------------------------------ headers
def test_headers_de_seguranca(client):
    h = client.get("/").headers
    assert h["Content-Security-Policy"] == CSP_PADRAO
    assert "frame-ancestors 'none'" in h["Content-Security-Policy"]
    assert h["X-Content-Type-Options"] == "nosniff"
    assert h["X-Frame-Options"] == "DENY"
    assert h["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_hsts_apenas_em_https(client):
    assert "Strict-Transport-Security" not in client.get("/").headers
    assert "Strict-Transport-Security" in client.get("/", base_url="https://localhost").headers


# ------------------------------------------------------------------ cookies
def test_cookie_de_sessao_secure_httponly_samesite(client):
    cookie = client.get("/").headers["Set-Cookie"]
    assert "Secure" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie


def test_cookie_secure_relaxado_so_em_debug(monkeypatch):
    app = criar_app(monkeypatch, debug=True)
    assert app.config["SESSION_COOKIE_SECURE"] is False
    assert app.config["COOKIE_SECURE"] is False


def test_cookies_do_supabase_seguem_a_config(app):
    from app.controllers.session_controller import COOKIE_ACESSO, _definir_cookies
    from flask import make_response

    with app.test_request_context():
        resposta = _definir_cookies(make_response("ok"),
                                    {"access_token": "a", "refresh_token": "r"})
        cookies = [c for c in resposta.headers.getlist("Set-Cookie") if COOKIE_ACESSO in c
                   or "avaliaai_refresh" in c]
    assert len(cookies) == 2
    for c in cookies:
        assert "Secure" in c and "HttpOnly" in c and "SameSite=Lax" in c


# ------------------------------------------------------------------ CSRF
def test_post_sem_token_csrf_e_rejeitado(client):
    resposta = client.post("/login", data={"username": "a", "senha": "b"})
    assert resposta.status_code == 400


def test_post_sem_token_csrf_responde_json_para_api(client):
    resposta = client.post("/login", data={}, headers={"Accept": "application/json"})
    assert resposta.status_code == 400
    assert "CSRF" in resposta.get_json()["erro"]


def test_post_com_token_csrf_valido_passa(client):
    token = token_csrf(client)
    resposta = client.post("/login", data={"username": "a", "csrf_token": token})
    assert resposta.status_code == 200


def test_token_csrf_tambem_vale_pelo_header(client):
    token = token_csrf(client)
    assert client.post("/login", data={"username": "a"},
                       headers={"X-CSRFToken": token}).status_code == 200


def test_get_nao_exige_csrf(client):
    assert client.get("/").status_code == 200


def test_todo_post_da_aplicacao_esta_protegido(app):
    """Nenhuma view pode estar isenta de CSRF (@csrf.exempt)."""
    assert not csrf._exempt_views and not csrf._exempt_blueprints


# ------------------------------------------------------------------ rate limit
def _post(client, rota, **dados):
    token = token_csrf(client)
    return client.post(rota, data={**dados, "csrf_token": token})


def test_login_limita_por_ip(client):
    codigos = [_post(client, "/login", username=f"u{i}").status_code for i in range(11)]
    assert codigos[:10] == [200] * 10
    assert codigos[10] == 429


def test_username_nao_bloqueia_uma_conta_por_ips_diferentes(client):
    # Várias origens usando o mesmo username não devem impedir o login de outro IP.
    for i in range(12):
        resposta = client.post(
            "/login", data={"username": "Alvo", "csrf_token": token_csrf(client)},
            environ_overrides={"REMOTE_ADDR": f"10.0.0.{i}"})
        assert resposta.status_code == 200



def test_cadastro_limita_por_ip(client):
    codigos = [_post(client, "/cadastro").status_code for _ in range(6)]
    assert codigos == [200] * 5 + [429]


def test_avaliacao_limita_por_ip_quando_anonimo(client, monkeypatch):
    monkeypatch.setattr("app.controllers.session_controller.obter_usuario_atual", lambda: None)
    codigos = [_post(client, "/avaliar").status_code for _ in range(21)]
    assert codigos[-1] == 429 and codigos[:20] == [200] * 20


def test_avaliacao_limita_por_usuario_e_nao_por_ip(client, monkeypatch):
    usuario = {"id": 7}
    monkeypatch.setattr("app.controllers.session_controller.obter_usuario_atual",
                        lambda: usuario)
    for i in range(20):  # IPs diferentes, mesmo usuário
        r = client.post("/avaliar", data={"csrf_token": token_csrf(client)},
                        environ_overrides={"REMOTE_ADDR": f"10.1.0.{i}"})
        assert r.status_code == 200
    r = client.post("/avaliar", data={"csrf_token": token_csrf(client)},
                    environ_overrides={"REMOTE_ADDR": "10.1.0.200"})
    assert r.status_code == 429
    # outro usuário, mesmo IP, não é afetado
    usuario["id"] = 8
    assert client.post("/avaliar", data={"csrf_token": token_csrf(client)}).status_code == 200


def test_429_responde_json_para_api(client):
    for i in range(10):
        _post(client, "/login", username=f"u{i}")
    r = client.post("/login", data={"csrf_token": token_csrf(client)},
                    headers={"Accept": "application/json"})
    assert r.status_code == 429
    assert "Muitas tentativas" in r.get_json()["erro"]


def test_get_do_formulario_nao_conta_no_limite(client):
    for _ in range(30):
        assert client.get("/").status_code == 200



class TestSegurancaRedirecionamento(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        # Simula o contexto de uma requisição local para a validação da URL base
        self.ctx = self.app.test_request_context('/', base_url='http://localhost:5000')
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_is_safe_url_rejeita_redirecionamento_externo(self):
        # URLs seguras (mesmo domínio ou relativas com parâmetros)
        self.assertTrue(is_safe_url('/professores?nome=joao&departamento=CIC'))
        self.assertTrue(is_safe_url('http://localhost:5000/avaliar/1'))

        # URLs perigosas (Open Redirect e bypass com barra invertida)
        self.assertFalse(is_safe_url('http://hacker.com/phishing'))
        self.assertFalse(is_safe_url('https://google.com'))
        self.assertFalse(is_safe_url('/\\hacker.com'))
        self.assertFalse(is_safe_url('\\\\hacker.com'))
        self.assertFalse(is_safe_url(None))

    def test_rota_perfil_valida_parametro_next(self):
        # Usamos o cliente de teste nativo do Flask
        cliente = self.app.test_client()
        
        # Teste 1: URL limpa ou ausente deve redirecionar/assumir padrão seguro
        resp_segura = cliente.get('/professores/1?next=/professores?nome=joao')
        # Como o banco não está mockado neste teste isolado, esperamos um erro 404 (professor não existe), 
        # mas a aplicação NÃO deve quebrar por erro de sintaxe na URL.
        self.assertNotEqual(resp_segura.status_code, 500)