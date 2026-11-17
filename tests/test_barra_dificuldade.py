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


class BaseDificuldade(unittest.TestCase):
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


class TestFormularioDificuldade(BaseDificuldade):
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


class TestVisualizacaoDificuldade(BaseDificuldade):
    """Perfil do professor, perfil do usuário e comparação exibem a barra estilo HP."""

    ROTULO = 'aria-label="Dificuldade {} de 5 (1 = muito fácil, 5 = muito difícil)"'

    def setUp(self):
        super().setUp()
        # Duas avaliações do professor 1 / disciplina 10 com dificuldades 3 e 4 -> média 3,5
        notas = {**{c: '4' for c in CRITERIOS}, 'dificuldade': '3', 'disciplina_id': '10'}
        self.assertEqual(self.postar('/avaliar/1', notas).status_code, 303)
        self.postar('/logout', {})
        entrar_pela_web(self.web, self.cliente, 'bruno@gmail.com', 'Bruno')
        self.assertEqual(self.postar('/avaliar/1', {**notas, 'dificuldade': '4'}).status_code, 303)

    @staticmethod
    def preenchimento(html):
        """Classes (largura, nível) do preenchimento da primeira barra de dificuldade."""
        return re.search(r'class="barra-hp-cheia preenche-(\d+) nivel-(\d)"', html).groups()

    def test_perfil_do_professor_usa_media_exata_e_cor_do_nivel(self):
        html = self.web.get('/professores/1?disciplina_id=10').get_data(as_text=True)

        self.assertIn(self.ROTULO.format('3,5'), html)
        self.assertEqual(self.preenchimento(html), ('70', '4'))  # 3,5/5 = 70%; arredonda p/ nível 4
        self.assertNotIn('3,5 / 5', html)  # só a barra e a escala, sem o valor em texto
        self.assertIn('<span>1</span><span>2</span><span>3</span><span>4</span><span>5</span>', html)
        self.assertNotIn('style=', html)

    def test_perfil_do_usuario_mostra_barra_da_propria_nota(self):
        html = self.web.get('/perfil', headers={'Accept': 'text/html'}).get_data(as_text=True)

        self.assertIn(self.ROTULO.format('4'), html)
        self.assertEqual(self.preenchimento(html), ('80', '4'))
        self.assertNotIn('4/5', html)
        self.assertIn('barra-hp-escala', html)

    def test_comparacao_mostra_barra_na_linha_da_dificuldade(self):
        html = self.web.get('/comparar?professor_1=1&professor_2=2').get_data(as_text=True)

        self.assertEqual(html.count('class="barra-hp-trilho"'), 1)  # professor 2 não tem avaliações
        self.assertIn(self.ROTULO.format('3,5'), html)
        self.assertNotIn('3,50 / 5', html)
        self.assertIn('4,00 / 5', html)  # os outros critérios continuam com o número
        self.assertIn('barra-hp-escala', html)


class TestMacroBarraDificuldade(unittest.TestCase):
    """Cor e largura nos extremos da escala."""

    def setUp(self):
        app = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                          'SUPABASE_CLIENT': ClienteFalso()})
        with app.app_context():
            self.macro = app.jinja_env.get_template('_macros.html').module.barra_dificuldade

    def test_verde_no_facil_vermelho_no_dificil_e_nada_sem_valor(self):
        self.assertIn('preenche-20 nivel-1', str(self.macro(1)))
        self.assertIn('preenche-100 nivel-5', str(self.macro(5)))
        self.assertIn('preenche-48 nivel-2', str(self.macro(2.4)))
        self.assertEqual(str(self.macro(None)).strip(), '')

if __name__ == '__main__':
    unittest.main()
