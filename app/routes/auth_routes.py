# app/routes/auth_routes.py
"""
Rotas de autenticação, usando UsuarioRepository/Usuario (de vocês) e o
session_controller para criação de sessão, identificação do usuário
logado, proteção de rota e logout.

Fluxo: cadastro -> login -> rota protegida -> logout.
Ajuste os nomes de templates conforme o restante do projeto AvaliaAi.
"""

from flask import Blueprint, request, jsonify, make_response, render_template
from werkzeug.security import generate_password_hash, check_password_hash

from app.models import Usuario
from app.repositorio import UsuarioRepository
from app.controllers.session_controller import (
    criar_sessao,
    encerrar_sessao,
    obter_usuario_atual,
    login_required,
)

auth_bp = Blueprint("auth", __name__)
usuario_repo = UsuarioRepository()


@auth_bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "GET":
        return render_template("cadastro.html")

    nome = request.form["nome"]
    email = request.form["email"]
    senha = request.form["senha"]

    # A coluna do banco se chama "senha", mas o valor salvo e sempre o
    # HASH da senha, nunca a senha em texto puro.
    novo_usuario = Usuario(nome=nome, email=email, senha=generate_password_hash(senha))

    sucesso, mensagem = usuario_repo.criar_usuario(novo_usuario)
    if not sucesso:
        return jsonify({"erro": mensagem}), 409

    return jsonify({"mensagem": mensagem}), 201


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form["email"]
    senha = request.form["senha"]

    usuario = usuario_repo.buscar_usuario_por_email(email)

    # Mensagem genérica de propósito: não revelar se o e-mail existe ou não.
    if usuario is None or not check_password_hash(usuario.senha, senha):
        return jsonify({"erro": "E-mail ou senha inválidos"}), 401

    response = make_response(jsonify({"mensagem": "Login realizado com sucesso"}))
    return criar_sessao(usuario.id, response)  # 1. criação da sessão


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    response = make_response(jsonify({"mensagem": "Sessão encerrada"}))
    return encerrar_sessao(response)  # 4. logout


@auth_bp.route("/perfil")
@login_required  # 3. proteção da rota
def perfil():
    usuario_logado = obter_usuario_atual()  # 2. identificação do usuário autenticado
 
    if request.accept_mimetypes.accept_html:
        return render_template("perfil.html", usuario=usuario_logado)
 
    return jsonify(
        {"id": usuario_logado["id"], "nome": usuario_logado["nome"], "email": usuario_logado["email"]}
    )