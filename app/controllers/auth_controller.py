"""Cadastro e login: validação, delegação ao Supabase Auth e mapeamento de erros para as rotas."""
from app.repositorio import repositorios
from app.validacoes import validar_cadastro


def cadastrar(formulario):
    """Retorna (dados, erros, status). status 201 em sucesso, 400 validação, 409 conflito."""
    dados, erros = validar_cadastro(formulario)
    if erros:
        return dados, erros, 400
    resultado = repositorios().usuarios.criar(
        dados['nome'], dados['username'], dados['email'], dados['senha'])
    if not resultado[0]:
        _, campo, mensagem = resultado
        return dados, {campo: mensagem}, 409
    return dados, {}, 201


def autenticar(formulario):
    """Sessão ({'access_token', 'refresh_token'}) se o par usuário/senha for válido, senão None."""
    return repositorios().usuarios.autenticar(
        formulario.get('username', ''), formulario.get('senha', ''))
