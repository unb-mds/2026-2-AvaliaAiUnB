"""Template da lista de Consulta: dificuldade por disciplina, botão Comentários e paginação (issue #201)."""
import re
import unittest
from html.parser import HTMLParser
from urllib.parse import unquote

from flask import render_template

from app import create_app
from app.controllers import professor_controller as controller
from tests.fake_supabase import ClienteFalso
from tests.test_dificuldade_consulta import avaliacao


class BaseLista(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                               'SUPABASE_CLIENT': self.cliente})
        self.web = self.app.test_client()

    def avaliar(self, professor_id, disciplina_id, *dificuldades):
        tabela = self.cliente.tabelas['avaliacoes']
        for d in dificuldades:
            tabela.append({**avaliacao(professor_id, disciplina_id, d), 'id': len(tabela) + 1})

    def lista(self, caminho='/professores'):
        return self.web.get(caminho).get_data(as_text=True)

    @staticmethod
    def cartao(html, nome):
        """HTML do cartão (<li class="card ...">) do professor."""
        cartoes = re.findall(r'<li class="card card-interativo">.*?\n            </li>', html, re.S)
        return next(c for c in cartoes if nome in c)

    @staticmethod
    def itens(cartao):
        return re.findall(r'<li class="disciplina-item">.*?</li>', cartao, re.S)


class TestDificuldadeNoCartao(BaseLista):
    def test_disciplina_com_dificuldade_mostra_barra_compacta_texto_e_quantidade(self):
        self.avaliar(1, 10, 2, 2, 3, 2, 2)       # 11/5 = 2,2
        item = self.itens(self.cartao(self.lista(), 'JOSÉ ÁVILA'))[0]

        self.assertIn('CÁLCULO 1 — FGA0001', item)
        self.assertIn('barra-hp-compacta', item)
        self.assertIn('barra-hp-cheia preenche-44 nivel-2', item)
        # decorativa: o texto ao lado já diz o valor, então o leitor de tela não repete
        self.assertIn('class="barra-hp-trilho" aria-hidden="true"', item)
        self.assertNotIn('role="img"', item)
        self.assertNotIn('aria-label', item)
        self.assertIn('Dificuldade 2,2/5', item)
        self.assertIn('5 avaliações', item)
        self.assertNotIn('barra-hp-escala', item)

    def test_singular(self):
        self.avaliar(2, 20, 4)
        item = self.itens(self.cartao(self.lista(), 'MARIA LIMA'))[0]

        self.assertIn('Dificuldade 4,0/5', item)
        self.assertIn('1 avaliação<', item)
        self.assertNotIn('1 avaliações', item)

    def test_sem_avaliacoes_mostra_so_a_mensagem(self):
        item = self.itens(self.cartao(self.lista(), 'JOSÉ ÁVILA'))[0]

        self.assertIn('Sem avaliações ainda', item)
        self.assertNotIn('barra-hp', item)
        self.assertNotIn('Dificuldade', item)
        self.assertNotRegex(item, r'\d+ avalia')

    def test_professor_sem_disciplinas_continua_com_o_aviso(self):
        cartao = self.cartao(self.lista(), 'SEM TURMA')

        self.assertIn('Ainda não há disciplinas cadastradas', cartao)
        self.assertEqual(self.itens(cartao), [])

    def test_duas_disciplinas_tem_valores_independentes(self):
        self.cliente.tabelas['vw_professor_disciplina'].append(
            {'professor_id': 1, 'disciplina_id': 11, 'codigo_disciplina': 'FGA0003',
             'disciplina': 'ÁLGEBRA', 'ano': 2026, 'periodo': 1})
        self.avaliar(1, 10, 1, 2)                # 1,5 em 2 avaliações
        self.avaliar(1, 11, 5)                   # 5,0 em 1 avaliação
        calculo, algebra = self.itens(self.cartao(self.lista(), 'JOSÉ ÁVILA'))

        self.assertIn('Dificuldade 1,5/5', calculo)
        self.assertIn('2 avaliações', calculo)
        self.assertNotIn('5,0', calculo)
        self.assertIn('Dificuldade 5,0/5', algebra)
        self.assertIn('1 avaliação<', algebra)
        self.assertNotIn('1,5', algebra)

    def test_cabecalho_do_cartao_nao_muda(self):
        self.avaliar(1, 10, 2, 3)
        cartao = self.cartao(self.lista(), 'JOSÉ ÁVILA')

        self.assertIn('<p class="contagem">2 avaliações</p>', cartao)
        self.assertIn('média geral', cartao)
        self.assertIn('estrelas-cheias', cartao)


class TestAvaliacoesSemDificuldade(BaseLista):
    """Estado que o template precisa tratar mesmo que o backend de hoje não o produza."""

    def renderizar(self, dados):
        with self.app.test_request_context('/professores'):
            catalogo = controller.catalogo()
            paginacao = controller.paginar_catalogo(catalogo, None)
            dificuldades = {1: {10: dados}}
            return render_template('lista_professores.html', catalogo=catalogo,
                                   paginacao=paginacao, dificuldades=dificuldades,
                                   disciplinas_cartao=controller.organizar_disciplinas(
                                       paginacao['itens'], dificuldades),
                                   filtros={
                                       'nome': '', 'disciplina': '', 'departamento': '', 'q': ''},
                                   usuario=None)

    def test_so_quantidade_sem_barra_nem_numero(self):
        html = self.renderizar({'valor': None, 'texto_dificuldade': None, 'quantidade': 3,
                                'texto_avaliacoes': '3 avaliações'})
        item = self.itens(self.cartao(html, 'JOSÉ ÁVILA'))[0]

        self.assertIn('3 avaliações', item)
        self.assertNotIn('barra-hp', item)
        self.assertNotIn('Dificuldade', item)
        self.assertNotIn('Sem avaliações ainda', item)


class TestBotaoComentarios(BaseLista):
    def test_link_para_o_perfil_com_next_e_ancora(self):
        html = self.lista('/professores?nome=jose')
        botao = re.search(r'<a class="btn ghost" href="([^"]+)" '
                          r'aria-label="Ver comentários de JOSÉ ÁVILA">Comentários</a>', html)

        self.assertIsNotNone(botao)
        href = botao.group(1)
        self.assertTrue(href.startswith('/professores/1?'))
        self.assertEqual(unquote(href), '/professores/1?next=/professores?nome=jose#comentarios')
        self.assertTrue(href.endswith('#comentarios'))

    def test_fica_na_linha_de_acoes_com_os_outros_botoes(self):
        acoes = re.search(r'<div class="professor-acoes">(.*?)</div>',
                          self.cartao(self.lista(), 'JOSÉ ÁVILA'), re.S).group(1)

        self.assertLess(acoes.index('>Avaliar<'), acoes.index('>Comentários<'))
        self.assertLess(acoes.index('>Comentários<'), acoes.index('Comparar este professor'))

    def test_professor_sem_disciplinas_tambem_tem_o_botao(self):
        self.assertIn('Ver comentários de SEM TURMA', self.lista())


class TestPaginacao(BaseLista):
    def setUp(self):
        super().setUp()
        self.cliente.tabelas['professores'] = [
            {'id': i, 'nome': f'PROFESSOR {i:03d}', 'departamento': 'FCTE'} for i in range(1, 251)]
        self.cliente.tabelas['vw_professor_disciplina'] = []

    def nomes(self, html):
        return re.findall(r'PROFESSOR (\d{3})</a></h2>', html)

    def test_primeira_pagina(self):
        html = self.lista()

        nomes = self.nomes(html)
        self.assertEqual((nomes[0], nomes[-1], len(nomes)), ('001', '100', 100))
        self.assertIn('Mostrando 1–100 de 250 professores.', html)
        self.assertIn('Página 1 de 3', html)
        self.assertIn('<span class="botao botao-secundario" aria-disabled="true">Anterior</span>', html)
        self.assertIn('rel="next"', html)

    def test_ultima_pagina_tem_o_resto(self):
        html = self.lista('/professores?pagina=3')

        nomes = self.nomes(html)
        self.assertEqual((nomes[0], nomes[-1], len(nomes)), ('201', '250', 50))
        self.assertIn('Mostrando 201–250 de 250 professores.', html)
        self.assertIn('rel="prev"', html)
        self.assertIn('<span class="botao botao-secundario" aria-disabled="true">Próxima</span>', html)

    def test_pagina_invalida_ou_fora_do_intervalo(self):
        self.assertEqual(self.nomes(self.lista('/professores?pagina=abc'))[0], '001')
        self.assertEqual(self.nomes(self.lista('/professores?pagina=0'))[0], '001')
        self.assertEqual(self.nomes(self.lista('/professores?pagina=99'))[0], '201')

    def test_pagina_unica_nao_mostra_navegacao(self):
        self.cliente.tabelas['professores'] = self.cliente.tabelas['professores'][:5]
        self.app.extensions['repositorios'].professores.invalidar_cache()
        html = self.lista()

        self.assertNotIn('Paginação', html)
        self.assertNotIn('Mostrando', html)

    def test_links_de_paginacao_preservam_filtros(self):
        html = self.lista('/professores?departamento=FCTE&pagina=2')

        proxima = re.search(r'<a [^>]*rel="next" href="([^"]+)"', html).group(1)
        anterior = re.search(r'<a [^>]*rel="prev" href="([^"]+)"', html).group(1)
        self.assertEqual(sorted(p for p in proxima.replace('&amp;', '&').split('?')[1].split('&') if not p.endswith('=')),
                         ['departamento=FCTE', 'pagina=3'])
        self.assertEqual(sorted(p for p in anterior.replace('&amp;', '&').split('?')[1].split('&') if not p.endswith('=')),
                         ['departamento=FCTE', 'pagina=1'])


class FormulariosConsulta(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.formularios = []
        self.atual = None
        self.opcoes = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'form':
            self.atual = {'classe': attrs.get('class', ''), 'ocultos': {}}
            self.formularios.append(self.atual)
        elif tag == 'input' and self.atual is not None and attrs.get('type') == 'hidden':
            self.atual['ocultos'][attrs['name']] = attrs.get('value', '')
        elif tag == 'option':
            self.opcoes.append(attrs)

    def handle_endtag(self, tag):
        if tag == 'form':
            self.atual = None


class TestFiltroDepartamentoConsulta(BaseLista):
    def setUp(self):
        super().setUp()
        self.cliente.tabelas['professores'].extend([
            {'id': 4, 'nome': 'ANA LIMA', 'departamento': 'Instituto de Artes'},
            {'id': 5, 'nome': 'PAULA SOUZA', 'departamento': 'Psicologia'},
        ])

    def test_opcoes_vem_do_catalogo_completo_mesmo_com_filtro_aplicado(self):
        html = self.lista('/professores?departamento=FCTE')
        parser = FormulariosConsulta(html)
        self.assertEqual([o['value'] for o in parser.opcoes],
                         ['', 'FCTE', 'Instituto de Artes', 'Psicologia'])
        self.assertEqual([o['value'] for o in parser.opcoes if 'selected' in o], ['FCTE'])
        self.assertIn('JOSÉ ÁVILA', html)
        self.assertNotIn('ANA LIMA', html)
        self.assertNotIn('aria-label="Áreas de busca"', html)

    def test_busca_e_departamento_combinam_e_sao_preservados_nos_dois_formularios(self):
        html = self.lista('/professores?q=lima&departamento=fcte&pagina=3')
        parser = FormulariosConsulta(html)
        busca = next(f for f in parser.formularios if 'busca-unificada' in f['classe'])
        filtro = next(f for f in parser.formularios if 'filtro-departamento-consulta' in f['classe'])
        self.assertEqual(busca['ocultos'], {'departamento': 'FCTE'})
        self.assertEqual(filtro['ocultos'], {'q': 'lima'})
        self.assertNotIn('pagina', busca['ocultos'])
        self.assertNotIn('pagina', filtro['ocultos'])
        self.assertIn('MARIA LIMA', html)
        self.assertNotIn('ANA LIMA', html)
        self.assertNotIn('JOSÉ ÁVILA', html)

    def test_todos_departamentos_remove_so_departamento_e_mantem_busca(self):
        html = self.lista('/professores?q=lima&departamento=FCTE')
        filtro = next(f for f in FormulariosConsulta(html).formularios
                      if 'filtro-departamento-consulta' in f['classe'])
        resposta = self.web.get('/professores', query_string={**filtro['ocultos'], 'departamento': ''})
        html = resposta.get_data(as_text=True)
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('MARIA LIMA', html)
        self.assertIn('ANA LIMA', html)
        self.assertNotIn('JOSÉ ÁVILA', html)

    def test_departamento_desconhecido_nao_mostra_catalogo_inteiro(self):
        html = self.lista('/professores?departamento=Inexistente')
        self.assertIn('Departamento não encontrado: Inexistente', html)
        self.assertIn('Nenhum professor encontrado', html)
        self.assertNotIn('JOSÉ ÁVILA', html)

    def test_lista_vazia_mantem_opcao_todos(self):
        self.cliente.tabelas['professores'] = []
        html = self.lista()
        self.assertEqual([o['value'] for o in FormulariosConsulta(html).opcoes], [''])
        self.assertIn('Todos os departamentos', html)


if __name__ == '__main__':
    unittest.main()
