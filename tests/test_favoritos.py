"""Favoritar professores (issue #223, RF11), com o cliente falso."""
import unittest

from flask_wtf.csrf import generate_csrf

from app import create_app
from app.repositorio import FavoritoRepository
from tests.fake_supabase import ClienteFalso, entrar_pela_web

EMAIL_ANA = 'ana@gmail.com'
EMAIL_BRUNO = 'bruno@gmail.com'


class BaseFavoritos(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                               'SUPABASE_CLIENT': self.cliente})
        self.app.add_url_rule('/teste/csrf', 'teste_csrf', generate_csrf)
        self.web = self.app.test_client()
        self.id_ana = self._entrar(self.web, EMAIL_ANA, 'Ana')

    def _entrar(self, web, email, nome):
        entrar_pela_web(web, self.cliente, email, nome)
        return next(u['id'] for u in self.cliente.auth.usuarios.values() if u['email'] == email)

    def favoritos(self):
        return [dict(l) for l in self.cliente.tabelas['favoritos']]

    def favoritar(self, professor_id=1, acao='adicionar', web=None, csrf=True,
                  accept='text/html', **extra):
        web = web or self.web
        dados = {'acao': acao, **extra}
        if csrf:
            dados['csrf_token'] = web.get('/teste/csrf').get_data(as_text=True)
        return web.post(f'/professores/{professor_id}/favorito', data=dados,
                        headers={'Accept': accept})


class TestFavoritarRotas(BaseFavoritos):
    def test_favorita_e_desfavorita(self):
        resposta = self.favoritar(1)
        self.assertEqual(resposta.status_code, 303)
        self.assertEqual(resposta.headers['Location'], '/professores/1')
        self.assertEqual([(f['usuario_id'], f['professor_id']) for f in self.favoritos()],
                         [(self.id_ana, 1)])

        resposta = self.favoritar(1, 'remover')
        self.assertEqual(resposta.status_code, 303)
        self.assertEqual(self.favoritos(), [])

    def test_favoritar_duas_vezes_nao_duplica(self):
        self.favoritar(1)
        self.favoritar(1)
        self.assertEqual(len(self.favoritos()), 1)

    def test_remover_o_que_nao_e_favorito_nao_falha(self):
        self.assertEqual(self.favoritar(2, 'remover').status_code, 303)
        self.assertEqual(self.favoritos(), [])

    def test_resposta_json(self):
        resposta = self.favoritar(2, accept='application/json')
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json(), {'professor_id': 2, 'favorito': True})
        resposta = self.favoritar(2, 'remover', accept='application/json')
        self.assertEqual(resposta.get_json(), {'professor_id': 2, 'favorito': False})

    def test_exige_csrf(self):
        self.assertEqual(self.favoritar(1, csrf=False).status_code, 400)
        self.assertEqual(self.favoritos(), [])

    def test_exige_login(self):
        anonimo = self.app.test_client()
        resposta = anonimo.post('/professores/1/favorito', data={'acao': 'adicionar'},
                                headers={'Accept': 'application/json'})
        # Sem sessão não há token CSRF válido nem usuário: nada é gravado.
        self.assertIn(resposta.status_code, (400, 401))
        self.assertEqual(self.favoritos(), [])

    def test_exige_login_com_csrf_valido(self):
        anonimo = self.app.test_client()
        resposta = self.favoritar(1, web=anonimo, accept='application/json')
        self.assertEqual(resposta.status_code, 401)
        self.assertEqual(self.favoritos(), [])

    def test_acao_invalida(self):
        self.assertEqual(self.favoritar(1, 'trocar').status_code, 400)
        self.assertEqual(self.favoritos(), [])

    def test_professor_inexistente(self):
        self.assertEqual(self.favoritar(999).status_code, 404)
        self.assertEqual(self.favoritos(), [])

    def test_usuario_id_do_formulario_e_ignorado(self):
        self.favoritar(1, usuario_id='outra-pessoa')
        self.assertEqual([f['usuario_id'] for f in self.favoritos()], [self.id_ana])

    def test_destino_seguro_e_respeitado(self):
        resposta = self.favoritar(1, destino='/perfil')
        self.assertEqual(resposta.headers['Location'], '/perfil')

    def test_destino_externo_e_ignorado(self):
        for destino in ('https://malicioso.example/', '//malicioso.example', '/\\malicioso'):
            with self.subTest(destino=destino):
                resposta = self.favoritar(1, destino=destino)
                self.assertEqual(resposta.headers['Location'], '/professores/1')

    def test_desfavoritar_nao_afeta_outro_usuario(self):
        web_bruno = self.app.test_client()
        id_bruno = self._entrar(web_bruno, EMAIL_BRUNO, 'Bruno')
        self.favoritar(1)
        self.favoritar(1, web=web_bruno)
        self.favoritar(1, 'remover')
        self.assertEqual([f['usuario_id'] for f in self.favoritos()], [id_bruno])


class TestFavoritosTelas(BaseFavoritos):
    def ver(self, caminho, web=None):
        return (web or self.web).get(caminho, headers={'Accept': 'text/html'})

    def test_botao_no_perfil_do_professor(self):
        html = self.ver('/professores/1').get_data(as_text=True)
        self.assertIn('action="/professores/1/favorito"', html)
        self.assertIn('name="acao" value="adicionar"', html)
        self.assertIn('aria-pressed="false"', html)
        self.assertIn('name="csrf_token"', html)

        self.favoritar(1)
        html = self.ver('/professores/1').get_data(as_text=True)
        self.assertIn('name="acao" value="remover"', html)
        self.assertIn('aria-pressed="true"', html)

    def test_visitante_ve_link_para_entrar(self):
        html = self.ver('/professores/1', self.app.test_client()).get_data(as_text=True)
        self.assertNotIn('/professores/1/favorito', html)
        self.assertIn('Entrar para favoritar', html)

    def test_lista_no_perfil_do_usuario(self):
        html = self.ver('/perfil').get_data(as_text=True)
        self.assertIn('Favoritos', html)
        self.assertIn('ainda não favoritou', html)

        self.favoritar(1)
        self.favoritar(2)
        html = self.ver('/perfil').get_data(as_text=True)
        self.assertIn('JOSÉ ÁVILA', html)
        self.assertIn('MARIA LIMA', html)
        # Mais recente primeiro
        self.assertLess(html.index('MARIA LIMA'), html.index('JOSÉ ÁVILA'))
        self.assertIn('Remover JOSÉ ÁVILA dos favoritos', html)

    def test_lista_aparece_so_para_o_dono(self):
        self.favoritar(1)
        web_bruno = self.app.test_client()
        self._entrar(web_bruno, EMAIL_BRUNO, 'Bruno')
        html = self.ver('/perfil', web_bruno).get_data(as_text=True)
        self.assertNotIn('JOSÉ ÁVILA', html)
        self.assertIn('ainda não favoritou', html)
        # O botão no perfil do professor reflete só a lista de quem está logado
        html = self.ver('/professores/1', web_bruno).get_data(as_text=True)
        self.assertIn('aria-pressed="false"', html)

    def test_perfil_json_traz_favoritos(self):
        self.favoritar(2)
        dados = self.web.get('/perfil', headers={'Accept': 'application/json'}).get_json()
        self.assertEqual(dados['favoritos'],
                         [{'id': 2, 'nome': 'MARIA LIMA', 'departamento': 'FCTE'}])

    def test_remover_pelo_perfil_volta_ao_perfil(self):
        self.favoritar(1)
        resposta = self.favoritar(1, 'remover', destino='/perfil')
        self.assertEqual(resposta.headers['Location'], '/perfil')
        self.assertEqual(self.favoritos(), [])


class TestFavoritoRepository(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.repo = FavoritoRepository(self.cliente)

    def test_ciclo_completo(self):
        self.assertFalse(self.repo.eh_favorito('u1', 1))
        self.repo.adicionar('u1', 1)
        self.repo.adicionar('u1', 2)
        self.repo.adicionar('u2', 3)
        self.assertTrue(self.repo.eh_favorito('u1', 1))
        self.assertFalse(self.repo.eh_favorito('u2', 1))
        self.assertEqual([p['id'] for p in self.repo.listar_por_usuario('u1')], [2, 1])
        self.assertTrue(self.repo.remover('u1', 1))
        self.assertFalse(self.repo.remover('u1', 1))
        self.assertEqual([p['id'] for p in self.repo.listar_por_usuario('u1')], [2])

    def test_lista_vazia(self):
        self.assertEqual(self.repo.listar_por_usuario('u1'), [])

    def test_ignora_professor_removido_do_catalogo(self):
        self.repo.adicionar('u1', 1)
        self.cliente.tabelas['favoritos'].append({'usuario_id': 'u1', 'professor_id': 404,
                                                  'criado_em': '2030-01-01T00:00:00+00:00'})
        self.assertEqual([p['id'] for p in self.repo.listar_por_usuario('u1')], [1])


if __name__ == '__main__':
    unittest.main()
