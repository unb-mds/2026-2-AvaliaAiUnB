"""Validações de entrada reutilizadas pelas rotas, antes da persistência."""

# Critérios gravados em avaliacoes (cada um é uma coluna com nota de 1 a 5).
CRITERIOS = {
    'didatica': 'Didática',
    'clareza': 'Clareza',
    'organizacao': 'Organização',
    'disponibilidade': 'Disponibilidade/atenção aos alunos',
    'dificuldade': 'Dificuldade',
}


def validar_avaliacao(dados, criterios=CRITERIOS):
    notas, erros = {}, {}
    for criterio, titulo in criterios.items():
        valor = dados.get(criterio, '')
        if valor not in ('1', '2', '3', '4', '5'):
            erros[criterio] = f'{titulo}: selecione uma nota inteira de 1 a 5.'
        else:
            notas[criterio] = int(valor)
    return notas, erros
