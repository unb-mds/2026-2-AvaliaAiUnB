import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))

from resumo_sigaa import Resumo


class TestResumo(unittest.TestCase):
    def test_sem_falhas_sai_com_zero(self):
        r = Resumo()
        r.registrar_ok("FCTE")
        r.registrar_sem_turmas("FACE")  # aviso, não é falha
        self.assertEqual(r.codigo_saida(), 0)

    def test_ignorada_pos_nao_e_erro(self):
        r = Resumo()
        r.registrar_ignorada_pos("PROGRAMA DE PÓS-GRADUAÇÃO EM ADMINISTRAÇÃO - BRASÍLIA")
        self.assertEqual(r.codigo_saida(), 0)
        saida = io.StringIO()
        with redirect_stdout(saida):
            r.imprimir()
        self.assertIn("Unidades ignoradas (pós-graduação): 1", saida.getvalue())
        self.assertIn("EM ADMINISTRAÇÃO", saida.getvalue())

    def test_unidade_pulada_sai_com_um(self):
        r = Resumo()
        r.registrar_unidade_pulada("FCTE", "timeout")
        self.assertEqual(r.codigo_saida(), 1)

    def test_conta_linhas_puladas_por_motivo(self):
        r = Resumo()
        r.registrar_linha_pulada("stale")
        r.registrar_linha_pulada("stale")
        r.registrar_linha_pulada("erro")
        self.assertEqual(r.linhas_puladas, {"stale": 2, "erro": 1})

    def test_motivo_desconhecido(self):
        with self.assertRaises(ValueError):
            Resumo().registrar_linha_pulada("xyz")

    def test_incorporar_soma_contadores(self):
        total, parcial = Resumo(), Resumo()
        total.registrar_linha_pulada("erro")
        total.a_definir_ignorados = 1
        parcial.registrar_linha_pulada("erro")
        parcial.registrar_linha_pulada("stale")
        parcial.a_definir_ignorados = 2
        total.incorporar(parcial)
        self.assertEqual(total.linhas_puladas, {"erro": 2, "stale": 1})
        self.assertEqual(total.a_definir_ignorados, 3)

    def test_imprimir_mostra_o_essencial(self):
        r = Resumo()
        r.registrar_ok("FCTE")
        r.registrar_sem_turmas("FACE")
        r.registrar_unidade_pulada("IB", "timeout")
        r.registrar_linha_pulada("stale")
        r.a_definir_ignorados = 4
        saida = io.StringIO()
        with redirect_stdout(saida):
            r.imprimir()
        texto = saida.getvalue()
        for trecho in ("FACE", "IB: timeout", "Linhas puladas: 1", "ignorados: 4"):
            self.assertIn(trecho, texto)


if __name__ == "__main__":
    unittest.main()
