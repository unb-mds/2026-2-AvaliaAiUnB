import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))

from texto_sigaa import (
    UnidadeInvalidaError,
    contar_a_definir,
    eh_a_definir,
    extrair_docentes,
    normalizar_texto,
    professores_em_varias_unidades,
    validar_ano,
    validar_periodo,
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


class TestDocentesSeparadosPorSufixo(unittest.TestCase):
    def test_casos_reais(self):
        casos = {
            "LUIZ EDUARDO DE LACERDA ABREU (60h) EDNEIDE ELISBÃO (60h)":
                ["LUIZ EDUARDO DE LACERDA ABREU", "EDNEIDE ELISBÃO"],
            "MANOEL PEREIRA DE ANDRADE (20h) JOÃO LUIZ HOMEM DE CARVALHO (20h)":
                ["MANOEL PEREIRA DE ANDRADE", "JOÃO LUIZ HOMEM DE CARVALHO"],
            "JOÃO LUIZ HOMEM DE CARVALHO (60h)": ["JOÃO LUIZ HOMEM DE CARVALHO"],
            "ANA SOUZA (60h), JOAO LIMA (30h)": ["ANA SOUZA", "JOAO LIMA"],
            "A DEFINIR DOCENTE (60h)": [],
        }
        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                self.assertEqual(extrair_docentes(texto), esperado)

    def test_ultimo_nome_sem_sufixo_e_mantido(self):
        self.assertEqual(
            extrair_docentes("LUIZ ABREU (60h) EDNEIDE ELISBÃO"),
            ["LUIZ ABREU", "EDNEIDE ELISBÃO"],
        )

    def test_a_definir_junto_de_docente_sem_separador(self):
        self.assertEqual(
            extrair_docentes("A DEFINIR DOCENTE (30h) ANA SOUZA (30h)"),
            ["ANA SOUZA"],
        )

    def test_repetidos(self):
        self.assertEqual(extrair_docentes("ANA SOUZA (30h) ANA SOUZA (30h)"), ["ANA SOUZA"])


class TestContarADefinir(unittest.TestCase):
    def test_contagem(self):
        self.assertEqual(contar_a_definir("A DEFINIR DOCENTE (60h)"), 1)
        self.assertEqual(contar_a_definir("ANA SOUZA (60h)"), 0)
        self.assertEqual(contar_a_definir(None), 0)


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


class TestValidarAnoPeriodo(unittest.TestCase):
    def test_validos(self):
        self.assertEqual(validar_ano(" 2026 "), "2026")
        self.assertEqual(validar_periodo("2"), "2")

    def test_invalidos(self):
        for ano in ("", "26", "20266", "abcd", None):
            with self.assertRaises(ValueError):
                validar_ano(ano)
        for periodo in ("", "0", "5", "x"):
            with self.assertRaises(ValueError):
                validar_periodo(periodo)


class TestProfessoresEmVariasUnidades(unittest.TestCase):
    def test_lista_so_quem_esta_em_mais_de_uma(self):
        professores = [
            {"nome": "ANA", "departamento": "FGA"},
            {"nome": "ana ", "departamento": "FCTE"},
            {"nome": "BRUNO", "departamento": "FGA"},
            {"nome": "ANA", "departamento": "FGA"},  # repetida na mesma unidade
        ]
        self.assertEqual(
            professores_em_varias_unidades(professores), {"ANA": ["FCTE", "FGA"]}
        )

    def test_vazio(self):
        self.assertEqual(professores_em_varias_unidades([]), {})


if __name__ == "__main__":
    unittest.main()
