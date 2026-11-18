"""Validações de entrada reutilizadas pelas rotas, antes da persistência."""

# Critérios gravados em avaliacoes (cada um é uma coluna com nota de 1 a 5).
CRITERIOS = {
    'didatica': 'Didática',
    'clareza': 'Clareza',
    'organizacao': 'Organização',
    'disponibilidade': 'Disponibilidade/atenção aos alunos',
    'dificuldade': 'Dificuldade',
}


COMENTARIO_MINIMO = 2
COMENTARIO_MAXIMO = 1000


def validar_comentario(texto):
    """Valida o texto de um comentário. Devolve (texto_limpo, erro); erro é None se válido.

    O texto é simples: nada de HTML ou Markdown é interpretado (a escrita na tela é
    escapada pelo template). \\r\\n vira \\n, então uma quebra de linha conta um caractere.
    """
    limpo = (texto or '').replace('\r\n', '\n').replace('\r', '\n').strip()
    if len(limpo) < COMENTARIO_MINIMO:
        return limpo, f'O comentário precisa ter pelo menos {COMENTARIO_MINIMO} caracteres.'
    if len(limpo) > COMENTARIO_MAXIMO:
        return limpo, f'O comentário pode ter no máximo {COMENTARIO_MAXIMO} caracteres.'
    return limpo, None


def validar_avaliacao(dados, criterios=CRITERIOS):
    notas, erros = {}, {}
    for criterio, titulo in criterios.items():
        valor = dados.get(criterio, '')
        if valor not in ('1', '2', '3', '4', '5'):
            erros[criterio] = f'{titulo}: selecione uma nota inteira de 1 a 5.'
        else:
            notas[criterio] = int(valor)
    return notas, erros
