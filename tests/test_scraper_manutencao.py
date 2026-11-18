import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))

import manutencao_banco
from manutencao_banco import (
    agrupar_duplicados,
    formatar_valor,
    gerar_csv,
    ler_tabela,
    main,
    normalizar_chave,
)
from tests.fake_supabase import ClienteFalso


def cliente_com_duplicatas():
    cliente = ClienteFalso()
    cliente.tabelas["professores"] = [
        {"id": 1, "nome": "JOSÉ ÁVILA", "departamento": "FCTE", "criado_em": None},
        {"id": 2, "nome": "jose  avila", "departamento": "IB", "criado_em": None},
        {"id": 3, "nome": "MARIA LIMA", "departamento": "FCTE", "criado_em": None},
    ]
    cliente.tabelas["disciplinas"] = [
        {"id": 10, "codigo": "FGA0001", "nome": "CÁLCULO 1", "criado_em": None},
        {"id": 11, "codigo": "MAT0025", "nome": "CÁLCULO 1", "criado_em": None},
    ]
    return cliente


class TestHelpers(unittest.TestCase):
    def test_normalizar_chave_ignora_acento_caixa_e_espacos(self):
        self.assertEqual(normalizar_chave("  José\xa0 Ávila "), "JOSE AVILA")
        self.assertEqual(normalizar_chave(None), "")

    def test_agrupar_duplicados_so_devolve_repetidos(self):
        linhas = [{"nome": "Ana"}, {"nome": "ANA "}, {"nome": "Bia"}]
        self.assertEqual(
            agrupar_duplicados(linhas, "nome"),
            {"ANA": [{"nome": "Ana"}, {"nome": "ANA "}]},
        )

    def test_formatar_valor_como_export_do_supabase(self):
        self.assertEqual(
            formatar_valor("2026-10-24T17:55:25.696851+00:00"),
            "2026-10-24 17:55:25.696851+00",
        )
        self.assertEqual(formatar_valor(None), "")
        self.assertEqual(formatar_valor(2026), "2026")

    def test_gerar_csv_crlf_aspas_minimas_e_sem_quebra_final(self):
        csv = gerar_csv(
            [{"id": 20, "codigo": "FCE0080", "nome": "SURDEZ: CULTURA, LÍNGUA"}],
            ["id", "codigo", "nome"],
        )
        self.assertEqual(csv, 'id,codigo,nome\r\n20,FCE0080,"SURDEZ: CULTURA, LÍNGUA"')


class TestBanco(unittest.TestCase):
    def test_ler_tabela_pagina_ate_o_fim(self):
        cliente = ClienteFalso()
        cliente.tabelas["turmas"] = [{"id": i} for i in range(1, 6)]
        antigo = manutencao_banco.PAGINA
        manutencao_banco.PAGINA = 2
        try:
            self.assertEqual([t["id"] for t in ler_tabela(cliente, "turmas")], [1, 2, 3, 4, 5])
        finally:
            manutencao_banco.PAGINA = antigo

    def test_duplicatas_sai_com_1_e_lista_os_grupos(self):
        saida = io.StringIO()
        with redirect_stdout(saida):
            codigo = main(["duplicatas"], cliente=cliente_com_duplicatas())
        self.assertEqual(codigo, 1)
        self.assertIn("JOSE AVILA: #1 FCTE | #2 IB", saida.getvalue())
        # mesmo nome com códigos diferentes é só informativo
        self.assertIn("CALCULO 1: FGA0001 | MAT0025", saida.getvalue())

    def test_duplicatas_sai_com_0_sem_duplicatas(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["duplicatas"], cliente=ClienteFalso()), 0)

    def test_backup_grava_um_csv_por_tabela(self):
        with tempfile.TemporaryDirectory() as pasta, redirect_stdout(io.StringIO()):
            self.assertEqual(
                main(["backup", "--destino", pasta], cliente=cliente_com_duplicatas()), 0
            )
            arquivos = sorted(p.name for p in Path(pasta).iterdir())
            self.assertEqual(
                arquivos, ["disciplinas_rows.csv", "professores_rows.csv", "turmas_rows.csv"]
            )
            professores = (Path(pasta) / "professores_rows.csv").read_bytes().decode("utf-8")
            self.assertTrue(professores.startswith("id,nome,departamento,criado_em\r\n1,JOSÉ ÁVILA,FCTE,"))
            turmas = (Path(pasta) / "turmas_rows.csv").read_text(encoding="utf-8")
            self.assertEqual(turmas, "id,professor_id,disciplina_id,ano,periodo,criado_em")


if __name__ == "__main__":
    unittest.main()
