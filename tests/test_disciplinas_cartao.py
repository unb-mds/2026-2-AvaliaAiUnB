"""Ordem e agrupamento das disciplinas no cartão da lista de Consulta (issue #201)."""
import re
import unittest

from app import create_app
from tests.fake_supabase import ClienteFalso
from tests.test_dificuldade_consulta import avaliacao


class BaseDisciplinas(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                               'SUPABASE_CLIENT': self.cliente})
        self.web = self.app.test_client()
        self.cliente.tabelas['vw_professor_disciplina'] = []

    def disciplinas(self, *nomes):
        """Professor 1 passa a ministrar as disciplinas `nomes` (ids 101, 102, ...)."""
        for i, nome in enumerate(nomes, start=101):
            self.cliente.tabelas['vw_professor_disciplina'].append(
                {'professor_id': 1, 'disciplina_id': i, 'codigo_disciplina': f'COD{i}',
                 'disciplina': nome, 'ano': 2026, 'periodo': 1})

    def avaliar(self, nome_ou_id, quantidade):
        tabela = self.cliente.tabelas['avaliacoes']
        for _ in range(quantidade):
            tabela.append({**avaliacao(1, nome_ou_id, 3), 'id': len(tabela) + 1})

    def cartao(self):
        html = self.web.get('/professores').get_data(as_text=True)
        cartoes = re.findall(r'<li class="card card-interativo">.*?\n            </li>', html, re.S)
        return next(c for c in cartoes if 'JOSÉ ÁVILA' in c)

    @staticmethod
    def nomes(trecho):
        return re.findall(r'<span class="disciplina-titulo">(.*?) — ', trecho)

    def partes(self):
        """(nomes visíveis, nomes dentro do <details>, <details> ou None)."""
        cartao = self.cartao()
        detalhes = re.search(r'<details class="disciplinas-extras">.*?</details>', cartao, re.S)
        fora = cartao.replace(detalhes.group(0), '') if detalhes else cartao
        return self.nomes(fora), self.nomes(detalhes.group(0)) if detalhes else [], detalhes


class TestAteCincoDisciplinas(BaseDisciplinas):
    def test_cinco_mostram_todas_sem_details(self):
        self.disciplinas('A', 'B', 'C', 'D', 'E')
        visiveis, extras, detalhes = self.partes()

        self.assertEqual(sorted(visiveis), ['A', 'B', 'C', 'D', 'E'])
        self.assertIsNone(detalhes)
        self.assertNotIn('Ver mais', self.cartao())

    def test_uma_disciplina_continua_igual(self):
        self.disciplinas('A')
        visiveis, _, detalhes = self.partes()

        self.assertEqual(visiveis, ['A'])
        self.assertIsNone(detalhes)


class TestMaisDeCinco(BaseDisciplinas):
    def test_seis_mostram_quatro_e_dois_no_details(self):
        self.disciplinas('A', 'B', 'C', 'D', 'E', 'F')
        visiveis, extras, detalhes = self.partes()

        self.assertEqual(len(visiveis), 4)
        self.assertEqual(len(extras), 2)
        self.assertIn('<summary>Ver mais 2 disciplinas</summary>', detalhes.group(0))
        self.assertEqual(sorted(visiveis + extras), ['A', 'B', 'C', 'D', 'E', 'F'])

    def test_extras_usam_o_mesmo_formato_de_item(self):
        self.disciplinas('A', 'B', 'C', 'D', 'E', 'F', 'G')
        self.avaliar(106, 2)
        self.avaliar(107, 1)
        _, _, detalhes = self.partes()
        trecho = detalhes.group(0)

        self.assertEqual(trecho.count('<li class="disciplina-item">'), 3)
        self.assertIn('Ver mais 3 disciplinas', trecho)
        self.assertEqual(trecho.count('Sem avaliações ainda'), 3)   # as extras são as sem avaliação
        self.assertEqual(trecho.count('<ul class="disciplinas disciplinas-lista-extras">'), 1)

    def test_details_fica_dentro_do_cartao_antes_dos_botoes(self):
        self.disciplinas('A', 'B', 'C', 'D', 'E', 'F')
        cartao = self.cartao()

        self.assertLess(cartao.index('<details'), cartao.index('<div class="professor-acoes">'))
        self.assertGreater(cartao.index('<details class="disciplinas-extras">'), cartao.index('<ul class="disciplinas">'))


class TestOrdem(BaseDisciplinas):
    def test_mais_avaliacoes_primeiro_depois_sem_avaliacoes_e_empate_por_nome(self):
        self.disciplinas('ZETA', 'ALFA', 'BETA', 'GAMA', 'DELTA')   # ids 101..105
        self.avaliar(101, 1)    # ZETA 1
        self.avaliar(103, 3)    # BETA 3
        self.avaliar(104, 1)    # GAMA 1 (empata com ZETA)
        visiveis, _, _ = self.partes()

        self.assertEqual(visiveis, ['BETA', 'GAMA', 'ZETA', 'ALFA', 'DELTA'])

    def test_ordem_entre_visiveis_e_extras_e_nada_some(self):
        self.disciplinas('F', 'E', 'D', 'C', 'B', 'A')              # ids 101..106
        self.avaliar(101, 2)    # F
        self.avaliar(103, 5)    # D
        visiveis, extras, _ = self.partes()

        self.assertEqual(visiveis, ['D', 'F', 'A', 'B'])
        self.assertEqual(extras, ['C', 'E'])      # sem avaliações continuam presentes, no details

    def test_ordem_por_nome_ignora_acento_e_caixa(self):
        self.disciplinas('Álgebra', 'bases', 'Cálculo')
        visiveis, _, _ = self.partes()

        self.assertEqual(visiveis, ['Álgebra', 'bases', 'Cálculo'])


class TestRestoDoCartao(BaseDisciplinas):
    def test_botoes_e_metricas_continuam(self):
        self.disciplinas('A', 'B', 'C', 'D', 'E', 'F')
        self.avaliar(103, 2)
        cartao = self.cartao()

        self.assertIn('Dificuldade 3,0/5', cartao)
        self.assertIn('2 avaliações', cartao)
        self.assertIn('>Avaliar<', cartao)
        self.assertIn('>Comentários<', cartao)
        self.assertIn('Comparar este professor', cartao)

    def test_avaliar_com_uma_unica_disciplina_vai_direto_ao_formulario(self):
        self.disciplinas('A')

        self.assertIn('/avaliar/1?disciplina_id=101', self.cartao())


if __name__ == '__main__':
    unittest.main()
