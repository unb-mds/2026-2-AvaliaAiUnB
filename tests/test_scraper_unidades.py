import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))

from resumo_sigaa import Resumo
from unidades_sigaa import eh_unidade_de_pos, escolher_unidades

POS_ADM = "PROGRAMA DE PÓS-GRADUAÇÃO EM ADMINISTRAÇÃO - BRASÍLIA"
POS_BIO = (
    "PROGRAMA DE PÓS-GRADUAÇÃO PROFBIO ENSINO DE BIOLOGIA EM REDE NACIONAL "
    "(PROFISSIONAL) - BRASÍLIA"
)
POS_ELE = "PROGRAMA DE PÓS-GRADUAÇÃO PROFISSIONAL EM ENGENHARIA ELÉTRICA - BRASÍLIA"
DECANATO = "DECANATO DE PÓS-GRADUAÇÃO / DPG - BRASÍLIA"
FCTE = "FACULDADE DE CIÊNCIAS E TECNOLOGIAS EM ENGENHARIA - GAMA"

DISPONIVEIS = [
    ("1", FCTE),
    ("2", POS_ADM),
    ("3", DECANATO),
    ("4", POS_BIO),
    ("5", POS_ELE),
]


class TestEhUnidadeDePos(unittest.TestCase):
    def test_exemplos_reais(self):
        for texto in (POS_ADM, POS_BIO, POS_ELE):
            self.assertTrue(eh_unidade_de_pos(texto), texto)

    def test_nao_casa_decanato_nem_graduacao(self):
        self.assertFalse(eh_unidade_de_pos(DECANATO))
        self.assertFalse(eh_unidade_de_pos(FCTE))

    def test_variacoes_de_caixa_acento_e_hifen(self):
        self.assertTrue(eh_unidade_de_pos("programa de pos-graduacao em fisica"))
        self.assertTrue(eh_unidade_de_pos("  PROGRAMA DE  PÓS GRADUAÇÃO EM FÍSICA"))

    def test_so_vale_no_prefixo(self):
        self.assertFalse(eh_unidade_de_pos("CENTRO X - PROGRAMA DE PÓS-GRADUAÇÃO EM Y"))

    def test_vazio_e_none(self):
        self.assertFalse(eh_unidade_de_pos(""))
        self.assertFalse(eh_unidade_de_pos(None))


class TestEscolherUnidades(unittest.TestCase):
    def test_sem_filtro_tira_so_as_de_pos(self):
        resumo = Resumo()
        escolhidas = escolher_unidades(DISPONIVEIS, None, resumo)
        self.assertEqual(escolhidas, [("1", FCTE), ("3", DECANATO)])
        self.assertEqual(resumo.unidades_ignoradas_pos, [POS_ADM, POS_BIO, POS_ELE])
        self.assertEqual(resumo.codigo_saida(), 0)

    def test_pedida_de_pos_e_ignorada_e_registrada(self):
        resumo = Resumo()
        escolhidas = escolher_unidades(DISPONIVEIS, ["2", "1"], resumo)
        self.assertEqual(escolhidas, [("1", FCTE)])
        self.assertEqual(resumo.unidades_ignoradas_pos, [POS_ADM])
        self.assertEqual(resumo.codigo_saida(), 0)

    def test_pedidas_mantem_ordem_e_tiram_repetidas(self):
        escolhidas = escolher_unidades(DISPONIVEIS, ["3", "1", "3"], Resumo())
        self.assertEqual(escolhidas, [("3", DECANATO), ("1", FCTE)])

    def test_value_inexistente_e_erro(self):
        resumo = Resumo()
        escolhidas = escolher_unidades(DISPONIVEIS, ["999", "1"], resumo)
        self.assertEqual(escolhidas, [("1", FCTE)])
        self.assertEqual(resumo.unidades_puladas, [("999", "não existe no formulário")])
        self.assertEqual(resumo.codigo_saida(), 1)


if __name__ == "__main__":
    unittest.main()
