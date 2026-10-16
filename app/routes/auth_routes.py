# app/routes/auth_routes.py
"""Rotas de autenticação: cadastro -> login -> rota protegida -> logout."""
from flask import Blueprint, jsonify, make_response, redirect, render_template, request, url_for

from app.controllers import auth_controller
from app.controllers.session_controller import (
    criar_sessao,
    encerrar_sessao,
    login_required,
    obter_usuario_atual,
)

auth_bp = Blueprint("auth", __name__)


def _quer_html():
    # O formulário explicita a resposta HTML também em navegadores embutidos
    # que enviam Accept genérico ao submeter formulários.
    return request.form.get('formato') == 'html' or request.accept_mimetypes.best == 'text/html'


@auth_bp.route("/cadastro", methods=["GET", "POST"])
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
    if request.accept_mimetypes.accept_html:
        return render_template("perfil.html", usuario=usuario_logado)
    return jsonify({k: usuario_logado[k] for k in ("id", "nome", "email", "username")})
