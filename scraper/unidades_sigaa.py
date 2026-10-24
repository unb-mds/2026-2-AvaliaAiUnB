"""Escolha das unidades a processar (sem selenium nem Supabase)."""
import re
import unicodedata

from texto_sigaa import normalizar_texto

PREFIXO_POS = re.compile(r"PROGRAMA DE POS[- ]?GRADUACAO\b")


def _sem_acentos(texto: str) -> str:
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if not unicodedata.combining(c))


def eh_unidade_de_pos(texto) -> bool:
    """True se o nome da unidade começa com 'PROGRAMA DE PÓS-GRADUAÇÃO'.

    Compara sem acentos e sem diferença de caixa. 'DECANATO DE PÓS-GRADUAÇÃO'
    não conta: a regra é de prefixo.
    """
    nome = _sem_acentos(normalizar_texto(texto)).upper()
    return PREFIXO_POS.match(nome) is not None


def escolher_unidades(disponiveis, pedidas, resumo):
    """Cruza as unidades pedidas (values) com as do formulário.

    Sem pedidas, parte de todas. Unidades de pós-graduação são ignoradas e
    registradas no resumo (não são erro). Value pedido que não existe vira
    unidade pulada.
    """
    if pedidas:
        por_value = dict(disponiveis)
        candidatas = []
        for valor in dict.fromkeys(pedidas):  # sem repetidos, mantendo a ordem
            if valor in por_value:
                candidatas.append((valor, por_value[valor]))
            else:
                resumo.registrar_unidade_pulada(valor, "não existe no formulário")
    else:
        candidatas = list(disponiveis)

    escolhidas = []
    for valor, texto in candidatas:
        if eh_unidade_de_pos(texto):
            resumo.registrar_ignorada_pos(texto)
        else:
            escolhidas.append((valor, texto))
    return escolhidas
