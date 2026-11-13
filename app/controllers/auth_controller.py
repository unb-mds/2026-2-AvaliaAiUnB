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


def enviar_email_recuperacao(email):
    """Delega ao repositório a requisição para envio do e-mail de recuperação de senha."""
    if not email:
        return False
    return repositorios().usuarios.enviar_email_recuperacao(email)


def redefinir_senha(formulario):
    """Valida as regras de negócio e delega a atualização da nova senha ao repositório."""
    senha = formulario.get('senha', '')
    confirmar_senha = formulario.get('confirmar_senha', '')
    access_token = formulario.get('access_token', '')

    if not access_token:
        return False, "Link de recuperação inválido ou expirado. Solicite um novo e-mail."
    
    if not senha or len(senha) < 6:
        return False, "A nova senha deve ter no mínimo 6 caracteres."
    
    if senha != confirmar_senha:
        return False, "As senhas não coincidem."
        
    return repositorios().usuarios.atualizar_senha(access_token, senha)