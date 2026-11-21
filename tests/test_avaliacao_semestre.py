"""Turma (semestre) cursada na avaliação e filtro de semestre nas médias (issue #252).

No cliente falso, o professor 1 deu CÁLCULO 1 (disciplina 10) em 2026/1 e 2026/2, e
o professor 2 deu FÍSICA 1 (disciplina 20) só em 2026/2."""
import re
import unittest

from flask_wtf.csrf import generate_csrf

from app import create_app
from app.repositorio import AvaliacaoRepository
from app.validacoes import CRITERIOS
from tests.fake_supabase import ClienteFalso, entrar_pela_web

NOTAS_INT = {**{c: 4 for c in CRITERIOS}, 'dificuldade': 3}
NOTAS = {**{c: str(v) for c, v in NOTAS_INT.items()}, 'disciplina_id': '10'}


class TestRepositorio(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.repo = AvaliacaoRepository(self.cliente)

    def semestres(self):
        return sorted((a['ano'], a['periodo']) for a in self.cliente.tabelas['avaliacoes'])

    def test_semestres_da_disciplina_do_mais_recente_ao_mais_antigo(self):
        self.assertEqual(self.repo.semestres_da_disciplina(1, 10), [(2026, 2), (2026, 1)])
        self.assertEqual(self.repo.semestres_da_disciplina(1, 20), [])

    def test_uma_avaliacao_por_semestre_cursado(self):
        self.assertTrue(self.repo.salvar('u1', 1, 10, NOTAS_INT, (2026, 1)))
        self.assertTrue(self.repo.salvar('u1', 1, 10, NOTAS_INT, (2026, 2)))
        self.assertFalse(self.repo.salvar('u1', 1, 10, NOTAS_INT, (2026, 1)))
        self.assertEqual(self.semestres(), [(2026, 1), (2026, 2)])
        self.assertEqual(self.repo.semestres_avaliados('u1', 1, 10), {(2026, 1), (2026, 2)})

    def test_sem_semestre_usa_a_turma_mais_recente(self):
        self.assertTrue(self.repo.salvar('u1', 1, 10, NOTAS_INT))
        self.assertEqual(self.semestres(), [(2026, 2)])
        self.assertFalse(self.repo.salvar('u1', 1, 10, NOTAS_INT))

    def test_recusa_semestre_sem_turma(self):
        with self.assertRaises(ValueError):
            self.repo.salvar('u1', 1, 10, NOTAS_INT, (2025, 1))
        self.assertEqual(self.semestres(), [])

    def test_restricao_unica_do_banco_vira_false(self):
        original = self.cliente.table

        def tabela(nome):
            consulta = original(nome)
            if nome == 'avaliacoes':
                executar = consulta.execute

                def execute():
                    if consulta.novo is not None:
                        raise RuntimeError('duplicate key value violates unique constraint (23505)')
                    return executar()
                consulta.execute = execute
            return consulta
        self.cliente.table = tabela
        self.assertFalse(self.repo.salvar('u1', 1, 10, NOTAS_INT, (2026, 1)))

    def test_medias_por_semestre(self):
        self.repo.salvar('u1', 1, 10, {**NOTAS_INT, 'didatica': 2}, (2026, 1))
        self.repo.salvar('u2', 1, 10, {**NOTAS_INT, 'didatica': 5}, (2026, 2))
        self.assertEqual(self.repo.calcular_medias(1, 10)['medias']['didatica'], 3.5)
        semestre = self.repo.calcular_medias(1, 10, (2026, 1))
        self.assertEqual((semestre['quantidade'], semestre['medias']['didatica']), (1, 2))


class BaseWeb(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                               'SUPABASE_CLIENT': self.cliente})
        self.app.add_url_rule('/teste/csrf', 'teste_csrf', generate_csrf)
        self.web = self.app.test_client()
        entrar_pela_web(self.web, self.cliente, 'ana@gmail.com', 'Ana')

    def ver(self, caminho):
        return self.web.get(caminho, headers={'Accept': 'text/html'}).get_data(as_text=True)

    def postar(self, dados, caminho='/avaliar/1', accept='text/html'):
        token = self.web.get('/teste/csrf').get_data(as_text=True)
        return self.web.post(caminho, data={**dados, 'csrf_token': token},
                             headers={'Accept': accept})

    def semestres(self):
        return sorted((a['ano'], a['periodo']) for a in self.cliente.tabelas['avaliacoes'])


class TestFormularioDeAvaliacao(BaseWeb):
    def test_lista_as_turmas_com_a_mais_recente_marcada(self):
        html = self.ver('/avaliar/1?disciplina_id=10')
        self.assertIn('Turma cursada', html)
        self.assertRegex(html, r'id="semestre-2026-2" value="2026-2"\s+checked')
        self.assertIn('id="semestre-2026-1" value="2026-1"', html)
        self.assertIn('mais recente', html)

    def test_semestre_da_url_vem_marcado(self):
        html = self.ver('/avaliar/1?disciplina_id=10&semestre=2026-1')
        self.assertRegex(html, r'id="semestre-2026-1" value="2026-1"\s+checked')

    def test_avalia_o_semestre_escolhido(self):
        self.assertEqual(self.postar({**NOTAS, 'semestre': '2026-1'}).status_code, 303)
        self.assertEqual(self.semestres(), [(2026, 1)])

    def test_mesmo_par_em_outro_semestre(self):
        self.postar({**NOTAS, 'semestre': '2026-1'})
        self.assertEqual(self.postar({**NOTAS, 'semestre': '2026-2'}).status_code, 303)
        self.assertEqual(self.semestres(), [(2026, 1), (2026, 2)])

    def test_semestre_ja_avaliado_fica_desabilitado_e_e_recusado(self):
        self.postar({**NOTAS, 'semestre': '2026-2'})
        html = self.ver('/avaliar/1?disciplina_id=10')
        self.assertRegex(html, r'id="semestre-2026-2" value="2026-2"\s+disabled')
        self.assertIn('já avaliada', html)
        # A próxima livre é pré-selecionada
        self.assertRegex(html, r'id="semestre-2026-1" value="2026-1"\s+checked')
        resposta = self.postar({**NOTAS, 'semestre': '2026-2'})
        self.assertEqual(resposta.status_code, 409)
        self.assertIn('já avaliou este professor nesta disciplina em 2026/2',
                      resposta.get_data(as_text=True))
        self.assertEqual(self.semestres(), [(2026, 2)])

    def test_semestre_sem_turma_ou_ilegivel(self):
        for valor in ('2025-1', 'abc', '', '2026-2-1'):
            with self.subTest(valor=valor):
                resposta = self.postar({**NOTAS, 'semestre': valor})
                self.assertEqual(resposta.status_code, 400)
                self.assertIn('id="erro-semestre"', resposta.get_data(as_text=True))
        self.assertEqual(self.semestres(), [])

    def test_todas_as_turmas_avaliadas(self):
        self.postar({**NOTAS, 'semestre': '2026-1'})
        self.postar({**NOTAS, 'semestre': '2026-2'})
        html = self.ver('/avaliar/1?disciplina_id=10')
        self.assertIn('em todas as turmas desta disciplina', html)
        self.assertNotIn('id="formAvaliacao"', html)

    def test_cliente_sem_o_campo_usa_a_mais_recente(self):
        resposta = self.postar(NOTAS, accept='application/json')
        self.assertEqual(resposta.status_code, 303)
        self.assertEqual(self.semestres(), [(2026, 2)])
        resposta = self.postar(NOTAS, accept='application/json')
        self.assertEqual(resposta.status_code, 409)
        self.assertIn('semestre', resposta.get_json()['erros'])

    def test_edicao_mostra_o_semestre_e_nao_o_troca(self):
        self.postar({**NOTAS, 'semestre': '2026-1'})
        avaliacao_id = self.cliente.tabelas['avaliacoes'][0]['id']
        html = self.ver(f'/avaliacoes/{avaliacao_id}/editar')
        self.assertIn('Turma de 2026/1', html)
        self.assertNotIn('name="semestre"', html)


class TestFiltroDeSemestreNasMedias(BaseWeb):
    def setUp(self):
        super().setUp()
        self.postar({**NOTAS, 'didatica': '2', 'semestre': '2026-1'})
        self.postar({**NOTAS, 'didatica': '5', 'semestre': '2026-2'})

    def medias(self, caminho):
        html = self.ver(caminho)
        inicio = html.index('<section class="medias"')
        return html[inicio:html.index('</section>', inicio)]

    def test_padrao_e_a_media_de_todos_os_semestres(self):
        secao = self.medias('/professores/1?disciplina_id=10')
        self.assertIn('todos os semestres · 2 avaliações', secao)
        self.assertIn('3,5 / 5', secao)
        ativo = re.search(r'<a class="filter active"[^>]*>\s*([^<]+?)\s*</a>', secao)
        self.assertEqual(ativo.group(1), 'Todos')

    def test_filtra_um_semestre(self):
        secao = self.medias('/professores/1?disciplina_id=10&semestre=2026-1')
        self.assertIn('2026/1 · 1 avaliação', secao)
        self.assertIn('2 / 5', secao)
        self.assertIn('semestre=2026-2', secao)

    def test_topo_do_perfil_continua_com_todas(self):
        html = self.ver('/professores/1?disciplina_id=10&semestre=2026-1')
        self.assertIn('2 avaliações</div>', html)

    def test_semestre_invalido_vira_todos(self):
        for valor in ('2019-1', 'x'):
            with self.subTest(valor=valor):
                self.assertIn('todos os semestres',
                              self.medias(f'/professores/1?disciplina_id=10&semestre={valor}'))

    def test_semestre_sem_avaliacoes(self):
        self.cliente.tabelas['avaliacoes'][:] = [a for a in self.cliente.tabelas['avaliacoes']
                                                 if a['periodo'] == 2]
        secao = self.medias('/professores/1?disciplina_id=10&semestre=2026-1')
        self.assertIn('na turma de 2026/1', secao)

    def test_avaliar_leva_o_semestre_filtrado(self):
        html = self.ver('/professores/1?disciplina_id=10&semestre=2026-1')
        self.assertRegex(html, r'href="/avaliar/1\?[^"]*semestre=2026-1')

    def test_sem_chips_quando_ha_um_so_semestre(self):
        self.assertNotIn('semestre-filtro', self.medias('/professores/2?disciplina_id=20'))

    def test_grafico_reflete_os_semestres_cursados(self):
        html = self.ver('/professores/1')
        self.assertIn('<svg class="grafico-evolucao"', html)
        self.assertIn('em 2026/1 para', html)


if __name__ == '__main__':
    unittest.main()
