import unicodedata


def normalizar_busca(texto):
    """Padroniza texto para buscas sem distinção de acentos, caixa ou espaços."""
    texto = unicodedata.normalize('NFKD', str(texto or ''))
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    return ''.join(texto.casefold().split())
