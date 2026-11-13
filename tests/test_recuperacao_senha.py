"""Testes para o fluxo de recuperação e redefinição de senha."""
os_environ_backup = None
import os
import unittest
from unittest.mock import patch

# Define uma SECRET_KEY forte com 32+ caracteres e as variáveis do Supabase para os testes
os.environ.setdefault('SECRET_KEY', 'chave-secreta-super-segura-e-com-mais-de-32-caracteres-para-passar-na-validacao')
os.environ.setdefault('SUPABASE_URL', 'https://mock.supabase.co')
os.environ.setdefault('SUPABASE_SERVICE_KEY', 'mock-service-key')

from run import app


class RecuperacaoSenhaTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

    def test_pagina_recuperar_senha_get(self):
        """Garante que a página de solicitação de recuperação carrega corretamente."""
        response = self.client.get('/recuperar-senha')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Recuperar Senha', response.data)

    @patch('app.repositorio.UsuarioRepository.enviar_email_recuperacao')
    def test_solicitar_recuperacao_post(self, mock_enviar):
        """Verifica se a rota de solicitação de e-mail oculta a existência do utilizador (segurança)."""
        mock_enviar.return_value = True
        response = self.client.post('/recuperar-senha', data={'email': 'teste@unb.br', 'formato': 'html'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Se o e-mail estiver cadastrado', response.data)

    def test_pagina_redefinir_senha_get(self):
        """Garante que a página de criação de nova senha carrega corretamente."""
        response = self.client.get('/redefinir-senha')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Criar Nova Senha', response.data)

    def test_redefinir_senha_validacao_tamanho(self):
        """Garante que senhas menores que 6 caracteres são rejeitadas na regra de negócio."""
        response = self.client.post('/redefinir-senha', data={
            'senha': '123',
            'confirmar_senha': '123',
            'access_token': 'token_falso',
            'formato': 'html'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'no m\xc3\xadnimo 6 caracteres', response.data)


if __name__ == '__main__':
    unittest.main()