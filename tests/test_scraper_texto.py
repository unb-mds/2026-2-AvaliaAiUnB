import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))

from texto_sigaa import eh_a_definir, extrair_docentes, normalizar_texto


class TestNormalizarTexto(unittest.TestCase):
    def test_vazio_e_none(self):
        self.assertEqual(normalizar_texto(None), "")
        self.assertEqual(normalizar_texto("   "), "")

    def test_nbsp_e_espacos(self):
        self.assertEqual(normalizar_texto("  FCTE\xa0 -  Gama \n"), "FCTE - Gama")


class TestExtrairDocentes(unittest.TestCase):
    def test_remove_sufixo_carga_horaria(self):
        self.assertEqual(extrair_docentes("MARIA SILVA (60h)"), ["MARIA SILVA"])

    def test_varios_por_quebra_de_linha(self):
        texto = "MARIA SILVA (30h)\nJOAO SOUZA (30h)"
        self.assertEqual(extrair_docentes(texto), ["MARIA SILVA", "JOAO SOUZA"])

    def test_varios_por_virgula_e_ponto_e_virgula(self):
        texto = "MARIA SILVA (30h), JOAO SOUZA (15h); ANA LIMA (15h)"
        self.assertEqual(
            extrair_docentes(texto), ["MARIA SILVA", "JOAO SOUZA", "ANA LIMA"]
        )

    def test_nbsp_e_espacos_duplicados(self):
        self.assertEqual(extrair_docentes("MARIA\xa0  SILVA\xa0(60h)"), ["MARIA SILVA"])

    def test_a_definir_docente(self):
        self.assertEqual(extrair_docentes("A DEFINIR DOCENTE (60h)"), [])
        self.assertEqual(extrair_docentes("a definir docente"), [])

    def test_celula_mista(self):
        texto = "A DEFINIR DOCENTE (30h)\nMARIA SILVA (30h)"
        self.assertEqual(extrair_docentes(texto), ["MARIA SILVA"])

    def test_vazio_e_none(self):
        self.assertEqual(extrair_docentes(""), [])
        self.assertEqual(extrair_docentes(None), [])

    def test_duplicados_na_celula(self):
        self.assertEqual(
            extrair_docentes("MARIA SILVA (30h)\nMARIA SILVA (30h)"), ["MARIA SILVA"]
        )


class TestEhADefinir(unittest.TestCase):
    def test_variacoes(self):
        self.assertTrue(eh_a_definir(" a definir  docente "))
        self.assertFalse(eh_a_definir("MARIA SILVA"))


if __name__ == "__main__":
    unittest.main()
