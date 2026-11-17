"""Barra de crescimento da dificuldade (issue #193): seleção no formulário e leitura."""
import re
import unittest

from flask_wtf.csrf import generate_csrf

from app import create_app
from app.validacoes import CRITERIOS
from tests.fake_supabase import ClienteFalso, entrar_pela_web


def radio_dificuldade(html, nota):
    """Tag <input> do rádio de dificuldade com o valor `nota`."""
    return re.search(rf'<input[^>]*id="dificuldade-{nota}"[^>]*>', html, re.S).group(0)


class TestFormularioDificuldade(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        app = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                          'SUPABASE_CLIENT': self.cliente})
        app.add_url_rule('/teste/csrf', 'teste_csrf', generate_csrf)
        self.web = app.test_client()
        entrar_pela_web(self.web, self.cliente, 'ana@gmail.com', 'Ana')

    def postar(self, caminho, data):
        token = self.web.get('/teste/csrf').get_data(as_text=True)
        return self.web.post(caminho, data={**data, 'csrf_token': token})

    def test_formulario_usa_degraus_so_na_dificuldade_e_mantem_radios(self):
        html = self.web.get('/avaliar/2?disciplina_id=20').get_data(as_text=True)

        self.assertEqual(html.count('degraus-selecao'), 1)
        grupo = html[html.index('degraus-selecao'):]
        grupo = grupo[:grupo.index('</fieldset>')]
        valores = re.findall(r'type="radio"\s+name="dificuldade"\s+id="dificuldade-(\d)"\s+value="(\d)"', grupo)
        self.assertEqual(valores, [(str(n), str(n)) for n in range(1, 6)])
        self.assertIn('1 = Muito fácil', grupo)
        self.assertIn('5 = Muito difícil', grupo)
        self.assertNotIn('style=', html)

    def test_edicao_mostra_degrau_salvo_marcado(self):
        notas = {**{c: '4' for c in CRITERIOS}, 'dificuldade': '3', 'disciplina_id': '10'}
        self.assertEqual(self.postar('/avaliar/1', notas).status_code, 303)
        id_avaliacao = self.cliente.tabelas['avaliacoes'][0]['id']

        html = self.web.get(f'/avaliacoes/{id_avaliacao}/editar',
                            headers={'Accept': 'text/html'}).get_data(as_text=True)

        self.assertIn('checked', radio_dificuldade(html, 3))
        for nota in (1, 2, 4, 5):
            self.assertNotIn('checked', radio_dificuldade(html, nota))


if __name__ == '__main__':
    unittest.main()
