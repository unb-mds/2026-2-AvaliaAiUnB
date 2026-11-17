"""Listagem de comentários no perfil do professor (issue #167), com o cliente falso."""
import unittest
from unittest.mock import patch

from app import create_app
from app.repositorio import LIMITE_COMENTARIOS, ComentarioRepository
from tests.fake_supabase import ClienteFalso, entrar_pela_web

ANA, BIA = 'uuid-ana', 'uuid-bia'
EMAIL_ANA, EMAIL_BIA = 'ana@gmail.com', 'bia@gmail.com'
FRASE_LIMITE = 'Mostrando os 50 comentários mais recentes.'
FRASE_VAZIO = 'Ainda não há comentários para este professor.'
AVISO_ERRO = 'Não foi possível carregar os comentários agora.'


class BaseRotas(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        # Professor 1 ministra as disciplinas 10 e 11; o professor 2, só a 20.
        self.cliente.tabelas['vw_professor_disciplina'].append(
            {'professor_id': 1, 'disciplina_id': 11, 'codigo_disciplina': 'FGA0011',
             'disciplina': 'CÁLCULO 2', 'ano': 2026, 'periodo': 1})
        self.cliente.tabelas['perfis'] += [
            {'id': ANA, 'username': 'ana', 'nome_completo': 'Ana Silva', 'email': EMAIL_ANA},
            {'id': BIA, 'username': 'bia', 'nome_completo': 'Bia Souza', 'email': EMAIL_BIA},
        ]
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                               'SUPABASE_CLIENT': self.cliente})
        self.web = self.app.test_client()

    def semear(self, texto, usuario=ANA, professor=1, disciplina=10, **extra):
        tabela = self.cliente.tabelas['comentarios']
        n = len(tabela) + 1
        momento = f'2026-03-01T10:{n // 60:02d}:{n % 60:02d}+00:00'
        tabela.append({'id': n, 'usuario_id': usuario, 'professor_id': professor,
                       'disciplina_id': disciplina, 'texto': texto, 'criado_em': momento,
                       'atualizado_em': momento, 'ocultado_em': None, **extra})

    def perfil(self, query='', professor=1):
        return self.web.get(f'/professores/{professor}{query}', headers={'Accept': 'text/html'})

    def html(self, query='', professor=1):
        resposta = self.perfil(query, professor)
        self.assertEqual(resposta.status_code, 200)
        return resposta.get_data(as_text=True)


class TestListagem(BaseRotas):
    def test_lista_os_comentarios_do_professor_mais_recentes_primeiro(self):
        self.semear('primeiro texto')
        self.semear('segundo texto', usuario=BIA)
        self.semear('terceiro texto')
        self.semear('de outro professor', professor=2, disciplina=20)
        html = self.html()
        self.assertLess(html.index('terceiro texto'), html.index('segundo texto'))
        self.assertLess(html.index('segundo texto'), html.index('primeiro texto'))
        self.assertNotIn('de outro professor', html)
        self.assertIn('<strong>ana</strong>', html)
        self.assertIn('<strong>bia</strong>', html)

    def test_secao_separada_das_notas_com_titulo(self):
        html = self.html()
        self.assertIn('id="comentarios"', html)
        self.assertLess(html.index('Médias Consolidadas'), html.index('id="titulo-comentarios"'))

    def test_mostra_disciplina_data_e_editado(self):
        self.semear('texto original', criado_em='2026-03-05T15:00:00+00:00',
                    atualizado_em='2026-03-05T15:00:00+00:00')
        self.semear('texto mexido', disciplina=11, criado_em='2026-03-06T15:00:00+00:00',
                    atualizado_em='2026-03-07T15:00:00+00:00')
        html = self.html()
        self.assertIn('CÁLCULO 1 — FGA0001', html)
        self.assertIn('05/03/2026', html)
        self.assertIn('06/03/2026', html)
        self.assertEqual(html.count('(editado)'), 1)
        trecho = html[html.index('texto mexido') - 400:html.index('texto mexido')]
        self.assertIn('(editado)', trecho)

    def test_data_usa_o_horario_de_brasilia(self):
        self.semear('quase meia-noite', criado_em='2026-03-06T01:30:00+00:00',
                    atualizado_em='2026-03-06T01:30:00+00:00')
        self.assertIn('05/03/2026', self.html())

    def test_nao_lista_ocultados(self):
        self.semear('visível')
        self.semear('texto oculto', ocultado_em='2026-03-02T00:00:00+00:00')
        html = self.html()
        self.assertIn('visível', html)
        self.assertNotIn('texto oculto', html)

    def test_estado_vazio(self):
        html = self.html()
        self.assertIn(FRASE_VAZIO, html)
        self.assertNotIn(FRASE_LIMITE, html)

    def test_professor_sem_disciplinas_mostra_so_o_estado_vazio(self):
        html = self.html(professor=3)
        self.assertIn(FRASE_VAZIO, html)
        self.assertNotIn('id="comentarios_disciplina"', html)

    def test_quebras_de_linha_sao_preservadas(self):
        self.semear('linha um\nlinha dois\r\nlinha três')
        html = self.html()
        self.assertIn('linha um<br>linha dois<br>linha três', html)

    def test_perfil_funciona_para_quem_esta_logado(self):
        entrar_pela_web(self.web, self.cliente, EMAIL_ANA, 'Ana')
        self.semear('comentário visto logado', usuario=BIA)
        self.assertIn('comentário visto logado', self.html())


class TestFiltro(BaseRotas):
    def setUp(self):
        super().setUp()
        self.semear('texto de cálculo um', disciplina=10)
        self.semear('texto de cálculo dois', disciplina=11)

    def test_padrao_e_todas_as_disciplinas(self):
        html = self.html()
        self.assertIn('<option value="">Todas as disciplinas</option>', html)
        self.assertIn('texto de cálculo um', html)
        self.assertIn('texto de cálculo dois', html)

    def test_filtra_por_disciplina_e_marca_a_opcao(self):
        html = self.html('?comentarios_disciplina=11')
        self.assertIn('texto de cálculo dois', html)
        self.assertNotIn('texto de cálculo um', html)
        self.assertRegex(html, r'<option value="11"\s+selected>')

    def test_disciplina_sem_comentarios_mostra_vazio_do_filtro(self):
        self.cliente.tabelas['comentarios'].clear()
        self.semear('só na dez', disciplina=10)
        html = self.html('?comentarios_disciplina=11')
        self.assertIn('Não há comentários para este professor nesta disciplina.', html)
        self.assertNotIn('só na dez', html)

    def test_filtro_invalido_volta_a_todas_sem_404(self):
        # 20 é uma disciplina real, mas de outro professor.
        for valor in ('', 'abc', '999', '-1', '1.5', '20', '10; DROP', ' '):
            with self.subTest(valor=valor):
                html = self.html(f'?comentarios_disciplina={valor}')
                self.assertIn('texto de cálculo um', html)
                self.assertIn('texto de cálculo dois', html)
                self.assertNotRegex(html, r'<option value="\d+"\s+selected>\s*FÍSICA')

    def test_nao_reutiliza_disciplina_id(self):
        # disciplina_id decide as médias; o filtro de comentários é independente.
        html = self.html('?disciplina_id=11')
        self.assertIn('texto de cálculo um', html)
        self.assertIn('texto de cálculo dois', html)
        html = self.html('?disciplina_id=11&comentarios_disciplina=10')
        self.assertIn('texto de cálculo um', html)
        self.assertNotIn('texto de cálculo dois', html)

    def test_disciplina_id_invalido_continua_dando_404_nas_medias(self):
        self.assertEqual(self.perfil('?disciplina_id=999').status_code, 404)

    def test_formulario_do_filtro_preserva_disciplina_id_e_next(self):
        html = self.html('?disciplina_id=11&next=/professores?nome=jo')
        inicio = html.index('id="comentarios_disciplina"')
        formulario = html[html.rindex('<form', 0, inicio):inicio]
        self.assertIn('method="get"', formulario)
        self.assertIn('name="disciplina_id" value="11"', formulario)
        self.assertIn('name="next" value="/professores?nome=jo"', formulario)

    def test_filtro_de_comentarios_e_preservado_no_formulario_das_medias(self):
        html = self.html('?comentarios_disciplina=11')
        self.assertIn('name="comentarios_disciplina" value="11"', html)
        self.assertNotIn('name="comentarios_disciplina" value=', self.html())


class TestSeguranca(BaseRotas):
    def test_script_aparece_como_texto_escapado(self):
        self.semear('<script>alert(1)</script> <b>negrito</b> & cia')
        html = self.html()
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', html)
        self.assertIn('&lt;b&gt;negrito&lt;/b&gt; &amp; cia', html)
        self.assertNotIn('<script>alert(1)', html)
        self.assertNotIn('<b>negrito', html)

    def test_username_tambem_e_escapado(self):
        self.cliente.tabelas['perfis'][0]['username'] = '<i>ana</i>'
        self.semear('qualquer texto')
        html = self.html()
        self.assertIn('&lt;i&gt;ana&lt;/i&gt;', html)
        self.assertNotIn('<strong><i>', html)

    def test_pagina_nunca_contem_email_nem_usuario_id(self):
        self.semear('texto da ana', usuario=ANA)
        self.semear('texto da bia', usuario=BIA)
        paginas = [self.html()]
        entrar_pela_web(self.web, self.cliente, EMAIL_ANA, 'Ana')
        paginas.append(self.html())
        # A conta logada tem outro id (uuid do login); ele também não pode aparecer.
        id_logada = next(u['id'] for u in self.cliente.auth.usuarios.values()
                         if u['email'] == EMAIL_ANA)
        for html in paginas:
            for segredo in (EMAIL_ANA, EMAIL_BIA, ANA, BIA, 'Ana Silva', 'Bia Souza'):
                self.assertNotIn(segredo, html)
        self.assertNotIn(id_logada, paginas[1])

    def test_sem_safe_no_template(self):
        from pathlib import Path
        modelo = Path('app/templates/perfil_professor.html').read_text(encoding='utf-8')
        self.assertNotIn('|safe', modelo.replace(' ', ''))
        self.assertNotIn('style=', self.html())


class TestLimiteEErro(BaseRotas):
    def test_exatamente_no_limite_nao_mostra_a_frase(self):
        for n in range(LIMITE_COMENTARIOS):
            self.semear(f'comentário número {n}')
        html = self.html()
        self.assertEqual(html.count('class="comentario"'), LIMITE_COMENTARIOS)
        self.assertNotIn(FRASE_LIMITE, html)

    def test_acima_do_limite_mostra_a_frase_e_corta_os_mais_antigos(self):
        for n in range(LIMITE_COMENTARIOS + 1):
            self.semear(f'comentário número {n}.')
        html = self.html()
        self.assertEqual(html.count('class="comentario"'), LIMITE_COMENTARIOS)
        self.assertIn(FRASE_LIMITE, html)
        self.assertIn('comentário número 50.', html)
        self.assertNotIn('comentário número 0.', html)

    def test_erro_na_consulta_mostra_aviso_e_o_perfil_continua(self):
        self.semear('não deve aparecer')
        with patch.object(ComentarioRepository, 'listar_por_professor',
                          side_effect=RuntimeError('banco fora do ar')):
            with self.assertLogs(self.app.logger, level='ERROR') as registro:
                resposta = self.perfil()
        self.assertEqual(resposta.status_code, 200)
        html = resposta.get_data(as_text=True)
        self.assertIn(AVISO_ERRO, html)
        self.assertIn('role="alert"', html)
        self.assertIn('Médias Consolidadas', html)
        self.assertIn('JOSÉ ÁVILA', html)
        self.assertNotIn('não deve aparecer', html)
        self.assertNotIn(FRASE_VAZIO, html)
        self.assertNotIn('banco fora do ar', html)       # o detalhe vai só para o log
        self.assertTrue(any('banco fora do ar' in linha for linha in registro.output))

    def test_sem_erro_o_aviso_nao_aparece(self):
        self.assertNotIn(AVISO_ERRO, self.html())


if __name__ == '__main__':
    unittest.main()
