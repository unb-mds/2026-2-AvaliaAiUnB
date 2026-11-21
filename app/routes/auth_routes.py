# app/routes/auth_routes.py
"""Rotas de autenticação: login com Google (cria a conta no 1º acesso) -> rota protegida -> logout."""
from smtplib import SMTPException

from flask import (Blueprint, abort, jsonify, make_response, redirect, render_template, request,
                   session, url_for)

from app import verificacao_email
from app.controllers import auth_controller, professor_controller
from app.controllers.session_controller import (
    criar_sessao,
    encerrar_sessao,
    login_required,
    obter_usuario_atual,
    sanitizar_destino,
)
from app.seguranca import (
    chave_usuario_ou_ip,
    limiter,
    limitar_login_google,
)

auth_bp = Blueprint("auth", __name__)

CHAVE_PKCE_GOOGLE = "pkce_google"
CHAVE_DESTINO_LOGIN = "destino_pos_login"
ERRO_GOOGLE = "Não foi possível entrar com o Google. Tente novamente."


def _quer_html():
    # O formulário explicita a resposta HTML também em navegadores embutidos
    # que enviam Accept genérico ao submeter formulários.
    return request.form.get('formato') == 'html' or request.accept_mimetypes.best == 'text/html'


@auth_bp.get("/login")
def login():
    destino = sanitizar_destino(request.args.get("next"))
    if destino:
        session[CHAVE_DESTINO_LOGIN] = destino
    else:
        session.pop(CHAVE_DESTINO_LOGIN, None)
    return render_template("login.html", next_url=destino)


@auth_bp.get("/cadastro")
def cadastro():
    # O cadastro acontece no primeiro login com Google; mantém links antigos funcionando.
    destino = sanitizar_destino(request.args.get("next"))
    if destino:
        return redirect(url_for("auth.login", next=destino))
    return redirect(url_for("auth.login"))


@auth_bp.get("/login/google")
@limitar_login_google
def login_google():
    # GET simples (link): a CSP form-action bloquearia um POST redirecionado ao Supabase.
    # O verificador PKCE amarra o retorno a este navegador, o que impede login CSRF.
    destino = sanitizar_destino(request.args.get("next")) or sanitizar_destino(session.get(CHAVE_DESTINO_LOGIN))
    if destino:
        session[CHAVE_DESTINO_LOGIN] = destino
    else:
        session.pop(CHAVE_DESTINO_LOGIN, None)

    url, verificador = auth_controller.iniciar_login_google(
        url_for("auth.retorno_google", _external=True))
    session[CHAVE_PKCE_GOOGLE] = verificador
    return redirect(url, code=302)


@auth_bp.get("/login/google/retorno")
@limitar_login_google
def retorno_google():
    verificador = session.pop(CHAVE_PKCE_GOOGLE, None)
    destino = sanitizar_destino(session.pop(CHAVE_DESTINO_LOGIN, None))
    sessao = None
    if not request.args.get("error"):
        sessao = auth_controller.concluir_login_google(request.args.get("code"), verificador)
    if sessao is None:
        if destino:
            session[CHAVE_DESTINO_LOGIN] = destino
        resposta = make_response(render_template("login.html", erro=ERRO_GOOGLE, next_url=destino), 400)
    else:
        destino_final = destino or url_for("main.index")
        resposta = criar_sessao(sessao, make_response(redirect(destino_final, code=303)))
    resposta.headers["Cache-Control"] = "no-store"
    return resposta


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    if _quer_html():
        return encerrar_sessao(make_response(redirect(url_for("main.index"), code=303)))
    return encerrar_sessao(make_response(jsonify({"mensagem": "Sessão encerrada"})))


@auth_bp.route("/perfil")
@login_required
def perfil():
    usuario_logado = obter_usuario_atual()
    avaliacoes = professor_controller.listar_avaliacoes_usuario(usuario_logado)
    favoritos = professor_controller.listar_favoritos_usuario(usuario_logado)
    if request.accept_mimetypes.accept_html:
        return render_template(
            "perfil.html",
            usuario=usuario_logado,
            avaliacoes=avaliacoes,
            favoritos=favoritos,
            criterios=professor_controller.criterios(),
            verificacao_disponivel=verificacao_email.disponivel(),
            email_verificado=verificacao_email.email_verificado(usuario_logado),
        )
    return jsonify({
        **{k: usuario_logado[k] for k in ("id", "nome", "email", "username")},
        "avaliacoes": avaliacoes,
        "favoritos": favoritos,
    })


@auth_bp.post("/perfil/enviar-verificacao")
@login_required
@limiter.limit("4 per hour", key_func=chave_usuario_ou_ip)
@limiter.limit("20 per hour")
def enviar_verificacao():
    if not verificacao_email.disponivel():
        abort(503)
    usuario = obter_usuario_atual()
    if verificacao_email.email_verificado(usuario):
        return redirect(url_for('auth.verificar_email'), code=303)
    if not usuario.get('email'):
        abort(400)
    try:
        verificacao_email.enviar_link(usuario)
    except (OSError, SMTPException):
        return _pagina_verificacao(usuario, erro='Não foi possível enviar o link. Tente de novo.', status=503)
    return redirect(url_for('auth.verificar_email', enviado=1), code=303)


def _pagina_verificacao(usuario, status=200, **contexto):
    resposta = make_response(render_template('verificar_email.html', usuario=usuario, **contexto), status)
    resposta.headers['Cache-Control'] = 'no-store'
    resposta.headers['Referrer-Policy'] = 'origin'
    return resposta


@auth_bp.route("/perfil/verificar-email", methods=["GET", "POST"])
@login_required
@limiter.limit("12 per hour", methods=['POST'], key_func=chave_usuario_ou_ip)
def verificar_email():
    if not verificacao_email.disponivel():
        abort(503)
    usuario = obter_usuario_atual()
    if request.method == 'POST':
        if verificacao_email.confirmar(usuario, request.form.get('chave', '')):
            return redirect(url_for('auth.verificar_email'), code=303)
        return _pagina_verificacao(usuario, erro='Link inválido ou expirado. Peça um novo link.', status=400)

    chave = request.args.get('chave', '')
    if chave and not verificacao_email.link_valido(usuario, chave):
        return _pagina_verificacao(usuario, erro='Link inválido ou expirado. Peça um novo link.', status=400)
    return _pagina_verificacao(usuario, chave=chave, enviado=request.args.get('enviado') == '1',
                               verificado=verificacao_email.email_verificado(usuario))