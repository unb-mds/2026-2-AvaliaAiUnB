# app/routes/auth_routes.py
"""Rotas de autenticação: cadastro -> login -> rota protegida -> logout."""
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
)
from app.seguranca import (
    chave_usuario_ou_ip,
    limiter,
    limitar_cadastro,
    limitar_login_google,
    limitar_login_por_ip,
    limitar_recuperacao_senha,
)

auth_bp = Blueprint("auth", __name__)

CHAVE_PKCE_GOOGLE = "pkce_google"
ERRO_GOOGLE = "Não foi possível entrar com o Google. Tente novamente."


def _quer_html():
    # O formulário explicita a resposta HTML também em navegadores embutidos
    # que enviam Accept genérico ao submeter formulários.
    return request.form.get('formato') == 'html' or request.accept_mimetypes.best == 'text/html'


@auth_bp.route("/cadastro", methods=["GET", "POST"])
@limitar_cadastro
def cadastro():
    if request.method == "GET":
        return render_template("cadastro.html")

    dados, erros, status = auth_controller.cadastrar(request.form)
    if _quer_html():
        if erros:
            return render_template('cadastro.html', erros=erros, dados=dados), status
        return render_template('cadastro.html', sucesso='Usuário criado com sucesso!'), 200
    if erros:
        return jsonify({'erro': 'Revise os dados de cadastro.', 'erros': erros}), status
    return jsonify({"mensagem": "Usuário criado com sucesso!"}), 201


@auth_bp.route("/login", methods=["GET", "POST"])
@limitar_login_por_ip
def login():
    if request.method == "GET":
        return render_template("login.html")

    sessao = auth_controller.autenticar(request.form)

    # Mensagem genérica de propósito: não revelar se o usuário existe ou não.
    if sessao is None:
        if _quer_html():
            return render_template("login.html", erro="Usuário ou senha inválidos"), 401
        return jsonify({"erro": "Usuário ou senha inválidos"}), 401

    if _quer_html():
        return criar_sessao(sessao, make_response(redirect(url_for("main.index"), code=303)))
    return criar_sessao(sessao, make_response(jsonify({"mensagem": "Login realizado com sucesso"})))


@auth_bp.get("/login/google")
@limitar_login_google
def login_google():
    # GET simples (link): a CSP form-action bloquearia um POST redirecionado ao Supabase.
    # O verificador PKCE amarra o retorno a este navegador, o que impede login CSRF.
    url, verificador = auth_controller.iniciar_login_google(
        url_for("auth.retorno_google", _external=True))
    session[CHAVE_PKCE_GOOGLE] = verificador
    return redirect(url, code=302)


@auth_bp.get("/login/google/retorno")
@limitar_login_google
def retorno_google():
    verificador = session.pop(CHAVE_PKCE_GOOGLE, None)
    sessao = None
    if not request.args.get("error"):
        sessao = auth_controller.concluir_login_google(request.args.get("code"), verificador)
    if sessao is None:
        resposta = make_response(render_template("login.html", erro=ERRO_GOOGLE), 400)
    else:
        resposta = criar_sessao(sessao, make_response(redirect(url_for("main.index"), code=303)))
    resposta.headers["Cache-Control"] = "no-store"
    return resposta


@auth_bp.route("/recuperar-senha", methods=["GET", "POST"])
@limitar_recuperacao_senha
def recuperar_senha():
    if request.method == "GET":
        return render_template("recuperar_senha.html")

    email = request.form.get("email")
    if email:
        auth_controller.enviar_email_recuperacao(email)

    mensagem = "Se o e-mail estiver cadastrado, você receberá um link de recuperação em instantes."
    
    if _quer_html():
        return render_template("recuperar_senha.html", mensagem=mensagem, tipo_mensagem="mensagem-sucesso"), 200
    
    return jsonify({"mensagem": mensagem}), 200


@auth_bp.route("/redefinir-senha", methods=["GET", "POST"])
def redefinir_senha():
    if request.method == "GET":
        return render_template("redefinir_senha.html")

    sucesso, erro_msg = auth_controller.redefinir_senha(request.form)

    if not sucesso:
        if _quer_html():
            return render_template("redefinir_senha.html", erro=erro_msg), 400
        return jsonify({"erro": erro_msg}), 400

    # Se for sucesso, redireciona o usuário para o login
    if _quer_html():
        return redirect(url_for("auth.login"))
    return jsonify({"mensagem": "Senha atualizada com sucesso!"}), 200


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
    if request.accept_mimetypes.accept_html:
        return render_template(
            "perfil.html",
            usuario=usuario_logado,
            avaliacoes=avaliacoes,
            criterios=professor_controller.criterios(),
            verificacao_disponivel=verificacao_email.disponivel(),
            email_verificado=verificacao_email.email_verificado(usuario_logado),
        )
    return jsonify({
        **{k: usuario_logado[k] for k in ("id", "nome", "email", "username")},
        "avaliacoes": avaliacoes,
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
