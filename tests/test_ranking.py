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
        self.web = create_app({'TESTING': True, 'SECRET_KEY': 'chave-de-teste', 'SUPABASE_CLIENT': self.cliente}).test_client()

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
                      '5 avaliações', '6 avaliações', 'class="rankrow"', 'href="/professores/1"',
                      'href="/professores"', 'href="/"'):
            self.assertIn(texto, html)
        self.assertLess(html.index('JOSÉ ÁVILA'), html.index('MARIA LIMA'))
        self.assertNotIn('SEM TURMA', html)
        self.cliente.tabelas['professores'][0]['nome'] = '<script>alert(1)</script>'
        html = self.web.get('/ranking').get_data(as_text=True)
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)

    def test_ranking_filtra_por_departamento_e_mantem_minimo(self):
        self.cliente.tabelas['professores'] = [
            {'id': 1, 'nome': 'JOSÉ ÁVILA', 'departamento': 'MAT'},
            {'id': 2, 'nome': 'MARIA LIMA', 'departamento': 'CIC'},
            {'id': 3, 'nome': 'CARLOS SOUZA', 'departamento': 'CIC'},
            {'id': 4, 'nome': 'ANA COSTA', 'departamento': 'CIC'},
        ]
        self.avaliar(1, nota=5)
        self.avaliar(2, nota=3)
        self.avaliar(3, nota=4)
        self.avaliar(4, quantidade=MINIMO_AVALIACOES_RANKING - 1, nota=5)

        ranking_cic = self.professores.ranking('cic')
        self.assertEqual(
            [(p['id'], p['posicao'], p['media']) for p in ranking_cic],
            [(3, 1, 4), (2, 2, 3)],
        )
        self.assertEqual([p['id'] for p in self.professores.ranking()], [1, 3, 2])

    def test_pagina_ranking_filtra_por_departamento_e_exibe_seletor(self):
        self.cliente.tabelas['professores'] = [
            {'id': 1, 'nome': 'JOSÉ ÁVILA', 'departamento': 'MAT'},
            {'id': 2, 'nome': 'MARIA LIMA', 'departamento': 'CIC'},
            {'id': 3, 'nome': 'ANA COSTA', 'departamento': 'FCTE'},
        ]
        self.avaliar(1, nota=5)
        self.avaliar(2, nota=4)

        filtrado = self.web.get('/ranking?departamento=CIC')
        self.assertEqual(filtrado.status_code, 200)
        html_cic = filtrado.get_data(as_text=True)
        self.assertIn('name="departamento"', html_cic)
        self.assertIn('<option value="CIC" selected>CIC</option>', html_cic)
        self.assertIn('Classificação do departamento CIC', html_cic)
        self.assertIn('MARIA LIMA', html_cic)
        self.assertNotIn('JOSÉ ÁVILA', html_cic)
        self.assertIn('Ver ranking geral', html_cic)

        vazio = self.web.get('/ranking?departamento=FCTE')
        self.assertEqual(vazio.status_code, 200)
        html_vazio = vazio.get_data(as_text=True)
        self.assertIn('Ainda não há professores no departamento FCTE com pelo menos 5 avaliações válidas', html_vazio)
        self.assertIn('Ver ranking geral de todos os departamentos', html_vazio)
if __name__ == '__main__':
    unittest.main()
