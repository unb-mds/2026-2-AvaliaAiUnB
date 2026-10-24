import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))

from persistencia_sigaa import (
    CONFLITO_DISCIPLINAS,
    CONFLITO_PROFESSORES,
    CONFLITO_TURMAS,
    salvar_disciplinas,
    salvar_professores,
    salvar_turmas,
)
from tests.fake_supabase import ClienteFalso

FCTE = "FCTE - FACULDADE DE CIÊNCIAS E TECNOLOGIAS EM ENGENHARIA"
FGA = "FACULDADE DO GAMA"

PROFESSORES = [
    {"nome": "ANA NOVA", "departamento": FCTE},
    {"nome": "BRUNO NOVO", "departamento": FCTE},
    {"nome": "ANA NOVA", "departamento": FGA},  # mesmo nome em outra unidade
]
DISCIPLINAS = [
    {"codigo": "FGA0100", "nome": "ALGORITMOS"},
    {"codigo": "FGA0200", "nome": "REDES"},
]


def turma(prof, depto, disc):
    return {
        "disciplina_codigo": disc,
        "professor_nome": prof,
        "professor_departamento": depto,
        "ano": 2026,
        "periodo": 2,
    }


TURMAS = [
    turma("ANA NOVA", FCTE, "FGA0100"),
    turma("ANA NOVA", FCTE, "FGA0100"),  # duplicada na origem
    turma("BRUNO NOVO", FCTE, "FGA0200"),
    turma("ANA NOVA", FGA, "FGA0200"),
]


def gravar(cliente):
    mapa_prof = salvar_professores(PROFESSORES, cliente)
    mapa_disc = salvar_disciplinas(DISCIPLINAS, cliente)
    salvar_turmas(TURMAS, mapa_prof, mapa_disc, cliente)
    return mapa_prof, mapa_disc


def estado(cliente):
    return {
        nome: [dict(l) for l in cliente.tabelas[nome]]
        for nome in ("professores", "disciplinas", "turmas")
    }


class TestPersistenciaIdempotente(unittest.TestCase):
    def test_grava_uma_vez(self):
        cliente = ClienteFalso()
        antes = len(cliente.tabelas["professores"])
        gravar(cliente)
        self.assertEqual(len(cliente.tabelas["professores"]), antes + 3)
        self.assertEqual(len(cliente.tabelas["disciplinas"]), 2)
        self.assertEqual(len(cliente.tabelas["turmas"]), 3)

    def test_rodar_duas_vezes_nao_duplica(self):
        cliente = ClienteFalso()
        mapas1 = gravar(cliente)
        estado1 = estado(cliente)

        mapas2 = gravar(cliente)

        self.assertEqual(estado(cliente), estado1)
        self.assertEqual(mapas2, mapas1)  # ids estáveis

    def test_usa_as_chaves_de_conflito_esperadas(self):
        cliente = ClienteFalso()
        gravar(cliente)
        self.assertEqual(
            cliente.upserts,
            [
                ("professores", CONFLITO_PROFESSORES),
                ("disciplinas", CONFLITO_DISCIPLINAS),
                ("turmas", CONFLITO_TURMAS),
            ],
        )
        self.assertEqual(CONFLITO_PROFESSORES, "nome,departamento")
        self.assertEqual(CONFLITO_DISCIPLINAS, "codigo")
        self.assertEqual(CONFLITO_TURMAS, "professor_id,disciplina_id,ano,periodo")

    def test_listas_vazias_nao_gravam(self):
        cliente = ClienteFalso()
        self.assertEqual(salvar_professores([], cliente), {})
        self.assertEqual(salvar_disciplinas([], cliente), {})
        salvar_turmas([], {}, {}, cliente)
        self.assertEqual(cliente.upserts, [])


if __name__ == "__main__":
    unittest.main()
