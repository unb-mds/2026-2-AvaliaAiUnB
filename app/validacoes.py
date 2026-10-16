"""Validações de entrada reutilizadas pelas rotas, antes da persistência."""
import re

MINIMO_SENHA = 8
DOMINIO_EMAIL = 'gmail.com'
PADRAO_USERNAME = re.compile(r'[a-z0-9._]{3,30}')

# Critérios gravados em avaliacoes (cada um é uma coluna com nota de 1 a 5).
CRITERIOS = {
    'didatica': 'Didática',
    'clareza': 'Clareza',
    'organizacao': 'Organização',
    'disponibilidade': 'Disponibilidade/atenção aos alunos',
    'dificuldade': 'Dificuldade',
}


def validar_cadastro(dados):
    nome = dados.get('nome', '').strip()
    username = dados.get('username', '').strip().lower()
    email = dados.get('email', '').strip().lower()
    senha = dados.get('senha', '')
    erros = {}
    if not nome:
        erros['nome'] = 'Informe seu nome.'
    if not PADRAO_USERNAME.fullmatch(username):
        erros['username'] = ('O nome de usuário deve ter de 3 a 30 caracteres: '
                             'letras, números, ponto ou sublinhado.')
    partes = email.rsplit('@', 1)
    local = partes[0]
    dominio = partes[1] if len(partes) == 2 else ''
    if (len(email) > 254 or len(local) > 64
            or not re.fullmatch(r"[a-z0-9!#$%&'*+/=?^_`{|}~.-]+", local)
            or local.startswith('.') or local.endswith('.') or '..' in local
            or '.' not in dominio
            or any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', p)
                   for p in dominio.split('.'))):
        erros['email'] = 'Informe um e-mail válido.'
    elif dominio != DOMINIO_EMAIL:
        erros['email'] = f'Use um e-mail @{DOMINIO_EMAIL}.'
    if not senha.strip() or len(senha) < MINIMO_SENHA:
        erros['senha'] = f'A senha deve ter pelo menos {MINIMO_SENHA} caracteres.'
    if dados.get('confirmar_senha', '') != senha or not senha:
        erros['confirmar_senha'] = 'A confirmação deve ser igual à senha.'
    return {'nome': nome, 'username': username, 'email': email, 'senha': senha}, erros


def validar_avaliacao(dados, criterios=CRITERIOS):
    notas, erros = {}, {}
    for criterio, titulo in criterios.items():
        valor = dados.get(criterio, '')
        if valor not in ('1', '2', '3', '4', '5'):
            erros[criterio] = f'{titulo}: selecione uma nota inteira de 1 a 5.'
        else:
            notas[criterio] = int(valor)
    return notas, erros
