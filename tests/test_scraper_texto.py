import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))

from texto_sigaa import (
    UnidadeInvalidaError,
    eh_a_definir,
    extrair_docentes,
    normalizar_texto,
    validar_unidade,
)


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


class TestValidarUnidade(unittest.TestCase):
    def test_devolve_texto_completo_normalizado(self):
        self.assertEqual(
            validar_unidade("  FCTE - FACULDADE  DO GAMA "),
            "FCTE - FACULDADE DO GAMA",
        )

    def test_vazio_ou_none(self):
        for texto in ("", "   ", " ", None):
            with self.assertRaises(UnidadeInvalidaError):
                validar_unidade(texto)

    def test_placeholder_do_select(self):
        with self.assertRaises(UnidadeInvalidaError):
            validar_unidade("-- SELECIONE UM DEPARTAMENTO --")

    def test_erro_e_value_error(self):
        self.assertTrue(issubclass(UnidadeInvalidaError, ValueError))


class TestEhADefinir(unittest.TestCase):
    def test_variacoes(self):
        self.assertTrue(eh_a_definir(" a definir  docente "))
        self.assertFalse(eh_a_definir("MARIA SILVA"))


if __name__ == "__main__":
    unittest.main()
