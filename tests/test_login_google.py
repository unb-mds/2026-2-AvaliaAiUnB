"""Login com Google pelo Supabase Auth (fluxo PKCE), com cliente falso em memória."""
import re
import unittest
from urllib.parse import parse_qs, urlparse

from app import create_app
from app.controllers.session_controller import COOKIE_ACESSO
from app.routes.auth_routes import CHAVE_PKCE_GOOGLE
from app.validacoes import CRITERIOS
from tests.fake_supabase import ClienteFalso

META_GOOGLE = {'full_name': 'Bia Souza', 'name': 'Bia Souza', 'email_verified': True}


class TestLoginGoogle(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                               'SUPABASE_CLIENT': self.cliente})
        self.web = self.app.test_client()

    def iniciar(self):
        resposta = self.web.get('/login/google')
        self.assertEqual(resposta.status_code, 302)
        with self.web.session_transaction() as sessao:
            verificador = sessao[CHAVE_PKCE_GOOGLE]
        return resposta, verificador

    def entrar_com_google(self, email='bia.souza@gmail.com', metadata=META_GOOGLE):
        _, verificador = self.iniciar()
        self.cliente.auth.preparar_retorno_google('codigo-1', email, metadata, verificador)
        return self.web.get('/login/google/retorno?code=codigo-1')

    def token_csrf(self, caminho):
        pagina = self.web.get(caminho, headers={'Accept': 'text/html'}).get_data(as_text=True)
        return re.search(r'name="csrf_token" value="([^"]+)"', pagina).group(1)

    def test_inicio_redireciona_ao_supabase_com_pkce(self):
        resposta, verificador = self.iniciar()
        destino = urlparse(resposta.headers['Location'])
        parametros = parse_qs(destino.query)
        self.assertEqual(f'{destino.scheme}://{destino.netloc}{destino.path}',
                         'https://projeto-falso.supabase.co/auth/v1/authorize')
        self.assertEqual(parametros['provider'], ['google'])
        self.assertEqual(parametros['code_challenge_method'], ['s256'])
        self.assertTrue(parametros['redirect_to'][0].endswith('/login/google/retorno'))
        # O verificador fica só no servidor; na URL vai apenas o desafio derivado dele.
        self.assertNotIn(verificador, resposta.headers['Location'])

    def test_primeiro_acesso_cria_perfil_e_sessao(self):
        resposta = self.entrar_com_google()
        self.assertEqual(resposta.status_code, 303)
        self.assertIn(COOKIE_ACESSO, resposta.headers.get('Set-Cookie', ''))
        self.assertEqual(self.cliente.tabelas['perfis'][0]['username'], 'bia.souza')
        self.assertEqual(self.cliente.tabelas['perfis'][0]['nome_completo'], 'Bia Souza')
        perfil = self.web.get('/perfil', headers={'Accept': 'application/json'}).get_json()
        self.assertEqual((perfil['username'], perfil['nome']), ('bia.souza', 'Bia Souza'))

    def test_username_em_uso_gera_outro_livre(self):
        self.cliente.tabelas['perfis'].append(
            {'id': 'outro', 'username': 'bia.souza', 'nome_completo': 'Outra'})
        self.assertEqual(self.entrar_com_google().status_code, 303)
        novo = self.cliente.tabelas['perfis'][-1]['username']
        self.assertRegex(novo, r'^bia\.souza\d{5}$')

    def test_conta_antiga_com_senha_e_vinculada_e_mantem_perfil_e_avaliacoes(self):
        # Conta criada pelo cadastro com senha (sistema anterior), já com uma avaliação.
        uid = 'conta-antiga'
        self.cliente.auth.usuarios[uid] = {'id': uid, 'email': 'ana@gmail.com',
                                           'user_metadata': {'nome': 'Ana', 'username': 'ana'}}
        self.cliente.tabelas['perfis'].append({'id': uid, 'username': 'ana', 'nome_completo': 'Ana'})
        self.cliente.tabelas['avaliacoes'].append({'id': 1, 'usuario_id': uid, 'professor_id': 2,
                                                   'disciplina_id': 20, 'ano': 2026, 'periodo': 2,
                                                   **{c: 4 for c in CRITERIOS}})

        self.assertEqual(self.entrar_com_google(email='ana@gmail.com').status_code, 303)
        self.assertEqual(len(self.cliente.auth.usuarios), 1)
        self.assertEqual(len(self.cliente.tabelas['perfis']), 1)
        perfil = self.web.get('/perfil', headers={'Accept': 'application/json'}).get_json()
        self.assertEqual((perfil['id'], perfil['username'], perfil['nome']), (uid, 'ana', 'Ana'))
        self.assertEqual(len(perfil['avaliacoes']), 1)

    def test_usuario_do_google_avalia_professor(self):
        self.entrar_com_google()
        dados = {**{c: '4' for c in CRITERIOS}, 'disciplina_id': '20',
                 'csrf_token': self.token_csrf('/avaliar/2?disciplina_id=20')}
        self.assertLess(self.web.post('/avaliar/2', data=dados).status_code, 400)
        gravada, = self.cliente.tabelas['avaliacoes']
        self.assertEqual(gravada['usuario_id'], self.cliente.tabelas['perfis'][0]['id'])

    def test_retorno_invalido_nao_autentica(self):
        # Sem ter iniciado o fluxo neste navegador (sem verificador): login CSRF.
        self.cliente.auth.preparar_retorno_google('codigo-x', 'x@gmail.com', META_GOOGLE, 'outro')
        resposta = self.web.get('/login/google/retorno?code=codigo-x')
        self.assertEqual(resposta.status_code, 400)
        self.assertNotIn(COOKIE_ACESSO, resposta.headers.get('Set-Cookie', ''))

        for url in ('/login/google/retorno', '/login/google/retorno?code=inexistente',
                    '/login/google/retorno?error=access_denied'):
            self.iniciar()
            resposta = self.web.get(url)
            self.assertEqual(resposta.status_code, 400, url)
            self.assertIn('Não foi possível entrar com o Google', resposta.get_data(as_text=True))
        self.assertEqual(self.cliente.tabelas['perfis'], [])

    def test_codigo_nao_pode_ser_reutilizado(self):
        self.assertEqual(self.entrar_com_google().status_code, 303)
        self.assertEqual(self.web.get('/login/google/retorno?code=codigo-1').status_code, 400)

    def test_botao_na_tela_de_login(self):
        self.assertIn('href="/login/google"', self.web.get('/login').get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
