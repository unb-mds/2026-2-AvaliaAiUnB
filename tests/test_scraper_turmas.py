import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))

from turmas_sigaa import montar_payload_turmas


def turma(prof, disc, depto="FCTE - GAMA", ano=2026, periodo=2):
    return {
        "disciplina_codigo": disc,
        "professor_nome": prof,
        "professor_departamento": depto,
        "ano": ano,
        "periodo": periodo,
    }


class TestMontarPayloadTurmas(unittest.TestCase):
    mapa_prof = {("ANA", "FCTE - GAMA"): 1, ("JOAO", "FCTE - GAMA"): 2}
    mapa_disc = {"FGA0001": 10, "FGA0002": 20}

    def test_monta_ids_ano_periodo(self):
        payload = montar_payload_turmas(
            [turma("ANA", "FGA0001")], self.mapa_prof, self.mapa_disc
        )
        self.assertEqual(
            payload,
            [{"professor_id": 1, "disciplina_id": 10, "ano": 2026, "periodo": 2}],
        )

    def test_deduplica_pela_chave_unica(self):
        turmas = [
            turma("ANA", "FGA0001"),
            turma("ANA", "FGA0001"),  # outra turma do mesmo prof/disciplina
            turma("JOAO", "FGA0001"),
            turma("ANA", "FGA0002"),
        ]
        payload = montar_payload_turmas(turmas, self.mapa_prof, self.mapa_disc)
        self.assertEqual(len(payload), 3)

    def test_ignora_sem_id(self):
        turmas = [turma("MARIA", "FGA0001"), turma("ANA", "XXX0000")]
        self.assertEqual(
            montar_payload_turmas(turmas, self.mapa_prof, self.mapa_disc), []
        )

    def test_vazio(self):
        self.assertEqual(montar_payload_turmas([], {}, {}), [])

    def test_ignora_campos_extras(self):
        t = turma("ANA", "FGA0001")
        t["docentes_brutos"] = "ANA (60h)"
        payload = montar_payload_turmas([t], self.mapa_prof, self.mapa_disc)
        self.assertNotIn("docentes_brutos", payload[0])


if __name__ == "__main__":
    unittest.main()
