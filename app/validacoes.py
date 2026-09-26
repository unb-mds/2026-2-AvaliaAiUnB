"""Validações de entrada reutilizadas pelas rotas, antes da persistência."""
import re

MINIMO_SENHA = 8
CRITERIOS = {
    'didatica': 'Didática',
    'organizacao': 'Organização',
    'dificuldade': 'Dificuldade',
    'disponibilidade': 'Disponibilidade/atenção aos alunos',
    'avaliacao_geral': 'Avaliação geral',
}


def validar_cadastro(dados):
    nome = dados.get('nome', '').strip()
    email = dados.get('email', '').strip()
    senha = dados.get('senha', '')
    erros = {}
    if not nome:
        erros['nome'] = 'Informe seu nome.'
    # Endereços usuais, inclusive +tag e domínios externos à UnB.
    partes = email.rsplit('@', 1)
    local = partes[0]
    dominio = partes[1] if len(partes) == 2 else ''
    if (len(email) > 254 or len(local) > 64
            or not re.fullmatch(r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~.-]+", local)
            or local.startswith('.') or local.endswith('.') or '..' in local
            or '.' not in dominio
            or any(not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?', p)
                   for p in dominio.split('.'))):
        erros['email'] = 'Informe um e-mail válido.'
    if not senha.strip() or len(senha) < MINIMO_SENHA:
        erros['senha'] = f'A senha deve ter pelo menos {MINIMO_SENHA} caracteres.'
    if dados.get('confirmar_senha', '') != senha or not senha:
        erros['confirmar_senha'] = 'A confirmação deve ser igual à senha.'
    return {'nome': nome, 'email': email, 'senha': senha}, erros


def validar_avaliacao(dados):
    notas, erros = {}, {}
    for criterio, titulo in CRITERIOS.items():
        valor = dados.get(criterio, '')
        if valor not in ('1', '2', '3', '4', '5'):
            erros[criterio] = f'{titulo}: selecione uma nota inteira de 1 a 5.'
        else:
            notas[criterio] = int(valor)
    return notas, erros
