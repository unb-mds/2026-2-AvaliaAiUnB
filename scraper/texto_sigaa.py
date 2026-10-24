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


def validar_ano(texto) -> str:
    """Ano com 4 dígitos (ex.: '2026'); levanta ValueError caso contrário."""
    ano = normalizar_texto(texto)
    if not re.fullmatch(r"\d{4}", ano):
        raise ValueError(f"Ano inválido: {ano!r} (esperado 4 dígitos, ex.: 2026).")
    return ano


def validar_periodo(texto) -> str:
    """Período de 1 a 4 (valores do select do SIGAA); levanta ValueError caso contrário."""
    periodo = normalizar_texto(texto)
    if periodo not in ("1", "2", "3", "4"):
        raise ValueError(f"Período inválido: {periodo!r} (esperado 1, 2, 3 ou 4).")
    return periodo


def professores_em_varias_unidades(professores) -> dict[str, list[str]]:
    """Docentes que aparecem em mais de uma unidade.

    Recebe dicts com 'nome' e 'departamento'. Os nomes são comparados sem
    diferença de caixa ou espaços; a chave do resultado é o nome normalizado
    em maiúsculas e o valor, as unidades em ordem alfabética.
    """
    unidades_por_nome = {}
    for p in professores:
        nome = normalizar_texto(p["nome"]).upper()
        unidades_por_nome.setdefault(nome, set()).add(p["departamento"])
    return {
        nome: sorted(unidades)
        for nome, unidades in sorted(unidades_por_nome.items())
        if len(unidades) > 1
    }


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
