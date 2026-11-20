"""Seleção de professores na comparação livre (#239): busca por nome ou disciplina
(/busca/professores) e filtro por departamento que encurta a lista."""
import unittest

from app import create_app
from app.controllers.professor_controller import resumir_disciplinas
from app.repositorio import MAXIMO_SUGESTOES
from tests.fake_supabase import ClienteFalso


class TestSelecaoProfessores(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.cliente.tabelas['professores'].append(
            {'id': 4, 'nome': 'ANA CALDAS', 'departamento': 'DEPARTAMENTO DE MATEMÁTICA'})
        self.cliente.tabelas['vw_professor_disciplina'].extend([
            {'professor_id': 4, 'disciplina_id': 30, 'codigo_disciplina': 'MAT0025',
             'disciplina': 'CÁLCULO 2', 'ano': 2026, 'periodo': 2},
            {'professor_id': 4, 'disciplina_id': 31, 'codigo_disciplina': 'MAT0031',
             'disciplina': 'ÁLGEBRA LINEAR', 'ano': 2026, 'periodo': 2},
        ])
        self.web = create_app({'TESTING': True, 'SECRET_KEY': 'teste-selecao-professores',
                               'SUPABASE_CLIENT': self.cliente}).test_client()

    def buscar(self, consulta):
        resposta = self.web.get(f'/busca/professores?{consulta}')
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.mimetype, 'application/json')
        return resposta.get_json()['professores']

    # ------------------------------------------------------------- /busca/professores

    def test_busca_pelo_nome_traz_id_departamento_e_disciplinas(self):
        professor, = self.buscar('q=jose%20avila')
        self.assertEqual(professor, {'id': 1, 'texto': 'JOSÉ ÁVILA', 'detalhe': 'FCTE',
                                     'disciplinas': 'CÁLCULO 1 (FGA0001)',
                                     'casou_disciplina': False})

    def test_busca_pela_disciplina_lista_quem_a_ministra(self):
        por_nome = self.buscar('q=calculo%202')
        self.assertEqual([p['texto'] for p in por_nome], ['ANA CALDAS'])
        self.assertTrue(por_nome[0]['casou_disciplina'])
        # A disciplina que casou aparece primeiro no resumo.
        self.assertTrue(por_nome[0]['disciplinas'].startswith('CÁLCULO 2 (MAT0025)'))
        self.assertEqual([p['id'] for p in self.buscar('q=fga0002')], [2])

    def test_so_traz_professores(self):
        # "fcte" é departamento: a busca de seleção não sugere departamentos nem disciplinas.
        self.assertEqual(self.buscar('q=fcte'), [])

    def test_quem_casa_pelo_nome_vem_antes_de_quem_casa_pela_disciplina(self):
        self.cliente.tabelas['professores'].append(
            {'id': 5, 'nome': 'CALEB SOUZA', 'departamento': 'FCTE'})
        textos = [p['texto'] for p in self.buscar('q=cal')]
        # CALEB e ANA CALDAS casam pelo nome; JOSÉ só pela disciplina CÁLCULO 1.
        self.assertEqual(textos, ['CALEB SOUZA', 'ANA CALDAS', 'JOSÉ ÁVILA'])

    def test_filtra_por_departamento(self):
        # Os dois casam pela disciplina; desempate pelo nome (ANA antes de JOSÉ).
        self.assertEqual([p['id'] for p in self.buscar('q=calculo')], [4, 1])
        self.assertEqual(
            [p['id'] for p in self.buscar('q=calculo&departamento=departamento%20de%20matematica')],
            [4])

    def test_termo_curto_e_limite(self):
        self.assertEqual(self.buscar('q=a'), [])
        self.assertEqual(self.buscar(''), [])
        for i in range(30):
            self.cliente.tabelas['professores'].append(
                {'id': 100 + i, 'nome': f'PROFESSOR {i}', 'departamento': 'FCTE'})
        self.assertEqual(len(self.buscar('q=professor')), 8)
        self.assertEqual(len(self.buscar('q=professor&limite=3')), 3)
        self.assertEqual(len(self.buscar('q=professor&limite=999')), MAXIMO_SUGESTOES)

    def test_resumo_das_disciplinas(self):
        disciplinas = [{'nome': f'DISC {i}', 'codigo': f'C{i}'} for i in range(5)]
        self.assertEqual(resumir_disciplinas(disciplinas),
                         'DISC 0 (C0), DISC 1 (C1), DISC 2 (C2) +2')
        self.assertEqual(resumir_disciplinas([{'nome': 'SEM CÓDIGO', 'codigo': ''}]), 'SEM CÓDIGO')
        self.assertEqual(resumir_disciplinas([]), '')

    # ------------------------------------------------- filtro por departamento (sem JS)

    def opcoes_de_professor(self, html):
        """ids que aparecem como <option> nos campos de professor."""
        inicio = html.index('class="selecao-comparacao"')
        trecho = html[inicio:html.index('class="acoes-comparacao"')]
        return {i for i in (1, 2, 3, 4) if f'<option value="{i}"' in trecho}

    def test_modo_livre_lista_todos_e_oferece_os_departamentos(self):
        html = self.web.get('/comparar?modo=livre').text
        self.assertEqual(self.opcoes_de_professor(html), {1, 2, 3, 4})
        self.assertIn('<option value="DEPARTAMENTO DE MATEMÁTICA">', html)
        self.assertIn('<option value="FCTE">', html)

    def test_filtro_encurta_a_lista_e_mantem_os_ja_escolhidos(self):
        filtrado = self.web.get('/comparar?modo=livre&departamento=FCTE&filtrar=1').text
        self.assertEqual(self.opcoes_de_professor(filtrado), {1, 2, 3})
        self.assertIn('<option value="FCTE" selected>', filtrado)

        com_escolha = self.web.get(
            '/comparar?modo=livre&departamento=fcte&professor=4&professor=&filtrar=1').text
        self.assertEqual(self.opcoes_de_professor(com_escolha), {1, 2, 3, 4})
        self.assertIn('value="4" selected', com_escolha)

    def test_departamento_desconhecido_e_ignorado(self):
        resposta = self.web.get('/comparar?modo=livre&departamento=INEXISTENTE')
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(self.opcoes_de_professor(resposta.text), {1, 2, 3, 4})

    # ------------------------------------------------------- campo digitável (JS)

    def test_campos_de_professor_apontam_para_a_busca(self):
        html = self.web.get('/comparar?modo=livre').text
        self.assertEqual(html.count('class="campo campo-professor compare-card" data-busca="/busca/professores"'), 2)
        self.assertIn('data-placeholder="Nome do professor ou de uma disciplina"', html)
        self.assertIn('src="/static/campo-busca.js"', html)
        # Filtrar, adicionar e remover não exigem os campos preenchidos.
        self.assertIn('name="filtrar" value="1" formnovalidate', html)
        self.assertIn('name="adicionar" value="1" formnovalidate', html)

    def test_escolhido_mostra_departamento_e_disciplinas(self):
        html = self.web.get('/comparar?modo=livre&professor=4&professor=').text
        self.assertIn('id="professor-1-detalhe">DEPARTAMENTO DE MATEMÁTICA · '
                      'ÁLGEBRA LINEAR (MAT0031), CÁLCULO 2 (MAT0025)</p>', html)
        self.assertIn('id="professor-2-detalhe"></p>', html)
        self.assertIn('aria-describedby="professor-1-detalhe"', html)

    def test_script_do_campo_de_professor(self):
        from pathlib import Path
        script = (Path(__file__).resolve().parent.parent / 'app' / 'static'
                  / 'campo-busca.js').read_text(encoding='utf-8')
        for trecho in ("'.campo-professor'", 'dados.professores', "'data-busca'",
                       "select[name=\"departamento\"]", 'setCustomValidity', 'Disciplinas: '):
            self.assertIn(trecho, script)
        self.assertNotIn('innerHTML', script)

    def test_compara_com_filtro_ativo(self):
        resposta = self.web.get(
            '/comparar?modo=livre&departamento=FCTE&professor=1&professor=4&comparar=1')
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('<table class="tabela-comparacao">', resposta.text)
        self.assertIn('ANA CALDAS', resposta.text)


if __name__ == '__main__':
    unittest.main()
