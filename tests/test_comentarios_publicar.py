"""Publicar comentário no perfil do professor (issue #167), com o cliente falso."""
import re
import unittest
from urllib.parse import parse_qs, urlsplit

from flask_wtf.csrf import generate_csrf

from app import create_app
from app.repositorio import repositorios
from app.validacoes import CRITERIOS
from tests.fake_supabase import ClienteFalso, entrar_pela_web

EMAIL = 'ana@gmail.com'
OUTRO_USUARIO = 'uuid-de-outra-pessoa'
FRASE_PRIMEIRO = 'Escreva o primeiro.'


class BasePublicar(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        # Professor 1 ministra as disciplinas 10 e 11; o professor 2, só a 20; o 3 não tem turma.
        self.cliente.tabelas['vw_professor_disciplina'].append(
            {'professor_id': 1, 'disciplina_id': 11, 'codigo_disciplina': 'FGA0011',
             'disciplina': 'CÁLCULO 2', 'ano': 2026, 'periodo': 1})
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                               'SUPABASE_CLIENT': self.cliente})
        self.app.add_url_rule('/teste/csrf', 'teste_csrf', generate_csrf)
        self.web = self.app.test_client()

    def entrar(self, email=EMAIL, nome='Ana'):
        entrar_pela_web(self.web, self.cliente, email, nome)
        return next(u['id'] for u in self.cliente.auth.usuarios.values() if u['email'] == email)

    def postar(self, dados, professor=1, csrf=True, web=None):
        web = web or self.web
        if csrf:
            dados = {**dados, 'csrf_token': web.get('/teste/csrf').get_data(as_text=True)}
        return web.post(f'/professores/{professor}/comentarios', data=dados,
                        headers={'Accept': 'text/html'})

    def perfil(self, query='', professor=1):
        resposta = self.web.get(f'/professores/{professor}{query}', headers={'Accept': 'text/html'})
        self.assertEqual(resposta.status_code, 200)
        return resposta.get_data(as_text=True)

    def comentarios(self):
        return self.cliente.tabelas['comentarios']


class TestVisitante(BasePublicar):
    def test_visitante_nao_consegue_postar_e_vai_ao_login(self):
        resposta = self.postar({'disciplina_id': '10', 'texto': 'comentário de visitante'})
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(urlsplit(resposta.headers['Location']).path, '/login')
        self.assertEqual(self.comentarios(), [])

    def test_visitante_ve_o_convite_e_nao_ve_o_formulario(self):
        html = self.perfil()
        self.assertIn('Entrar para comentar', html)
        self.assertNotIn('<textarea', html)
        self.assertNotIn('formulario-comentario', html)
        self.assertNotIn('Publicar', html)
        self.assertNotIn(FRASE_PRIMEIRO, html)

    def test_link_de_entrar_volta_ao_perfil_com_o_filtro(self):
        html = self.perfil('?comentarios_disciplina=11')
        href = re.search(r'<a href="([^"]+)">Entrar para comentar</a>', html).group(1)
        partes = urlsplit(href.replace('&amp;', '&'))
        self.assertEqual(partes.path, '/login')
        destino = urlsplit(parse_qs(partes.query)['next'][0])
        self.assertEqual(destino.path, '/professores/1')
        self.assertEqual(parse_qs(destino.query)['comentarios_disciplina'], ['11'])
        self.assertEqual(destino.fragment, 'comentarios')

    def test_convite_nao_aparece_para_professor_sem_disciplinas(self):
        html = self.perfil(professor=3)
        self.assertNotIn('Entrar para comentar', html)
        self.assertNotIn('<textarea', html)


class TestFormulario(BasePublicar):
    def test_formulario_do_usuario_logado(self):
        self.entrar()
        html = self.perfil('?disciplina_id=11&comentarios_disciplina=10&next=/professores?nome=jo')
        inicio = html.index('<form method="post" class="formulario-comentario"')
        form = html[inicio:html.index('</form>', inicio)]
        self.assertIn('action="/professores/1/comentarios"', form)
        self.assertRegex(form, r'name="csrf_token" value="[^"]+"')
        self.assertIn('name="next" value="/professores?nome=jo"', form)
        self.assertIn('name="comentarios_disciplina" value="10"', form)
        self.assertIn('name="disciplina_medias" value="11"', form)
        self.assertRegex(form, r'<select name="disciplina_id" id="disciplina_comentario" required')
        self.assertIn('<option value="" selected>Escolha a disciplina</option>', form)
        self.assertNotRegex(form, r'<option value="(10|11)"\s+selected')   # sem pré-seleção
        self.assertRegex(form, r'<textarea name="texto" id="texto_comentario" rows="5" maxlength="1000" required')
        self.assertIn('<label for="texto_comentario">', form)
        self.assertIn('2 a 1.000 caracteres', form)
        self.assertIn('Seu nome de usuário aparece junto do comentário.', form)
        self.assertIn('>Publicar</button>', form)
        self.assertNotIn('Entrar para comentar', html)

    def test_estado_vazio_convida_a_escrever_o_primeiro_so_para_logado(self):
        self.assertNotIn(FRASE_PRIMEIRO, self.perfil())
        self.entrar()
        self.assertIn('Ainda não há comentários para este professor. Escreva o primeiro.', self.perfil())

    def test_professor_sem_disciplinas_nao_mostra_formulario(self):
        self.entrar()
        html = self.perfil(professor=3)
        self.assertNotIn('<textarea', html)
        self.assertNotIn('formulario-comentario', html)
        self.assertNotIn(FRASE_PRIMEIRO, html)
        self.assertIn('Ainda não há comentários para este professor.', html)

    def test_postar_em_professor_sem_disciplinas_e_recusado(self):
        self.entrar()
        resposta = self.postar({'disciplina_id': '10', 'texto': 'comentário válido'}, professor=3)
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(self.comentarios(), [])


class TestPublicar(BasePublicar):
    def test_cria_com_o_usuario_da_sessao_mesmo_se_o_formulario_mandar_outro(self):
        id_logado = self.entrar()
        resposta = self.postar({'disciplina_id': '10', 'texto': '  Boa didática  ',
                                'usuario_id': OUTRO_USUARIO, 'professor_id': '2'})
        self.assertEqual(resposta.status_code, 303)
        gravado, = self.comentarios()
        self.assertEqual(gravado['usuario_id'], id_logado)
        self.assertNotEqual(gravado['usuario_id'], OUTRO_USUARIO)
        self.assertEqual((gravado['professor_id'], gravado['disciplina_id']), (1, 10))
        self.assertEqual(gravado['texto'], 'Boa didática')

    def test_comentario_publicado_aparece_no_perfil_com_o_username(self):
        self.entrar()
        self.postar({'disciplina_id': '11', 'texto': 'explica muito bem'})
        html = self.perfil()
        self.assertIn('explica muito bem', html)
        self.assertIn('<strong>ana</strong>', html)
        self.assertIn('CÁLCULO 2 — FGA0011', html)

    def test_mesma_conta_pode_comentar_varias_vezes_no_mesmo_par(self):
        self.entrar()
        for texto in ('primeiro relato', 'segundo relato'):
            self.assertEqual(self.postar({'disciplina_id': '10', 'texto': texto}).status_code, 303)
        self.assertEqual([c['texto'] for c in self.comentarios()], ['primeiro relato', 'segundo relato'])

    def test_redirect_de_sucesso_preserva_o_contexto(self):
        self.entrar()
        resposta = self.postar({
            'disciplina_id': '10', 'texto': 'texto válido', 'next': '/professores?nome=jo',
            'comentarios_disciplina': '11', 'disciplina_medias': '11'})
        self.assertEqual(resposta.status_code, 303)
        destino = urlsplit(resposta.headers['Location'])
        consulta = parse_qs(destino.query)
        self.assertEqual(destino.path, '/professores/1')
        self.assertEqual(destino.fragment, 'comentarios')
        self.assertEqual(consulta['comentarios_disciplina'], ['11'])
        self.assertEqual(consulta['disciplina_id'], ['11'])
        self.assertEqual(consulta['next'], ['/professores?nome=jo'])

    def test_redirect_descarta_contexto_invalido(self):
        self.entrar()
        resposta = self.postar({
            'disciplina_id': '10', 'texto': 'texto válido', 'next': 'https://evil.com/x',
            'comentarios_disciplina': '20', 'disciplina_medias': 'abc'})
        self.assertEqual(resposta.status_code, 303)
        destino = urlsplit(resposta.headers['Location'])
        consulta = parse_qs(destino.query)
        self.assertNotIn('comentarios_disciplina', consulta)   # 20 é de outro professor
        self.assertEqual(consulta['disciplina_id'], ['10'])    # volta à primeira disciplina
        self.assertEqual(consulta['next'], ['/professores'])   # destino externo trocado
        self.assertNotIn('evil.com', resposta.headers['Location'])

    def test_a_pagina_seguida_do_redirect_abre(self):
        self.entrar()
        resposta = self.postar({'disciplina_id': '10', 'texto': 'texto válido',
                                'comentarios_disciplina': '10', 'disciplina_medias': '10'})
        seguida = self.web.get(resposta.headers['Location'], headers={'Accept': 'text/html'})
        self.assertEqual(seguida.status_code, 200)
        self.assertIn('texto válido', seguida.get_data(as_text=True))

    def test_texto_com_html_e_gravado_como_texto_e_exibido_escapado(self):
        self.entrar()
        self.postar({'disciplina_id': '10', 'texto': '<script>alert(1)</script>'})
        self.assertEqual(self.comentarios()[0]['texto'], '<script>alert(1)</script>')
        html = self.perfil()
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', html)
        self.assertNotIn('<script>alert(1)', html)


class TestErros(BasePublicar):
    def setUp(self):
        super().setUp()
        self.entrar()

    def test_texto_invalido_da_400_e_preserva_texto_e_disciplina(self):
        for texto in ('x', ' y ', 'z' * 1001):
            with self.subTest(tamanho=len(texto)):
                resposta = self.postar({'disciplina_id': '11', 'texto': texto})
                self.assertEqual(resposta.status_code, 400)
                html = resposta.get_data(as_text=True)
                self.assertIn(f'>{texto}</textarea>', html)
                self.assertRegex(html, r'<option value="11"\s+selected>')
                self.assertRegex(html, r'<p class="campo-erro" id="erro-texto-comentario" role="alert">')
                self.assertIn('aria-invalid="true"', html)
        self.assertEqual(self.comentarios(), [])

    def test_mensagens_de_tamanho(self):
        curto = self.postar({'disciplina_id': '10', 'texto': 'x'}).get_data(as_text=True)
        longo = self.postar({'disciplina_id': '10', 'texto': 'x' * 1001}).get_data(as_text=True)
        self.assertIn('pelo menos 2 caracteres', curto)
        self.assertIn('no máximo 1000 caracteres', longo)

    def test_disciplina_de_outro_professor_da_erro(self):
        resposta = self.postar({'disciplina_id': '20', 'texto': 'texto que deve ser preservado'})
        self.assertEqual(resposta.status_code, 400)
        html = resposta.get_data(as_text=True)
        self.assertIn('Escolha a disciplina.', html)
        self.assertIn('>texto que deve ser preservado</textarea>', html)
        self.assertRegex(html, r'<select name="disciplina_id"[^>]*aria-invalid="true"')
        inicio = html.index('<form method="post" class="formulario-comentario"')
        formulario = html[inicio:html.index('</form>', inicio)]   # o select das médias não conta
        self.assertNotRegex(formulario, r'<option value="(10|11|20)"\s+selected>')
        self.assertEqual(self.comentarios(), [])

    def test_disciplina_nao_numerica_ou_ausente_da_erro(self):
        for dados in ({'disciplina_id': 'abc', 'texto': 'texto válido'},
                      {'disciplina_id': '', 'texto': 'texto válido'},
                      {'disciplina_id': '10.5', 'texto': 'texto válido'},
                      {'disciplina_id': '999', 'texto': 'texto válido'},
                      {'texto': 'texto válido'}):
            with self.subTest(dados=dados):
                resposta = self.postar(dados)
                self.assertEqual(resposta.status_code, 400)
                self.assertIn('Escolha a disciplina.', resposta.get_data(as_text=True))
        self.assertEqual(self.comentarios(), [])

    def test_os_dois_erros_aparecem_juntos(self):
        html = self.postar({'disciplina_id': '', 'texto': ' '}).get_data(as_text=True)
        self.assertIn('Escolha a disciplina.', html)
        self.assertIn('pelo menos 2 caracteres', html)

    def test_o_resto_do_perfil_continua_na_pagina_de_erro(self):
        html = self.postar({'disciplina_id': '', 'texto': 'ok'}).get_data(as_text=True)
        self.assertIn('Médias Consolidadas', html)
        self.assertIn('JOSÉ ÁVILA', html)

    def test_pagina_de_erro_escapa_o_texto_devolvido(self):
        perigoso = '</textarea><script>alert(1)</script>'
        html = self.postar({'disciplina_id': '', 'texto': perigoso}).get_data(as_text=True)
        self.assertIn('&lt;/textarea&gt;&lt;script&gt;alert(1)&lt;/script&gt;', html)
        self.assertNotIn('<script>alert(1)', html)

    def test_pagina_de_erro_nao_mostra_email_nem_ids(self):
        id_logado = next(u['id'] for u in self.cliente.auth.usuarios.values() if u['email'] == EMAIL)
        html = self.postar({'disciplina_id': '', 'texto': 'x', 'usuario_id': OUTRO_USUARIO}) \
            .get_data(as_text=True)
        for segredo in (EMAIL, id_logado, OUTRO_USUARIO):
            self.assertNotIn(segredo, html)

    def test_professor_inexistente_da_404(self):
        resposta = self.postar({'disciplina_id': '10', 'texto': 'texto válido'}, professor=999)
        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(self.comentarios(), [])

    def test_sem_csrf_da_erro_e_nao_grava(self):
        resposta = self.postar({'disciplina_id': '10', 'texto': 'texto válido'}, csrf=False)
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(self.comentarios(), [])


class TestLimite(BasePublicar):
    def test_o_11o_envio_na_hora_da_429(self):
        self.entrar()
        for n in range(10):
            resposta = self.postar({'disciplina_id': '10', 'texto': f'comentário {n}'})
            self.assertEqual(resposta.status_code, 303)
        resposta = self.postar({'disciplina_id': '10', 'texto': 'comentário 11'})
        self.assertEqual(resposta.status_code, 429)
        self.assertEqual(len(self.comentarios()), 10)

    def test_outra_conta_nao_e_afetada(self):
        self.entrar()
        for n in range(10):
            self.postar({'disciplina_id': '10', 'texto': f'comentário {n}'})
        outra = self.app.test_client()
        entrar_pela_web(outra, self.cliente, 'bia@gmail.com', 'Bia')
        self.assertEqual(self.postar({'disciplina_id': '10', 'texto': 'da bia'}, web=outra).status_code, 303)


class TestIndependenteDasNotas(BasePublicar):
    def test_publicar_nao_altera_avaliacoes_medias_nem_ranking(self):
        for n in range(5):
            self.cliente.tabelas['avaliacoes'].append({
                'id': n + 1, 'usuario_id': f'uuid-{n}', 'professor_id': 1, 'disciplina_id': 10,
                'ano': 2026, 'periodo': 1, **{c: 3 + n % 3 for c in CRITERIOS}})

        def retrato():
            with self.app.app_context():
                repos = repositorios()
                return (repos.avaliacoes.calcular_medias(1), repos.avaliacoes.calcular_medias(1, 10),
                        repos.professores.ranking(), repos.professores.catalogo())

        self.entrar()   # logado antes do retrato, para o topo da página não mudar
        antes_tabela = [dict(l) for l in self.cliente.tabelas['avaliacoes']]
        antes = retrato()
        ranking_antes = self.web.get('/ranking').get_data(as_text=True)

        self.assertEqual(self.postar({'disciplina_id': '10', 'texto': 'texto válido'}).status_code, 303)

        self.assertEqual(self.cliente.tabelas['avaliacoes'], antes_tabela)
        self.assertEqual(retrato(), antes)
        self.assertEqual(self.web.get('/ranking').get_data(as_text=True), ranking_antes)
        self.assertEqual(len(self.comentarios()), 1)


if __name__ == '__main__':
    unittest.main()
