"""Manutenção dos dados do catálogo no Supabase (issue #235).

Subcomandos (rodar da raiz do repositório):

    python scraper/manutencao_banco.py duplicatas
        Relatório somente leitura de professores e disciplinas duplicados.
        Sai com código 1 se encontrar duplicatas.

    python scraper/manutencao_banco.py backup [--destino docs/backup]
        Exporta professores, disciplinas e turmas para CSV no mesmo formato
        do "Export to CSV" do Supabase (<tabela>_rows.csv).

Só as tabelas públicas do catálogo entram no backup: avaliações, comentários
e perfis têm dados de usuários (LGPD) e não vão para o repositório.
"""
import argparse
import csv
import io
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

PAGINA = 1000  # limite padrão de linhas por resposta do PostgREST

COLUNAS_BACKUP = {
    "professores": ["id", "nome", "departamento", "criado_em"],
    "disciplinas": ["id", "codigo", "nome", "criado_em"],
    "turmas": ["id", "professor_id", "disciplina_id", "ano", "periodo", "criado_em"],
}


def _supabase():
    """Import tardio: os helpers puros podem ser testados sem .env."""
    from supabase_client import supabase

    return supabase


# ---------- helpers puros ----------

def normalizar_chave(texto) -> str:
    """Chave de comparação: sem acentos, caixa alta e espaços colapsados."""
    sem_acento = unicodedata.normalize("NFKD", str(texto or ""))
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acento.replace("\xa0", " ")).strip().upper()


def agrupar_duplicados(linhas: list, campo: str) -> dict:
    """{chave normalizada: [linhas]} só com as chaves que aparecem mais de uma vez."""
    grupos = defaultdict(list)
    for linha in linhas:
        grupos[normalizar_chave(linha.get(campo))].append(linha)
    return {chave: grupo for chave, grupo in sorted(grupos.items()) if len(grupo) > 1}


def formatar_valor(valor) -> str:
    """Formata como o export CSV do Supabase (timestamps no formato do Postgres)."""
    if valor is None:
        return ""
    texto = str(valor)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T[\d:.]+[+-]\d{2}:\d{2}", texto):
        texto = texto.replace("T", " ", 1)
        if texto.endswith(":00"):
            texto = texto[:-3]  # +00:00 -> +00
    return texto


def gerar_csv(linhas: list, colunas: list) -> str:
    """CSV com CRLF, aspas só quando preciso e sem quebra de linha no fim."""
    saida = io.StringIO()
    escritor = csv.writer(saida, lineterminator="\r\n")
    escritor.writerow(colunas)
    for linha in linhas:
        escritor.writerow([formatar_valor(linha.get(c)) for c in colunas])
    return saida.getvalue().removesuffix("\r\n")


# ---------- acesso ao banco ----------

def ler_tabela(cliente, tabela: str, colunas: str = "*") -> list:
    """Lê a tabela inteira, ordenada por id, paginando de PAGINA em PAGINA."""
    linhas, inicio = [], 0
    while True:
        pagina = (
            cliente.table(tabela).select(colunas).order("id")
            .range(inicio, inicio + PAGINA - 1).execute()
        ).data
        linhas.extend(pagina)
        if len(pagina) < PAGINA:
            return linhas
        inicio += PAGINA


def _imprimir_grupos(titulo: str, grupos: dict, formatar) -> None:
    print(f"\n--- {titulo}: {len(grupos)} grupo(s) ---")
    for chave, grupo in grupos.items():
        print(f"{chave}: " + " | ".join(formatar(l) for l in grupo))


def relatorio_duplicatas(cliente) -> int:
    """Imprime o relatório e devolve quantos grupos duplicados existem."""
    professores = ler_tabela(cliente, "professores", "id,nome,departamento")
    disciplinas = ler_tabela(cliente, "disciplinas", "id,codigo,nome")

    prof_dup = agrupar_duplicados(professores, "nome")
    disc_dup = agrupar_duplicados(disciplinas, "codigo")
    disc_mesmo_nome = agrupar_duplicados(disciplinas, "nome")

    print(f"Professores: {len(professores)} | Disciplinas: {len(disciplinas)}")
    _imprimir_grupos("PROFESSORES COM O MESMO NOME", prof_dup,
                     lambda p: f"#{p['id']} {p.get('departamento') or '(sem unidade)'}")
    _imprimir_grupos("DISCIPLINAS COM O MESMO CÓDIGO", disc_dup,
                     lambda d: f"#{d['id']} {d['nome']}")
    _imprimir_grupos("(informativo) DISCIPLINAS COM O MESMO NOME E CÓDIGOS DIFERENTES",
                     disc_mesmo_nome, lambda d: d["codigo"])
    return len(prof_dup) + len(disc_dup)


def gerar_backup(cliente, destino: Path) -> dict:
    """Grava <tabela>_rows.csv em `destino` e devolve {tabela: linhas}."""
    destino.mkdir(parents=True, exist_ok=True)
    totais = {}
    for tabela, colunas in COLUNAS_BACKUP.items():
        linhas = ler_tabela(cliente, tabela, ",".join(colunas))
        arquivo = destino / f"{tabela}_rows.csv"
        arquivo.write_text(gerar_csv(linhas, colunas), encoding="utf-8", newline="")
        totais[tabela] = len(linhas)
        print(f"[*] {arquivo}: {len(linhas)} linhas")
    return totais


def montar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="comando", required=True)
    sub.add_parser("duplicatas", help="relatório de professores/disciplinas duplicados")
    backup = sub.add_parser("backup", help="exporta o catálogo para CSV")
    backup.add_argument("--destino", type=Path, default=Path("docs/backup"),
                        help="pasta dos CSVs (padrão: docs/backup)")
    return parser


def main(argv=None, cliente=None) -> int:
    args = montar_parser().parse_args(argv)
    cliente = cliente or _supabase()
    if args.comando == "duplicatas":
        return 1 if relatorio_duplicatas(cliente) else 0
    gerar_backup(cliente, args.destino)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
