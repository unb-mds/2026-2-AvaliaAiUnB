"""Testes da autenticação do AvaliaAi UnB."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from werkzeug.security import check_password_hash

from app import create_app
from app.database import get_db_connection


class TestAutenticacao(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.caminho_banco = str(
            Path(self.temp.name) / "teste_autenticacao.db"
        )

        self.app = create_app({
            "TESTING": True,
            "DATABASE": self.caminho_banco
        })

        self.client = self.app.test_client()

    def sql(self, comando, parametros=()):
        with self.app.app_context():
            conexao = get_db_connection()
            try:
                cursor = conexao.execute(comando, parametros)
                linhas = cursor.fetchall()
                conexao.commit()
                return linhas
            finally:
                conexao.close()

    def cadastrar_usuario(self):
        return self.client.post(
            "/cadastro",
            data={
                "nome": "Ana Souza",
                "email": "ana@example.com",
                "senha": "senha123",
                "confirmar_senha": "senha123"
            }
        )

    def test_cadastro_cria_usuario_com_senha_hash(self):
        resposta = self.cadastrar_usuario()

        self.assertEqual(resposta.status_code, 201)

        usuario = self.sql(
            "SELECT * FROM usuarios WHERE email = ?",
            ("ana@example.com",)
        )[0]

        self.assertEqual(usuario["nome"], "Ana Souza")
        self.assertNotEqual(usuario["senha"], "senha123")
        self.assertTrue(
            check_password_hash(usuario["senha"], "senha123")
        )

    def test_login_com_credenciais_validas_cria_sessao(self):
        self.cadastrar_usuario()

        resposta = self.client.post(
            "/login",
            data={
                "email": "ana@example.com",
                "senha": "senha123"
            }
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertIn(
            "Login realizado com sucesso",
            resposta.get_data(as_text=True)
        )

        sessoes = self.sql("SELECT * FROM sessoes")

        self.assertEqual(len(sessoes), 1)
        self.assertEqual(sessoes[0]["usuario_id"], 1)

    def test_login_com_senha_incorreta(self):
        self.cadastrar_usuario()

        resposta = self.client.post(
            "/login",
            data={
                "email": "ana@example.com",
                "senha": "senha_errada"
            }
        )

        self.assertEqual(resposta.status_code, 401)
        self.assertEqual(
            len(self.sql("SELECT * FROM sessoes")),
            0
        )

    def test_login_com_email_inexistente(self):
        resposta = self.client.post(
            "/login",
            data={
                "email": "naoexiste@example.com",
                "senha": "senha123"
            }
        )

        self.assertEqual(resposta.status_code, 401)
        self.assertEqual(
            len(self.sql("SELECT * FROM sessoes")),
            0
        )

    def test_perfil_exige_autenticacao(self):
        resposta = self.client.get(
            "/perfil",
            headers={"Accept": "application/json"}
        )

        self.assertEqual(resposta.status_code, 401)

    def test_usuario_autenticado_acessa_perfil(self):
        self.cadastrar_usuario()

        self.client.post(
            "/login",
            data={
                "email": "ana@example.com",
                "senha": "senha123"
            }
        )

        resposta = self.client.get(
            "/perfil",
            headers={"Accept": "application/json"}
        )

        self.assertEqual(resposta.status_code, 200)

        dados = resposta.get_json()

        self.assertEqual(dados["nome"], "Ana Souza")
        self.assertEqual(dados["email"], "ana@example.com")
        self.assertNotIn("senha", dados)

    def test_logout_revoga_sessao(self):
        self.cadastrar_usuario()

        self.client.post(
            "/login",
            data={
                "email": "ana@example.com",
                "senha": "senha123"
            }
        )

        self.assertEqual(
            self.client.get(
                "/perfil",
                headers={"Accept": "application/json"}
            ).status_code,
            200
        )

        resposta_logout = self.client.post("/logout")

        self.assertEqual(resposta_logout.status_code, 200)

        self.assertEqual(
            len(self.sql("SELECT * FROM sessoes")),
            0
        )

        resposta_perfil = self.client.get(
            "/perfil",
            headers={"Accept": "application/json"}
        )

        self.assertEqual(resposta_perfil.status_code, 401)

    def test_sessao_expirada_nao_permite_acesso(self):
        self.cadastrar_usuario()

        self.client.post(
            "/login",
            data={
                "email": "ana@example.com",
                "senha": "senha123"
            }
        )

        sessao = self.sql("SELECT * FROM sessoes")[0]

        self.sql(
            "UPDATE sessoes SET expira_em = ? WHERE id = ?",
            ("2000-01-01T00:00:00+00:00", sessao["id"])
        )

        resposta = self.client.get(
            "/perfil",
            headers={"Accept": "application/json"}
        )

        self.assertEqual(resposta.status_code, 401)

        self.assertEqual(
            len(self.sql("SELECT * FROM sessoes")),
            0
        )

    def test_cookie_de_sessao_tem_propriedades_de_seguranca(self):
        self.cadastrar_usuario()

        resposta = self.client.post(
            "/login",
            data={
                "email": "ana@example.com",
                "senha": "senha123"
            }
        )

        self.assertEqual(resposta.status_code, 200)

        cookies = resposta.headers.getlist("Set-Cookie")

        cookie_sessao = next(
            cookie for cookie in cookies
            if "avaliaai_session=" in cookie
        )

        self.assertIn("HttpOnly", cookie_sessao)
        self.assertIn("Secure", cookie_sessao)
        self.assertIn("SameSite=Lax", cookie_sessao)


if __name__ == "__main__":
    unittest.main()