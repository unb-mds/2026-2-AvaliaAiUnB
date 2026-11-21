"""Atalhos para os comentários no perfil do professor e na tela de avaliar (issue #201)."""
import re
import unittest
from urllib.parse import unquote

from flask_wtf.csrf import generate_csrf

from app import create_app
from app.validacoes import CRITERIOS
from tests.fake_supabase import ClienteFalso, entrar_pela_web

NOTAS = {**{c: '4' for c in CRITERIOS}, 'dificuldade': '3', 'disciplina_id': '10'}


class BaseAtalhos(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        app = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                          'SUPABASE_CLIENT': self.cliente})
        app.add_url_rule('/teste/csrf', 'teste_csrf', generate_csrf)
        self.web = app.test_client()

    def entrar(self):
        entrar_pela_web(self.web, self.cliente, 'ana@gmail.com', 'Ana')

    def postar(self, caminho, data):
        token = self.web.get('/teste/csrf').get_data(as_text=True)
        return self.web.post(caminho, data={**data, 'csrf_token': token})


class TestAtalhoNoPerfil(BaseAtalhos):
    def test_visitante_ve_o_link_para_a_secao_de_comentarios(self):
        html = self.web.get('/professores/1').get_data(as_text=True)

        self.assertIn('<a class="btn ghost atalho-comentarios" href="#comentarios">Comentários</a>', html)
        self.assertEqual(html.count('id="comentarios"'), 1)   # o alvo da âncora existe
        self.assertLess(html.index('atalho-comentarios'), html.index('id="comentarios"'))

    def test_logado_tambem_ve(self):
        self.entrar()
        html = self.web.get('/professores/1').get_data(as_text=True)

        self.assertIn('href="#comentarios">Comentários</a>', html)

    def test_link_nao_mostra_contagem(self):
        html = self.web.get('/professores/1').get_data(as_text=True)
        link = re.search(r'class="btn ghost atalho-comentarios"[^>]*>(.*?)</a>', html, re.S).group(1)

        self.assertNotRegex(link, r'\d')


class TestConviteNaTelaDeAvaliar(BaseAtalhos):
    def setUp(self):
        super().setUp()
        self.entrar()

    def convite(self, html):
        return re.search(r'<p class="convite-comentario">(.*?)</p>', html, re.S)

    def test_convite_leva_ao_perfil_na_secao_de_comentarios_com_next(self):
        html = self.web.get('/avaliar/1?disciplina_id=10&next=/professores?nome=jose'
                            ).get_data(as_text=True)
        convite = self.convite(html)

        self.assertIsNotNone(convite)
        self.assertIn('Quer explicar sua nota?', convite.group(1))
        href = re.search(r'<a href="([^"]+)">Escreva um comentário</a>', convite.group(1)).group(1)
        self.assertEqual(unquote(href.replace('&amp;', '&')),
                         '/professores/1?disciplina_id=10&next=/professores?nome=jose#comentarios')

    def test_convite_fica_fora_do_formulario_e_sem_campo_novo(self):
        html = self.web.get('/avaliar/1?disciplina_id=10').get_data(as_text=True)
        inicio = html.index('id="formAvaliacao"')
        formulario = html[inicio:html.index('</form>', inicio)]

        self.assertNotIn('convite-comentario', formulario)
        self.assertNotIn('<textarea', html)
        self.assertEqual(sorted(set(re.findall(r'name="([^"]+)"', formulario))),
                         # 'semestre': turma cursada (issue #252), não vem do convite.
                         sorted([*CRITERIOS, 'csrf_token', 'disciplina_id', 'semestre']))

    def test_edicao_nao_mostra_o_convite(self):
        self.assertEqual(self.postar('/avaliar/1', NOTAS).status_code, 303)
        id_avaliacao = self.cliente.tabelas['avaliacoes'][0]['id']
        html = self.web.get(f'/avaliacoes/{id_avaliacao}/editar',
                            headers={'Accept': 'text/html'}).get_data(as_text=True)

        self.assertNotIn('convite-comentario', html)

    def test_envio_da_avaliacao_continua_gravando_igual(self):
        resposta = self.postar('/avaliar/1?next=/professores', NOTAS)

        self.assertEqual(resposta.status_code, 303)
        self.assertEqual(urlparse_caminho(resposta.headers['Location']), '/professores/1')
        gravadas = self.cliente.tabelas['avaliacoes']
        self.assertEqual(len(gravadas), 1)
        self.assertEqual({c: gravadas[0][c] for c in CRITERIOS},
                         {**{c: 4 for c in CRITERIOS}, 'dificuldade': 3})
        self.assertEqual((gravadas[0]['professor_id'], gravadas[0]['disciplina_id']), (1, 10))
        self.assertEqual(self.cliente.tabelas['comentarios'], [])

    def test_segunda_avaliacao_do_mesmo_par_continua_recusada(self):
        self.postar('/avaliar/1', NOTAS)

        self.assertEqual(self.postar('/avaliar/1', NOTAS).status_code, 409)
        self.assertEqual(len(self.cliente.tabelas['avaliacoes']), 1)

    def test_tela_de_avaliar_continua_exigindo_login(self):
        anonimo = create_anonimo()
        resposta = anonimo.get('/avaliar/1?disciplina_id=10')

        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(urlparse_caminho(resposta.headers['Location']), '/login')
        self.assertNotIn('convite-comentario', resposta.get_data(as_text=True))


def urlparse_caminho(url):
    from urllib.parse import urlsplit
    return urlsplit(url).path


def create_anonimo():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                      'SUPABASE_CLIENT': ClienteFalso()})
    return app.test_client()


if __name__ == '__main__':
    unittest.main()
