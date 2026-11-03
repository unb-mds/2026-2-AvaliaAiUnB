import unittest
from unittest.mock import patch

from app import create_app
from app.repositorio import MINIMO_AVALIACOES_RANKING, ProfessorRepository
from app.validacoes import CRITERIOS
from tests.fake_supabase import ClienteFalso


class TestRanking(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.professores = ProfessorRepository(self.cliente)
        self.web = create_app({'TESTING': True, 'SUPABASE_CLIENT': self.cliente}).test_client()

    def avaliar(self, professor_id, quantidade=MINIMO_AVALIACOES_RANKING, nota=4, **notas):
        for _ in range(quantidade):
            self.cliente.table('avaliacoes').insert({
                'professor_id': professor_id, 'disciplina_id': 10,
                **dict.fromkeys(CRITERIOS, nota), **notas,
            }).execute()

    def test_minimo_de_avaliacoes_e_ordem_por_media(self):
        self.avaliar(1, quantidade=MINIMO_AVALIACOES_RANKING - 1, nota=5)
        self.avaliar(2, nota=4)
        self.avaliar(3, nota=3)
        ranking = self.professores.ranking()
        self.assertEqual([(p['id'], p['posicao'], p['media'], p['quantidade']) for p in ranking],
                         [(2, 1, 4, 5), (3, 2, 3, 5)])
        self.avaliar(1, quantidade=1, nota=5)
        self.assertEqual(self.professores.ranking()[0]['id'], 1)

    def test_media_por_avaliacao_entre_disciplinas_e_periodos_sem_dificuldade(self):
        self.avaliar(1, quantidade=4, nota=5, dificuldade=1)
        self.avaliar(1, quantidade=1, nota=1, dificuldade=5)
        self.cliente.tabelas['avaliacoes'][-1].update(disciplina_id=20, ano=2025, periodo=1)
        professor, = self.professores.ranking()
        self.assertEqual(professor['quantidade'], 5)
        self.assertEqual(professor['media'], 4.2)
        self.cliente.tabelas['avaliacoes'][-1].update(didatica=5, clareza=4, organizacao=3)
        self.assertEqual(self.professores.ranking()[0]['media'], 4.65)

    def test_avaliacoes_invalidas_nao_contam_para_media_nem_minimo(self):
        self.avaliar(1, quantidade=4)
        for valor in (None, 0, 6, '5', True):
            self.avaliar(1, quantidade=1, didatica=valor)
        self.avaliar(1, quantidade=1, dificuldade=None)
        self.avaliar(1, quantidade=1)
        del self.cliente.tabelas['avaliacoes'][-1]['clareza']
        self.assertEqual(self.professores.ranking(), [])
        self.avaliar(1, quantidade=1)
        professor, = self.professores.ranking()
        self.assertEqual((professor['media'], professor['quantidade']), (4, 5))

    def test_desempates_por_quantidade_nome_e_id(self):
        self.cliente.tabelas['professores'].append(
            {'id': 4, 'nome': 'JOSÉ ÁVILA', 'departamento': 'FCTE'})
        for professor_id in (1, 4, 2):
            self.avaliar(professor_id)
        self.avaliar(3, quantidade=6)
        self.assertEqual([p['id'] for p in self.professores.ranking()], [3, 1, 4, 2])

    def test_paginacao_e_ordenacao_antes_do_arredondamento(self):
        self.avaliar(1, quantidade=1001, nota=4)
        self.avaliar(2, quantidade=1000, nota=4)
        self.cliente.tabelas['avaliacoes'][-1]['didatica'] = 5
        ranking = self.professores.ranking()
        self.assertEqual([p['id'] for p in ranking], [2, 1])
        self.assertEqual([p['quantidade'] for p in ranking], [1000, 1001])
        self.assertGreater(ranking[0]['media'], ranking[1]['media'])
        self.assertEqual(round(ranking[0]['media'], 2), round(ranking[1]['media'], 2))
        with patch('app.repositorio.TAMANHO_PAGINA', 2):
            self.assertEqual(self.professores.ranking(), ranking)

    def test_pagina_vazia_e_links_de_acesso(self):
        self.avaliar(1, quantidade=4, nota=5)
        resposta = self.web.get('/ranking')
        self.assertEqual(resposta.status_code, 200)
        html = resposta.get_data(as_text=True)
        self.assertIn('Ainda não há professores com pelo menos 5 avaliações válidas', html)
        self.assertNotIn('JOSÉ ÁVILA', html)
        for caminho in ('/', '/professores'):
            self.assertIn('href="/ranking"', self.web.get(caminho).get_data(as_text=True))
        self.cliente.tabelas['professores'].clear()
        self.assertEqual(self.web.get('/ranking').status_code, 200)

    def test_pagina_publica_com_posicao_media_quantidade_e_perfil(self):
        self.avaliar(1, nota=5, clareza=4)
        self.avaliar(2, quantidade=6, nota=4)
        resposta = self.web.get('/ranking')
        self.assertEqual(resposta.status_code, 200)
        html = resposta.get_data(as_text=True)
        for texto in ('Posição', 'Média geral', 'Avaliações', '1º', '2º', '4,75 / 5',
                      '<td>5</td>', '<td>6</td>', 'href="/professores/1"',
                      'href="/professores"', 'href="/"'):
            self.assertIn(texto, html)
        self.assertLess(html.index('JOSÉ ÁVILA'), html.index('MARIA LIMA'))
        self.assertNotIn('SEM TURMA', html)
        self.cliente.tabelas['professores'][0]['nome'] = '<script>alert(1)</script>'
        html = self.web.get('/ranking').get_data(as_text=True)
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)


if __name__ == '__main__':
    unittest.main()
