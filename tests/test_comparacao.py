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

    def test_cartoes_editoriais_usam_as_medias_calculadas(self):
        self.avaliar(1, 5, dificuldade=1)
        self.avaliar(1, 3, dificuldade=5)
        self.avaliar(2, 2, dificuldade=5)
        resposta = self.web.get('/comparar?professor_1=1&professor_2=2')
        self.assertEqual(resposta.status_code, 200)
        resumo = resposta.text.split('aria-label="Resumo da comparação"', 1)[1].split('</div>\n        <details', 1)[0]
        self.assertEqual(resumo.count('class="compare-card"'), 2)
        self.assertIn('class="bigscore">4,00', resumo)
        self.assertIn('class="bigscore">2,00', resumo)
        self.assertIn('<strong>2</strong> avaliações registradas', resumo)
        self.assertIn('href="/professores/1"', resumo)
        self.assertIn('href="/professores/2"', resumo)
        self.assertNotIn('fictícios', resumo)

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
        self._vincular(2)
        resposta_vazia = self.web.get('/comparar')
        self.assertEqual(resposta_vazia.status_code, 200)
        self.assertIn('Escolher disciplina', resposta_vazia.text)
        self.assertNotIn('<table', resposta_vazia.text)

        for caminho in ('/comparar?professor_1=1', '/comparar?professor_1=1&disciplina_id=10'):
            resposta = self.web.get(caminho)
            self.assertEqual(resposta.status_code, 200)
            self.assertIn('name="professor_1" value="1"', resposta.text)
            self.assertIn('value="1" selected', resposta.text)
            self.assertIn('Professor 2', resposta.text)
            self.assertNotIn('<table', resposta.text)

        for caminho in ('/professores', '/professores/1', '/professores/3'):
            html = self.web.get(caminho).text
            self.assertIn('/comparar?professor_1=', html)

    def test_comparar_professor_sem_disciplina_compartilhada_pre_seleciona_no_modo_geral(self):
        resposta = self.web.get('/comparar?professor_1=3')
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('value="3" selected', resposta.text)
        self.assertIn('Professor 2', resposta.text)
        self.assertNotIn('role="alert"', resposta.text)
        self.assertNotIn('<table', resposta.text)

    def test_comparacao_publica_com_todos_os_criterios(self):
        self.avaliar(1, 5)
        self.avaliar(1, 4, dificuldade=1)
        self.avaliar(2, 2)
        resposta = self.web.get('/comparar?professor_1=1&professor_2=2')
        self.assertEqual(resposta.status_code, 200)
        # A dificuldade (média 3) aparece como barra, com o valor no aria-label
        for texto in (*CRITERIOS.values(), 'JOSÉ ÁVILA', 'MARIA LIMA', '4,50 / 5',
                      'aria-label="Dificuldade 3 de 5', '2,00 / 5', '<td>2</td>', '<td>1</td>'):
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

    def _vincular(self, professor_id):
        vinculo = self.cliente.tabelas['vw_professor_disciplina'][0]
        self.cliente.tabelas['vw_professor_disciplina'].append({
            **vinculo, 'professor_id': professor_id,
        })

    def test_compara_tres_professores_com_notas_apenas_da_disciplina(self):
        self._vincular(2)
        self._vincular(3)
        self.avaliar(1, 5)
        self.avaliar(1, 1, disciplina_id=20)
        self.avaliar(2, 2)
        resposta = self.web.get('/comparar?disciplina_id=10&professor=1&professor=2'
                                '&professor=3&comparar=1')
        self.assertEqual(resposta.status_code, 200)
        for texto in ('CÁLCULO 1', 'JOSÉ ÁVILA', 'MARIA LIMA', 'SEM TURMA', '5,00 / 5',
                      '2,00 / 5', 'Sem avaliações', 'disciplina_id=10'):
            self.assertIn(texto, resposta.text)
        self.assertNotIn('3,00 / 5', resposta.text)

    def test_adiciona_remove_e_rejeita_selecoes_invalidas(self):
        self._vincular(2)
        self._vincular(3)
        base = '/comparar?disciplina_id=10'
        adicao = self.web.get(base + '&professor=1&professor=2&adicionar=1')
        self.assertEqual(adicao.text.count('name="professor"'), 3)
        remocao = self.web.get(base + '&professor=1&professor=2&professor=3&remover=1')
        self.assertEqual(remocao.text.count('name="professor"'), 2)
        self.assertIn('value="3" selected', remocao.text)
        self.assertNotIn('value="2" selected', remocao.text)
        for params in ('&professor=1', '&professor=1&professor=1', '&professor=1&professor=999'):
            with self.subTest(params=params):
                resposta = self.web.get(base + params + '&comparar=1')
                self.assertEqual(resposta.status_code, 400)
                self.assertNotIn('<table', resposta.text)

    def test_professor_1_escolhe_automaticamente_disciplina_com_pelo_menos_dois_professores(self):
        # Professor 1 ministra disciplina 10 (sozinho) e disciplina 20 (com professor 2)
        self.cliente.tabelas['vw_professor_disciplina'].append({
            'professor_id': 1, 'professor_nome': 'JOSÉ ÁVILA', 'departamento': 'MAT',
            'disciplina_id': 20, 'disciplina': 'FÍSICA 1', 'codigo_disciplina': 'IFD0171',
            'ano': 2026, 'periodo': 2,
        })
        resposta = self.web.get('/comparar?professor_1=1')
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('name="disciplina_id" value="20"', resposta.text)
        self.assertIn('value="1" selected', resposta.text)
        self.assertIn('MARIA LIMA', resposta.text)

        comparado = self.web.get('/comparar?disciplina_id=20&professor=1&professor=2&comparar=1')
        self.assertEqual(comparado.status_code, 200)
        self.assertIn('<table class="tabela-comparacao">', comparado.text)
        self.assertIn('JOSÉ ÁVILA', comparado.text)
        self.assertIn('MARIA LIMA', comparado.text)
    def test_compara_professores_de_disciplinas_diferentes_no_modo_livre(self):
        # Professor 1 ministra Cálculo 1 (id=10) e Professor 2 ministra Física 1 (id=20)
        self.cliente.tabelas['vw_professor_disciplina'].append({
            'professor_id': 2, 'professor_nome': 'MARIA LIMA', 'departamento': 'FIS',
            'disciplina_id': 20, 'disciplina': 'FÍSICA 1', 'codigo_disciplina': 'IFD0171',
            'ano': 2026, 'periodo': 2,
        })
        self.avaliar(1, 5, disciplina_id=10, dificuldade=2)
        self.avaliar(2, 3, disciplina_id=20, dificuldade=4)

        resposta = self.web.get('/comparar?modo=livre&professor=1&professor=2&comparar=1')
        self.assertEqual(resposta.status_code, 200)
        html = resposta.text
        for texto in ('ministram disciplinas diferentes', 'CÁLCULO 1', 'FÍSICA 1',
                      'JOSÉ ÁVILA', 'MARIA LIMA', 'Média geral', '5,00 / 5', '3,00 / 5'):
            self.assertIn(texto, html)

    def test_modo_livre_adiciona_remove_e_pre_seleciona_professor(self):
        pre = self.web.get('/comparar?modo=livre&professor_1=1')
        self.assertEqual(pre.status_code, 200)
        self.assertIn('value="1" selected', pre.text)

        adicao = self.web.get('/comparar?modo=livre&professor=1&professor=2&adicionar=1')
        self.assertEqual(adicao.status_code, 200)
        self.assertEqual(adicao.text.count('name="professor"'), 3)

        remocao = self.web.get('/comparar?modo=livre&professor=1&professor=2&professor=3&remover=1')
        self.assertEqual(remocao.status_code, 200)
        self.assertEqual(remocao.text.count('name="professor"'), 2)
        self.assertIn('value="3" selected', remocao.text)
        self.assertNotIn('value="2" selected', remocao.text)

    def test_modo_livre_rejeita_selecoes_invalidas(self):
        for params in ('&professor=1', '&professor=1&professor=1', '&professor=1&professor=999'):
            with self.subTest(params=params):
                resposta = self.web.get('/comparar?modo=livre' + params + '&comparar=1')
                self.assertEqual(resposta.status_code, 400)
                self.assertNotIn('<table', resposta.text)
                self.assertIn('role="alert"', resposta.text)

    def test_destaque_melhor_desempenho_e_regra_inversa_dificuldade(self):
        self._vincular(2)
        for _ in range(5):
            self.avaliar(1, 4, dificuldade=4)
            self.avaliar(2, 5, dificuldade=2)
        resposta = self.web.get('/comparar?disciplina_id=10&professor=1&professor=2&comparar=1')
        self.assertEqual(resposta.status_code, 200)
        html = resposta.text
        self.assertEqual(html.count('Melhor desempenho'), 1)
        self.assertEqual(html.count('Menor dificuldade'), 1)
        self.assertEqual(html.count('>Melhor<'), 5)
        self.assertIn('pelo menos 5 avaliações válidas', html)

    def test_destaque_exige_minimo_de_avaliacoes(self):
        self._vincular(2)
        for _ in range(5):
            self.avaliar(1, 3, dificuldade=3)
        for _ in range(4):
            self.avaliar(2, 5, dificuldade=1)
        resposta = self.web.get('/comparar?disciplina_id=10&professor=1&professor=2&comparar=1')
        self.assertEqual(resposta.status_code, 200)
        tabela = resposta.text[resposta.text.index('<table class="tabela-comparacao">'):]
        self.assertEqual(tabela.count('Melhor desempenho'), 1)
        pos_prof_1 = tabela.index('JOSÉ ÁVILA')
        pos_prof_2 = tabela.index('MARIA LIMA')
        pos_selo = tabela.index('Melhor desempenho')
        self.assertTrue(pos_prof_1 < pos_selo < pos_prof_2)

    def test_destaque_em_caso_de_empate(self):
        self._vincular(2)
        for _ in range(5):
            self.avaliar(1, 4, didatica=5, clareza=3, dificuldade=2)
            self.avaliar(2, 4, didatica=3, clareza=5, dificuldade=2)
        resposta = self.web.get('/comparar?disciplina_id=10&professor=1&professor=2&comparar=1')
        self.assertEqual(resposta.status_code, 200)
        html = resposta.text
        self.assertEqual(html.count('Melhor desempenho'), 2)
        self.assertEqual(html.count('Menor dificuldade'), 2)
        self.assertEqual(html.count('>Melhor<'), 8)

    def test_destaque_tambem_no_modo_livre(self):
        self.cliente.tabelas['vw_professor_disciplina'].append({
            'professor_id': 2, 'professor_nome': 'MARIA LIMA', 'departamento': 'FIS',
            'disciplina_id': 20, 'disciplina': 'FÍSICA 1', 'codigo_disciplina': 'IFD0171',
            'ano': 2026, 'periodo': 2,
        })
        for _ in range(5):
            self.avaliar(1, 5, disciplina_id=10, dificuldade=2)
            self.avaliar(2, 3, disciplina_id=20, dificuldade=4)
        resposta = self.web.get('/comparar?modo=livre&professor=1&professor=2&comparar=1')
        self.assertEqual(resposta.status_code, 200)
        tabela = resposta.text[resposta.text.index('<table class="tabela-comparacao">'):]
        self.assertEqual(tabela.count('Melhor desempenho'), 1)
        self.assertLess(tabela.index('JOSÉ ÁVILA'), tabela.index('Melhor desempenho'))
        self.assertLess(tabela.index('Melhor desempenho'), tabela.index('MARIA LIMA'))

if __name__ == '__main__':
    unittest.main()
