import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from app import create_app
from app.controllers.session_controller import sanitizar_destino


class TestRedirecionamentoPosLogin(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["COOKIE_SECURE"] = False
        self.client = self.app.test_client()

    def test_sanitizar_destino_aceita_caminhos_internos_com_query(self):
        self.assertEqual(sanitizar_destino("/perfil"), "/perfil")
        self.assertEqual(
            sanitizar_destino("/avaliar/245?disciplina_id=317&next=/professores"),
            "/avaliar/245?disciplina_id=317&next=/professores",
        )

    def test_sanitizar_destino_rejeita_open_redirect(self):
        invalidos = [
            None,
            "",
            "https://evil.com/phishing",
            "http://evil.com",
            "//evil.com",
            "/\\evil.com",
            "///evil.com",
            "javascript:alert(1)",
            "/perfil\r\nSet-Cookie: a=b",
            "/login",
        ]
        for url in invalidos:
            with self.subTest(url=url):
                self.assertIsNone(sanitizar_destino(url))

    def test_rota_protegida_redireciona_para_login_preservando_origem_e_query(self):
        resposta = self.client.get("/avaliar/245?disciplina_id=317&next=/professores")
        self.assertEqual(resposta.status_code, 302)

        location = urlsplit(resposta.headers["Location"])
        self.assertEqual(location.path, "/login")
        params = parse_qs(location.query)
        self.assertEqual(
            params.get("next"),
            ["/avaliar/245?disciplina_id=317&next=/professores"],
        )

    @patch("app.controllers.session_controller.repositorios")
    @patch("app.controllers.auth_controller.concluir_login_google")
    @patch("app.controllers.auth_controller.iniciar_login_google")
    def test_fluxo_oauth_google_retorna_para_pagina_e_query_originais(
        self, mock_iniciar, mock_concluir, mock_repos
    ):
        mock_iniciar.return_value = ("https://accounts.google.com/o/oauth2/auth", "verificador-pkce")
        mock_concluir.return_value = {"access_token": "tok-acesso", "refresh_token": "tok-refresh"}
        mock_repos.return_value.usuarios.usuario_do_token.return_value = {
            "id": "u1",
            "nome": "Estudante UnB",
            "email": "aluno@aluno.unb.br",
            "username": "estudante",
        }

        destino_original = "/avaliar/245?disciplina_id=317&next=/professores"

        # 1. Tenta acessar ação protegida deslogado
        r1 = self.client.get(destino_original)
        self.assertEqual(r1.status_code, 302)

        # 2. Abre /login?next=...
        r2 = self.client.get(r1.headers["Location"])
        self.assertEqual(r2.status_code, 200)

        # 3. Inicia OAuth com Google
        r3 = self.client.get("/login/google")
        self.assertEqual(r3.status_code, 302)

        # 4. Retorna do Google e deve ir direto para o destino original com query string
        r4 = self.client.get("/login/google/retorno?code=codigo-oauth")
        self.assertEqual(r4.status_code, 303)
        self.assertEqual(urlsplit(r4.headers["Location"]).path, "/avaliar/245")
        self.assertEqual(
            urlsplit(r4.headers["Location"]).query,
            "disciplina_id=317&next=/professores",
        )

    @patch("app.controllers.auth_controller.concluir_login_google")
    @patch("app.controllers.auth_controller.iniciar_login_google")
    def test_url_externa_no_parametro_next_e_ignorada_apos_login(
        self, mock_iniciar, mock_concluir
    ):
        mock_iniciar.return_value = ("https://accounts.google.com/o/oauth2/auth", "verificador-pkce")
        mock_concluir.return_value = {"access_token": "tok-acesso", "refresh_token": "tok-refresh"}

        self.client.get("/login?next=https://evil.com")
        self.client.get("/login/google?next=//evil.com")
        resposta = self.client.get("/login/google/retorno?code=codigo-oauth")

        self.assertEqual(resposta.status_code, 303)
        self.assertEqual(urlsplit(resposta.headers["Location"]).path, "/")


if __name__ == "__main__":
    unittest.main()