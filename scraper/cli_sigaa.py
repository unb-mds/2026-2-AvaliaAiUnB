"""Argumentos de linha de comando do scraper (sem selenium nem Supabase)."""
import argparse

from texto_sigaa import validar_ano, validar_periodo


def _como_argumento(validador):
    """Adapta um validador que levanta ValueError para o argparse."""

    def convertido(texto):
        try:
            return validador(texto)
        except ValueError as e:
            raise argparse.ArgumentTypeError(str(e))

    return convertido


def montar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scraper de turmas do SIGAA.")
    parser.add_argument(
        "--ano",
        type=_como_argumento(validar_ano),
        default="2026",
        help="ano das turmas (padrão: 2026)",
    )
    parser.add_argument(
        "--periodo",
        type=_como_argumento(validar_periodo),
        default="2",
        help="período das turmas, de 1 a 4 (padrão: 2)",
    )
    parser.add_argument(
        "--unidade",
        action="append",
        default=None,
        metavar="VALUE",
        help="value do <option> da unidade (ex.: 673); pode ser repetido. "
        "Sem esta opção, percorre todas as unidades de graduação",
    )
    parser.add_argument(
        "--pausa",
        type=float,
        default=1.0,
        help="segundos de pausa entre unidades (padrão: 1)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="roda o Chrome sem janela",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="imprime o que seria gravado, sem tocar no banco",
    )
    return parser
