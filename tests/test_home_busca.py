"""Busca por nome no cabeçalho da home: aponta para a Consulta e usa o mesmo parâmetro GET."""
import re
import unittest

from app import create_app
from app.routes.professor_routes import CAMPOS_FILTRO
from tests.fake_supabase import ClienteFalso


class TestHomeBusca(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.web = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                               'SUPABASE_CLIENT': self.cliente}).test_client()

    def html(self, caminho):
        resposta = self.web.get(caminho, headers={'Accept': 'text/html'})
        self.assertEqual(resposta.status_code, 200, caminho)
        return resposta.get_data(as_text=True)

    def formulario_de_busca(self):
        html = self.html('/')
        for abertura, corpo in re.findall(r'(<form\b[^>]*>)(.*?)</form>', html, re.DOTALL):
            if 'method="get"' in abertura:
                return abertura, corpo
        self.fail('A home não tem formulário method="get"')

    def test_home_tem_formulario_get_para_a_consulta(self):
        abertura, corpo = self.formulario_de_busca()
        self.assertIn('action="/professores"', abertura)
        self.assertIn('<button type="submit"', corpo)

    def test_campo_usa_o_parametro_de_nome_da_consulta(self):
        _, corpo = self.formulario_de_busca()
        campo = re.search(r'<input\b[^>]*\btype="search"[^>]*>', corpo)
        self.assertIsNotNone(campo, 'Falta o input de busca')
        nome = re.search(r'\bname="([^"]+)"', campo.group(0)).group(1)
        self.assertEqual(nome, 'nome')
        self.assertIn(nome, CAMPOS_FILTRO)

    def test_campo_tem_rotulo_associado(self):
        _, corpo = self.formulario_de_busca()
        self.assertRegex(corpo, r'<label\b[^>]*\bfor="busca-nome"')
        self.assertIn('id="busca-nome"', corpo)

    def test_consulta_aceita_o_parametro_de_nome(self):
        self.html('/professores?nome=Ana')


if __name__ == '__main__':
    unittest.main()
