import unittest
from unittest.mock import patch

from app import create_app
from app.repositorio import AvaliacaoRepository
from app.validacoes import CRITERIOS
from tests.fake_supabase import ClienteFalso


class TestComparacao(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.repositorio = AvaliacaoRepository(self.cliente)
        self.web = create_app({'TESTING': True, 'SECRET_KEY': 'teste-comparacao',
                               'SUPABASE_CLIENT': self.cliente}).test_client()

    def avaliar(self, professor_id, nota, disciplina_id=10, **notas):
        self.cliente.table('avaliacoes').insert({
            'professor_id': professor_id, 'disciplina_id': disciplina_id,
            **dict.fromkeys(CRITERIOS, nota), **notas}).execute()

    def test_medias_gerais_e_por_disciplina(self):
        self.avaliar(1, 5)
        self.avaliar(1, 1, disciplina_id=20, dificuldade=3)
        self.avaliar(2, 2)
        resultado = self.repositorio.calcular_medias(1)
        self.assertEqual(resultado['quantidade'], 2)
        self.assertEqual(resultado['medias']['didatica'], 3)
        self.assertEqual(resultado['medias']['dificuldade'], 4)
        self.assertEqual(self.repositorio.calcular_medias(1, 10)['medias']['didatica'], 5)

    def test_medias_ignoram_invalidas_e_paginam(self):
        self.avaliar(1, 4)
        self.avaliar(1, 2)
        self.avaliar(1, 5)
        for valor in (None, True, '4', 6, 0):
            self.avaliar(1, 5, clareza=valor)
        with patch('app.repositorio.TAMANHO_PAGINA', 2):
            resultado = self.repositorio.calcular_medias(1)
        self.assertEqual(resultado['quantidade'], 3)
        self.assertAlmostEqual(resultado['medias']['clareza'], 11 / 3)

    def test_selecao_inicial_e_preenchida_pelo_perfil(self):
        for caminho in ('/comparar', '/comparar?professor_1=1'):
            resposta = self.web.get(caminho)
            self.assertEqual(resposta.status_code, 200)
            self.assertIn('Professor 2', resposta.text)
            self.assertNotIn('<table', resposta.text)
        self.assertIn('value="1" selected', resposta.text)
        for caminho in ('/professores', '/professores/1', '/professores/3'):
            html = self.web.get(caminho).text
            self.assertIn('/comparar?professor_1=', html)

    def test_comparacao_publica_com_todos_os_criterios(self):
        self.avaliar(1, 5)
        self.avaliar(1, 4, dificuldade=1)
        self.avaliar(2, 2)
        resposta = self.web.get('/comparar?professor_1=1&professor_2=2')
        self.assertEqual(resposta.status_code, 200)
        for texto in (*CRITERIOS.values(), 'JOSÉ ÁVILA', 'MARIA LIMA', '4,50 / 5',
                      '3,00 / 5', '2,00 / 5', '<td>2</td>', '<td>1</td>'):
            self.assertIn(texto, resposta.text)
        self.avaliar(1, 3)
        self.assertIn('4,00 / 5', self.web.get('/comparar?professor_1=1&professor_2=2').text)

    def test_sem_avaliacoes_em_um_ou_ambos_os_lados(self):
        caminho = '/comparar?professor_1=1&professor_2=3'
        resposta = self.web.get(caminho)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.text.count('ainda não há avaliações válidas'), 2)
        self.assertNotIn('None', resposta.text)
        self.avaliar(1, 5)
        resposta = self.web.get(caminho)
        self.assertEqual(resposta.text.count('ainda não há avaliações válidas'), 1)
        self.assertIn('5,00 / 5', resposta.text)
        self.assertIn('Sem avaliações', resposta.text)

    def test_parametros_invalidos_e_repetidos(self):
        for parametros in ('professor_1=1&professor_2=1', 'professor_1=abc',
                           'professor_1=-1', 'professor_1=999',
                           'professor_1=1&professor_2=', 'professor_2=2'):
            with self.subTest(parametros=parametros):
                resposta = self.web.get('/comparar?' + parametros)
                self.assertEqual(resposta.status_code, 400)
                self.assertNotIn('<table', resposta.text)
                self.assertIn('role="alert"', resposta.text)

    def test_catalogo_vazio_ou_com_um_professor(self):
        self.cliente.tabelas['professores'] = []
        self.assertIn('pelo menos dois professores', self.web.get('/comparar').text)
        self.cliente.tabelas['professores'].append({'id': 1, 'nome': 'Ana', 'departamento': ''})
        resposta = self.web.get('/comparar')
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('pelo menos dois professores', resposta.text)


if __name__ == '__main__':
    unittest.main()
