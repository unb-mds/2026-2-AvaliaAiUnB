import unittest

from app import create_app
from tests.fake_supabase import ClienteFalso


class TestPaginaPrivacidade(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.web = create_app({
            'TESTING': True,
            'SECRET_KEY': 'chave-teste-privacidade',
            'SUPABASE_CLIENT': self.cliente,
        }).test_client()

    def test_pagina_privacidade_abre_sem_login_e_contem_secoes_obrigatorias(self):
        resposta = self.web.get('/privacidade')
        self.assertEqual(resposta.status_code, 200)
        html = resposta.get_data(as_text=True)

        # Dados guardados e finalidade
        self.assertIn('Política de Privacidade e Termos de Uso', html)
        self.assertIn('E-mail', html)
        self.assertIn('nome de usuário', html)
        self.assertIn('Avaliações', html)

        # Formulário de feedback, regras de conduta e exclusão de dados
        self.assertIn('feedback', html.lower())
        self.assertIn('ofensas', html.lower())
        self.assertIn('avaliações falsas', html.lower())
        self.assertIn('exclusão', html.lower())

    def test_link_para_privacidade_esta_acessivel_no_rodape(self):
        resposta_inicio = self.web.get('/')
        self.assertEqual(resposta_inicio.status_code, 200)
        html_inicio = resposta_inicio.get_data(as_text=True)
        self.assertIn('<footer', html_inicio)
        self.assertIn('href="/privacidade"', html_inicio)


if __name__ == '__main__':
    unittest.main()