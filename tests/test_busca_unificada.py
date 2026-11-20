"""Busca unificada (#220): sugestões em JSON e filtro `q` da Consulta."""
import re
import unittest
from pathlib import Path

from app import create_app
from app.repositorio import MAXIMO_SUGESTOES
from tests.fake_supabase import ClienteFalso


class TestBuscaUnificada(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.cliente.tabelas['professores'].append(
            {'id': 4, 'nome': 'ANA CALDAS', 'departamento': 'DEPARTAMENTO DE MATEMÁTICA'})
        self.cliente.tabelas['vw_professor_disciplina'].append(
            {'professor_id': 4, 'disciplina_id': 30, 'codigo_disciplina': 'MAT0025',
             'disciplina': 'CÁLCULO 2', 'ano': 2026, 'periodo': 1})
        self.web = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                               'SUPABASE_CLIENT': self.cliente}).test_client()

    def sugestoes(self, consulta):
        resposta = self.web.get(f'/busca/sugestoes?{consulta}')
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.mimetype, 'application/json')
        return resposta.get_json()['sugestoes']

    def test_sugere_professor_disciplina_e_departamento_com_o_tipo(self):
        tipos = {(s['tipo'], s['tipo_rotulo']) for s in self.sugestoes('q=ca')}
        self.assertIn(('professor', 'Professor'), tipos)      # ANA CALDAS
        self.assertIn(('disciplina', 'Disciplina'), tipos)    # CÁLCULO 1 e 2
        self.assertIn(('departamento', 'Departamento'),
                      {(s['tipo'], s['tipo_rotulo']) for s in self.sugestoes('q=fct')})

    def test_ignora_acentos_caixa_e_espacos(self):
        for termo in ('calculo%201', 'CÁLCULO1', '%20c%C3%A1lculo%201%20'):
            textos = [s['texto'] for s in self.sugestoes(f'q={termo}')]
            self.assertEqual(textos, ['CÁLCULO 1'], termo)
        self.assertEqual([s['texto'] for s in self.sugestoes('q=jose%20avila')], ['JOSÉ ÁVILA'])

    def test_disciplina_casa_pelo_codigo_e_mostra_o_codigo(self):
        sugestao, = self.sugestoes('q=fga0002')
        self.assertEqual((sugestao['tipo'], sugestao['texto'], sugestao['detalhe']),
                         ('disciplina', 'FÍSICA 1', 'FGA0002'))

    def test_quem_comeca_com_o_termo_vem_primeiro(self):
        textos = [s['texto'] for s in self.sugestoes('q=ma')]
        # MARIA LIMA e MAT0025 começam com "ma"; o departamento só tem "MATEMÁTICA" no meio.
        self.assertLess(textos.index('MARIA LIMA'), textos.index('DEPARTAMENTO DE MATEMÁTICA'))
        self.assertLess(textos.index('CÁLCULO 2'), textos.index('DEPARTAMENTO DE MATEMÁTICA'))

    def test_termo_curto_ou_vazio_nao_sugere(self):
        self.assertEqual(self.sugestoes('q='), [])
        self.assertEqual(self.sugestoes('q=a'), [])
        self.assertEqual(self.sugestoes(''), [])

    def test_respeita_o_limite_de_resultados(self):
        for i in range(30):
            self.cliente.tabelas['professores'].append(
                {'id': 100 + i, 'nome': f'PROFESSOR {i}', 'departamento': 'FCTE'})
        self.assertEqual(len(self.sugestoes('q=professor')), 8)
        self.assertEqual(len(self.sugestoes('q=professor&limite=3')), 3)
        self.assertEqual(len(self.sugestoes('q=professor&limite=999')), MAXIMO_SUGESTOES)
        self.assertEqual(len(self.sugestoes('q=professor&limite=0')), 1)
        self.assertEqual(len(self.sugestoes('q=professor&limite=abc')), 8)

    def test_urls_da_consulta(self):
        por_tipo = {s['tipo']: s['url'] for s in self.sugestoes('q=fcte')}
        self.assertEqual(por_tipo['departamento'], '/professores?departamento=FCTE')
        urls = {s['texto']: s['url'] for s in self.sugestoes('q=jose')}
        self.assertEqual(urls['JOSÉ ÁVILA'], '/professores/1')
        urls = {s['texto']: s['url'] for s in self.sugestoes('q=fisica')}
        self.assertEqual(urls['FÍSICA 1'], '/professores?disciplina=FGA0002')

    def test_contexto_da_comparacao_leva_para_a_comparacao_sem_departamento(self):
        sugestoes = self.sugestoes('q=ca&contexto=comparacao')
        self.assertTrue(sugestoes)
        self.assertNotIn('departamento', {s['tipo'] for s in sugestoes})
        urls = {s['texto']: s['url'] for s in sugestoes}
        self.assertEqual(urls['ANA CALDAS'], '/comparar?professor_1=4')
        self.assertEqual(urls['CÁLCULO 1'], '/comparar?disciplina_id=10')
        self.assertEqual(self.sugestoes('q=fcte&contexto=comparacao'), [])

    def test_contexto_desconhecido_usa_a_consulta(self):
        self.assertIn('departamento', {s['tipo'] for s in self.sugestoes('q=fcte&contexto=xyz')})

    def test_consulta_filtra_pelo_termo_unificado(self):
        def nomes(q):
            html = self.web.get(f'/professores?q={q}').get_data(as_text=True)
            return {n for n in ('JOSÉ ÁVILA', 'MARIA LIMA', 'SEM TURMA', 'ANA CALDAS') if n in html}
        self.assertEqual(nomes('maria'), {'MARIA LIMA'})                  # professor
        self.assertEqual(nomes('calculo'), {'JOSÉ ÁVILA', 'ANA CALDAS'})  # disciplina
        self.assertEqual(nomes('FGA0002'), {'MARIA LIMA'})                # código
        self.assertEqual(nomes('matematica'), {'ANA CALDAS'})             # departamento
        self.assertIn('Nenhum professor encontrado', self.web.get('/professores?q=zzz').text)

    def test_paginacao_preserva_o_termo(self):
        for i in range(120):
            self.cliente.tabelas['professores'].append(
                {'id': 100 + i, 'nome': f'PROFESSOR {i}', 'departamento': 'FCTE'})
        self.assertIn('q=professor', self.web.get('/professores?q=professor').text)


class TestCampoBuscaUnificada(unittest.TestCase):
    """O campo da Consulta funciona sem JavaScript e o script respeita a CSP."""

    def setUp(self):
        self.web = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                               'SUPABASE_CLIENT': ClienteFalso()}).test_client()

    def formulario(self, caminho):
        html = self.web.get(caminho).get_data(as_text=True)
        achado = re.search(r'<form\b[^>]*class="[^"]*\bbusca-unificada\b[^"]*"[^>]*>(.*?)</form>', html, re.S)
        self.assertIsNotNone(achado, f'{caminho} não tem o formulário da busca unificada')
        return html, achado.group(0)

    def test_consulta_tem_formulario_get_com_rotulo(self):
        html, formulario = self.formulario('/professores?q=Ávila')
        self.assertIn('method="get"', formulario)
        self.assertIn('action="/professores"', formulario)
        self.assertRegex(formulario, r'<label\b[^>]*for="busca-unificada"')
        self.assertRegex(formulario, r'<input\b[^>]*id="busca-unificada"[^>]*name="q"')
        self.assertIn('value="Ávila"', formulario)
        self.assertIn('data-sugestoes="/busca/sugestoes"', formulario)
        self.assertIn('<button type="submit"', formulario)
        self.assertIn('src="/static/campo-busca.js"', html)

    def test_comparacao_tem_o_campo_no_contexto_da_comparacao(self):
        for caminho in ('/comparar', '/comparar?professor_1=1&professor_2=2'):
            html, formulario = self.formulario(caminho)
            self.assertIn('action="/comparar"', formulario)
            self.assertIn('data-contexto="comparacao"', formulario)
            self.assertRegex(formulario, r'<label\b[^>]*for="busca-unificada"')
            self.assertRegex(formulario, r'<input\b[^>]*id="busca-unificada"[^>]*name="busca"')
            self.assertIn('src="/static/campo-busca.js"', html)

    def test_comparacao_sem_javascript_lista_resultados_com_o_tipo(self):
        html = self.web.get('/comparar?busca=calculo').get_data(as_text=True)
        self.assertIn('Resultados para “calculo”', html)
        self.assertIn('href="/comparar?disciplina_id=10"', html)
        self.assertIn('>Disciplina</span>', html)
        html = self.web.get('/comparar?busca=maria').get_data(as_text=True)
        self.assertIn('href="/comparar?professor_1=2"', html)
        self.assertIn('>Professor</span>', html)
        html = self.web.get('/comparar?busca=zzz').get_data(as_text=True)
        self.assertIn('Nenhum professor ou disciplina encontrado', html)
        self.assertNotIn('Resultados para', self.web.get('/comparar').get_data(as_text=True))

    def test_resultados_escapam_o_termo(self):
        html = self.web.get('/comparar?busca=%3Cscript%3Ealert(1)%3C/script%3E').text
        self.assertNotIn('<script>alert(1)', html)
        self.assertIn('&lt;script&gt;', html)

    def test_consulta_tem_um_unico_campo_de_busca(self):
        html = self.web.get('/professores').get_data(as_text=True)
        self.assertEqual(len(re.findall(r'<input\b[^>]*type="search"', html)), 1)
        self.assertNotRegex(html, r'<input\b[^>]*name="departamento"[^>]*type="(?:text|search)"')
        self.assertIn('<select id="departamento-consulta" name="departamento">', html)
        self.assertNotIn('filtros-ativos', html)

    def test_filtro_vindo_de_sugestao_aparece_com_limpar(self):
        html = self.web.get('/professores?departamento=FCTE').get_data(as_text=True)
        self.assertIn('Filtrando por departamento “FCTE”.', html)
        self.assertIn('href="/professores">Limpar filtros</a>', html)
        html = self.web.get('/professores?disciplina=FGA0001&q=jose').get_data(as_text=True)
        self.assertIn('Filtrando por disciplina “FGA0001” e pela busca “jose”.', html)

    def test_sem_javascript_inline(self):
        for caminho in ('/professores', '/comparar', '/comparar?busca=calculo'):
            resposta = self.web.get(caminho)
            html = resposta.get_data(as_text=True)
            for script in re.findall(r'<script\b[^>]*>(.*?)</script>', html, re.S):
                self.assertEqual(script.strip(), '', f'{caminho}: script inline bloqueado pela CSP')
            self.assertNotRegex(html, r'\son[a-z]+="', f'{caminho}: atributo on* bloqueado pela CSP')
            csp = resposta.headers['Content-Security-Policy']
            self.assertIn("script-src 'self'", csp)
            self.assertIn("connect-src 'self'", csp)

    def test_script_segue_o_padrao_combobox(self):
        script = (Path(__file__).resolve().parent.parent / 'app' / 'static'
                  / 'campo-busca.js').read_text(encoding='utf-8')
        for trecho in ("'combobox'", "'listbox'", "'option'", 'aria-expanded',
                       'aria-activedescendant', 'aria-controls', "'status'",
                       'ArrowDown', 'ArrowUp', 'Escape', 'tipo_rotulo'):
            self.assertIn(trecho, script)
        self.assertNotIn('innerHTML', script, 'Sugestões devem ser inseridas como texto')


if __name__ == '__main__':
    unittest.main()
