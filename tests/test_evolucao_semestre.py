"""Evolução das notas do professor por semestre (issue #224, RF12), com o cliente falso."""
import re
import unittest

from app import create_app
from app import grafico
from app.repositorio import AvaliacaoRepository
from tests.fake_supabase import ClienteFalso

NOTAS_BOAS = {'didatica': 5, 'clareza': 4, 'organizacao': 4, 'disponibilidade': 5,
              'dificuldade': 2}
NOTAS_MEDIAS = {'didatica': 3, 'clareza': 3, 'organizacao': 2, 'disponibilidade': 4,
                'dificuldade': 4}


def semear(cliente, ano, periodo, notas, professor_id=1, disciplina_id=10):
    tabela = cliente.tabelas['avaliacoes']
    tabela.append({'id': len(tabela) + 1, 'usuario_id': f'u{len(tabela) + 1}',
                   'professor_id': professor_id, 'disciplina_id': disciplina_id,
                   'ano': ano, 'periodo': periodo, **notas})


class TestMediasPorSemestre(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.repo = AvaliacaoRepository(self.cliente)

    def test_agrupa_e_ordena_do_mais_antigo_ao_mais_recente(self):
        semear(self.cliente, 2026, 2, NOTAS_BOAS)
        semear(self.cliente, 2025, 2, NOTAS_MEDIAS)
        semear(self.cliente, 2026, 1, NOTAS_MEDIAS)
        semear(self.cliente, 2026, 1, NOTAS_BOAS)
        semestres = self.repo.medias_por_semestre(1)
        self.assertEqual([(s['ano'], s['periodo'], s['quantidade']) for s in semestres],
                         [(2025, 2, 1), (2026, 1, 2), (2026, 2, 1)])
        self.assertEqual(semestres[1]['medias']['didatica'], 4)
        self.assertEqual(semestres[1]['medias']['dificuldade'], 3)

    def test_ignora_outro_professor_notas_invalidas_e_semestre_vazio(self):
        semear(self.cliente, 2026, 1, NOTAS_BOAS)
        semear(self.cliente, 2026, 1, NOTAS_MEDIAS, professor_id=2)
        semear(self.cliente, 2025, 1, {**NOTAS_BOAS, 'clareza': 9})
        semear(self.cliente, None, None, NOTAS_BOAS)
        semestres = self.repo.medias_por_semestre(1)
        self.assertEqual([(s['ano'], s['periodo'], s['quantidade']) for s in semestres],
                         [(2026, 1, 1)])

    def test_sem_avaliacoes(self):
        self.assertEqual(self.repo.medias_por_semestre(1), [])


class TestGeometria(unittest.TestCase):
    def ponto(self, rotulo, valor):
        return {'rotulo': rotulo, 'valor': valor, 'quantidade': 1}

    def test_escala_fixa_de_1_a_5(self):
        g = grafico.montar_grafico([self.ponto('2025/2', 1), self.ponto('2026/1', 5)])
        baixo, alto = g['pontos']
        self.assertEqual(baixo['y'], grafico.ALTURA - grafico.MARGEM_BASE)
        self.assertEqual(alto['y'], grafico.MARGEM_TOPO)
        self.assertEqual(baixo['x'], grafico.MARGEM_ESQUERDA)
        self.assertEqual(alto['x'], grafico.LARGURA - grafico.MARGEM_DIREITA)
        self.assertEqual(g['caminho'], f"M{baixo['x']},{baixo['y']} L{alto['x']},{alto['y']}")
        self.assertEqual([l['nota'] for l in g['grade']], [1, 2, 3, 4, 5])

    def test_pontos_dentro_do_viewbox(self):
        pontos = [self.ponto(f'20{20 + i}/1', 1 + (i % 5)) for i in range(6)]
        for p in grafico.montar_grafico(pontos)['pontos']:
            self.assertTrue(0 <= p['x'] <= grafico.LARGURA)
            self.assertTrue(0 <= p['y'] <= grafico.ALTURA)

    def test_mostra_so_os_semestres_mais_recentes(self):
        pontos = [self.ponto(f'{2015 + i}/1', 3) for i in range(10)]
        g = grafico.montar_grafico(pontos)
        self.assertEqual(len(g['pontos']), grafico.MAXIMO_SEMESTRES_GRAFICO)
        self.assertEqual(g['pontos'][-1]['rotulo'], '2024/1')

    def test_um_ponto_fica_no_centro_e_vazio_vira_none(self):
        g = grafico.montar_grafico([self.ponto('2026/1', 3)])
        largura_util = grafico.LARGURA - grafico.MARGEM_ESQUERDA - grafico.MARGEM_DIREITA
        self.assertEqual(g['pontos'][0]['x'], grafico.MARGEM_ESQUERDA + largura_util / 2)
        self.assertIsNone(grafico.montar_grafico([]))
        self.assertIsNone(grafico.montar_grafico([self.ponto('2026/1', None)]))


class TestEvolucaoNoPerfil(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                               'SUPABASE_CLIENT': self.cliente})
        self.web = self.app.test_client()

    def secao(self, caminho='/professores/1'):
        html = self.web.get(caminho, headers={'Accept': 'text/html'}).get_data(as_text=True)
        inicio = html.index('<section class="evolucao"')
        return html[inicio:html.index('</section>', inicio)]

    def test_grafico_e_tabela_com_dois_semestres(self):
        semear(self.cliente, 2025, 2, NOTAS_MEDIAS)
        semear(self.cliente, 2026, 1, NOTAS_BOAS)
        secao = self.secao()
        self.assertIn('<svg class="grafico-evolucao"', secao)
        self.assertIn('role="img"', secao)
        self.assertIn('Média geral por semestre', secao)
        # Média geral sem a dificuldade: (3+3+2+4)/4 = 3 e (5+4+4+5)/4 = 4,5
        self.assertIn('De 3 em 2025/2 para 4,5 em 2026/1, em 2 semestres.', secao)
        self.assertIn('<title>2026/1: 4,5 (1 avaliação)</title>', secao)
        self.assertIn('<table>', secao)
        self.assertIn('<th scope="row">2025/2</th>', secao)
        # Tabela do mais recente para o mais antigo
        self.assertLess(secao.index('<th scope="row">2026/1</th>'),
                        secao.index('<th scope="row">2025/2</th>'))

    def test_seletor_de_criterio(self):
        semear(self.cliente, 2025, 2, NOTAS_MEDIAS)
        semear(self.cliente, 2026, 1, NOTAS_BOAS)
        secao = self.secao('/professores/1?evolucao_criterio=dificuldade')
        self.assertIn('Dificuldade por semestre', secao)
        self.assertIn('De 4 em 2025/2 para 2 em 2026/1', secao)
        self.assertIn('1 = muito fácil; 5 = muito difícil', secao)
        ativo = re.search(r'<a class="filter active"[^>]*>([^<]+)</a>', secao)
        self.assertEqual(ativo.group(1), 'Dificuldade')
        self.assertIn('evolucao_criterio=didatica', secao)
        self.assertIn('#evolucao', secao)

    def test_criterio_invalido_volta_para_media_geral(self):
        semear(self.cliente, 2025, 2, NOTAS_MEDIAS)
        semear(self.cliente, 2026, 1, NOTAS_BOAS)
        secao = self.secao('/professores/1?evolucao_criterio=%3Cscript%3E')
        self.assertIn('Média geral por semestre', secao)
        self.assertNotIn('<script>', secao)

    def test_um_semestre_mostra_estado_vazio(self):
        semear(self.cliente, 2026, 1, NOTAS_BOAS)
        semear(self.cliente, 2026, 1, NOTAS_MEDIAS)
        secao = self.secao()
        self.assertNotIn('<svg', secao)
        self.assertIn('de um só semestre (2026/1)', secao)

    def test_sem_avaliacoes(self):
        secao = self.secao()
        self.assertNotIn('<svg', secao)
        self.assertIn('Ainda não há avaliações para mostrar a evolução', secao)

    def test_sem_style_inline_por_causa_da_csp(self):
        semear(self.cliente, 2025, 2, NOTAS_MEDIAS)
        semear(self.cliente, 2026, 1, NOTAS_BOAS)
        secao = self.secao()
        self.assertNotIn('style=', secao)
        self.assertNotIn('<script', secao)

    def test_preserva_os_demais_filtros_do_perfil(self):
        semear(self.cliente, 2025, 2, NOTAS_MEDIAS)
        semear(self.cliente, 2026, 1, NOTAS_BOAS)
        secao = self.secao('/professores/1?disciplina_id=10&comentarios_disciplina=10')
        link = re.search(r'href="([^"]*evolucao_criterio=clareza[^"]*)"', secao).group(1)
        self.assertIn('disciplina_id=10', link)
        self.assertIn('comentarios_disciplina=10', link)


if __name__ == '__main__':
    unittest.main()
