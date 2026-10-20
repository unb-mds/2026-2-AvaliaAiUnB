"""Helpers puros de texto do scraper do SIGAA (sem selenium nem Supabase)."""
import re

A_DEFINIR = "A DEFINIR DOCENTE"


def normalizar_texto(texto) -> str:
    """Troca \\xa0 por espaço, colapsa espaços/quebras e remove as pontas."""
    if not texto:
        return ""
    return re.sub(r"\s+", " ", str(texto).replace("\xa0", " ")).strip()


def eh_a_definir(nome: str) -> bool:
    return normalizar_texto(nome).upper() == A_DEFINIR


def extrair_docentes(texto) -> list[str]:
    """Separa os docentes de uma célula, sem o sufixo '(NNh)'.

    'A DEFINIR DOCENTE' não é docente e fica de fora.
    """
    docentes = []
    for parte in re.split(r"[\r\n,;]+", str(texto or "").replace("\xa0", " ")):
        nome = normalizar_texto(re.sub(r"\(\s*\d+\s*h\s*\)", "", parte))
        if not nome or eh_a_definir(nome) or nome in docentes:
            continue
        docentes.append(nome)
    return docentes
