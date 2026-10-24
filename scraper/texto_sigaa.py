"""Helpers puros de texto do scraper do SIGAA (sem selenium nem Supabase)."""
import re

A_DEFINIR = "A DEFINIR DOCENTE"


def normalizar_texto(texto) -> str:
    """Troca \\xa0 por espaço, colapsa espaços/quebras e remove as pontas."""
    if not texto:
        return ""
    return re.sub(r"\s+", " ", str(texto).replace("\xa0", " ")).strip()


class UnidadeInvalidaError(ValueError):
    """Unidade não selecionada ou com texto inválido no formulário."""


def validar_unidade(texto) -> str:
    """Devolve o texto completo da unidade normalizado ou levanta erro.

    Rejeita texto vazio e a opção-placeholder do select (ex.: '-- SELECIONE --').
    """
    unidade = normalizar_texto(texto)
    if not unidade or "SELECIONE" in unidade.upper():
        raise UnidadeInvalidaError(
            f"Unidade inválida ou não selecionada (texto lido: {unidade!r})."
        )
    return unidade


def eh_a_definir(nome: str) -> bool:
    return normalizar_texto(nome).upper() == A_DEFINIR


def _nomes_da_celula(texto) -> list[str]:
    """Todos os nomes da célula (inclusive 'A DEFINIR DOCENTE'), sem '(NNh)'.

    Delimitadores: quebra de linha, ',', ';' e o próprio sufixo '(NNh)'
    (docentes podem vir separados só por espaço depois dele). O último nome
    pode vir sem sufixo.
    """
    nomes = []
    for parte in re.split(r"[\r\n,;]+", str(texto or "").replace("\xa0", " ")):
        for pedaco in re.split(r"\(\s*\d+\s*h\s*\)", parte):
            nome = normalizar_texto(pedaco)
            if nome:
                nomes.append(nome)
    return nomes


def extrair_docentes(texto) -> list[str]:
    """Separa os docentes de uma célula, sem o sufixo '(NNh)'.

    'A DEFINIR DOCENTE', vazios e repetidos ficam de fora.
    """
    docentes = []
    for nome in _nomes_da_celula(texto):
        if not eh_a_definir(nome) and nome not in docentes:
            docentes.append(nome)
    return docentes


def contar_a_definir(texto) -> int:
    """Quantas vezes 'A DEFINIR DOCENTE' aparece na célula."""
    return sum(1 for nome in _nomes_da_celula(texto) if eh_a_definir(nome))
