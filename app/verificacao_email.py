import os
import smtplib
import ssl
from email.message import EmailMessage
from hashlib import sha256
from urllib.parse import urlsplit

from flask import current_app, url_for
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.repositorio import repositorios

VALIDADE_LINK = 30 * 60


def _origem():
    return os.environ.get('VERIFICACAO_EMAIL_ORIGEM', '').rstrip('/')


def disponivel():
    origem = urlsplit(_origem())
    return (
        origem.scheme == 'https' and bool(origem.hostname)
        and not (origem.username or origem.password or origem.path or origem.query or origem.fragment)
        and all(os.environ.get(nome) for nome in (
            'VERIFICACAO_EMAIL_SMTP_HOST', 'VERIFICACAO_EMAIL_SMTP_USUARIO',
            'VERIFICACAO_EMAIL_SMTP_SENHA', 'VERIFICACAO_EMAIL_REMETENTE',
        ))
    )


def _identidade(usuario):
    return sha256(f"{usuario['id']}\0{usuario['email']}".encode()).hexdigest()


def _assinador():
    return URLSafeTimedSerializer(current_app.secret_key, salt='verificacao-email-comentarios')


def email_verificado(usuario):
    return bool(usuario and usuario.get('email') and disponivel()
                and repositorios().usuarios.email_verificado(usuario['id'], _identidade(usuario)))


def link_valido(usuario, token):
    try:
        identidade = _assinador().loads(token, max_age=VALIDADE_LINK)
    except BadSignature:
        return False
    return bool(usuario.get('email')) and identidade == _identidade(usuario)


def confirmar(usuario, token):
    if not link_valido(usuario, token):
        return False
    repositorios().usuarios.gravar_email_verificado(usuario['id'], _identidade(usuario))
    return True


def enviar_link(usuario):
    token = _assinador().dumps(_identidade(usuario))
    caminho = url_for('auth.verificar_email', chave=token)
    mensagem = EmailMessage()
    mensagem['From'] = os.environ['VERIFICACAO_EMAIL_REMETENTE']
    mensagem['To'] = usuario['email']
    mensagem['Subject'] = 'Verifique seu e-mail no AvaliaUnB'
    mensagem.set_content(
        'Abra o link enquanto estiver conectado à mesma conta. '
        'O link expira em 30 minutos.\n\n'
        f'{_origem()}{caminho}\n\n'
        'Se você não solicitou este e-mail, pode ignorar a mensagem.'
    )
    with smtplib.SMTP_SSL(os.environ['VERIFICACAO_EMAIL_SMTP_HOST'], 465,
                          timeout=5, context=ssl.create_default_context()) as smtp:
        smtp.login(os.environ['VERIFICACAO_EMAIL_SMTP_USUARIO'],
                   os.environ['VERIFICACAO_EMAIL_SMTP_SENHA'])
        smtp.send_message(mensagem)
