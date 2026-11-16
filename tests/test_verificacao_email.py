import os
import re
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from app import create_app
from app.controllers.session_controller import COOKIE_ACESSO
from app.repositorio import UsuarioRepository
from tests.fake_supabase import ClienteFalso, sessao_google


class TestVerificacaoEmail(unittest.TestCase):
    def setUp(self):
        ambiente = patch.dict(os.environ, {
            'VERIFICACAO_EMAIL_ORIGEM': 'https://avalia.example.test',
            'VERIFICACAO_EMAIL_SMTP_HOST': 'smtp.example.test',
            'VERIFICACAO_EMAIL_SMTP_USUARIO': 'usuario-de-teste',
            'VERIFICACAO_EMAIL_SMTP_SENHA': 'senha-de-teste',
            'VERIFICACAO_EMAIL_REMETENTE': 'aplicacao@example.test',
        })
        ambiente.start()
        self.addCleanup(ambiente.stop)
        self.cliente = ClienteFalso()
        self.cliente.tabelas['emails_verificados'] = []
        self.repositorio = UsuarioRepository(self.cliente, lambda: self.cliente)
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'verificacao-teste',
                               'SUPABASE_CLIENT': self.cliente})
        self.web = self.app.test_client()
        self.caminho = '/perfil/verificar-email'
        self.usuario_id = self._entrar('ana@example.test', 'Ana')

    def _entrar(self, email, nome):
        with self.app.app_context():
            sessao = sessao_google(self.cliente, self.repositorio, email, nome)
        self.web.set_cookie(COOKIE_ACESSO, sessao['access_token'])
        return self.cliente.auth.tokens[sessao['access_token']]

    def _postar(self, caminho, **dados):
        pagina = self.web.get(self.caminho)
        csrf = re.search(r'name="csrf_token" value="([^"]+)"', pagina.text)[1]
        return self.web.post(caminho, base_url='https://localhost',
                             headers={'Referer': 'https://localhost/'},
                             data={'csrf_token': csrf, **dados})

    @patch('app.verificacao_email.smtplib.SMTP_SSL')
    def _solicitar(self, smtp):
        resposta = self._postar('/perfil/enviar-verificacao', email='outro@example.test')
        self.assertEqual(resposta.status_code, 303)
        cliente_smtp = smtp.return_value.__enter__.return_value
        mensagem = cliente_smtp.send_message.call_args.args[0]
        self.assertEqual(mensagem['To'], 'ana@example.test')
        link = re.search(r'https://\S+', mensagem.get_content())[0]
        url = urlsplit(link)
        self.assertEqual(url.netloc, 'avalia.example.test')
        self.assertEqual(url.path, self.caminho)
        return url.query, parse_qs(url.query)['chave'][0]

    def test_abertura_do_link_e_confirmacao_com_csrf(self):
        query, chave = self._solicitar()
        resposta = self.web.get(f'{self.caminho}?{query}')
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.headers['Referrer-Policy'], 'origin')
        self.assertEqual(self.cliente.tabelas['emails_verificados'], [])
        self.assertEqual(self.web.post(self.caminho, data={'chave': chave}).status_code, 400)
        self.assertEqual(self._postar(self.caminho, chave=chave).status_code, 303)
        self.assertIn('E-mail verificado', self.web.get(self.caminho).text)
        linha, = self.cliente.tabelas['emails_verificados']
        self.assertEqual(linha['usuario_id'], self.usuario_id)
        self.assertNotIn('ana@example.test', str(linha))

    def test_link_invalido_expirado_ou_de_outra_conta(self):
        _, chave = self._solicitar()
        self.assertEqual(self._postar(self.caminho, chave='invalida').status_code, 400)
        with patch('app.verificacao_email.VALIDADE_LINK', -1):
            self.assertEqual(self._postar(self.caminho, chave=chave).status_code, 400)
        self._entrar('bia@example.test', 'Bia')
        self.assertEqual(self._postar(self.caminho, chave=chave).status_code, 400)
        self.assertEqual(self.cliente.tabelas['emails_verificados'], [])

    def test_mudanca_de_endereco_invalida_confirmacao_e_link(self):
        _, chave = self._solicitar()
        self.assertEqual(self._postar(self.caminho, chave=chave).status_code, 303)
        self.cliente.auth.usuarios[self.usuario_id]['email'] = 'novo@example.test'
        self.assertIn('Enviar link de verificação', self.web.get(self.caminho).text)
        self.assertEqual(self._postar(self.caminho, chave=chave).status_code, 400)
