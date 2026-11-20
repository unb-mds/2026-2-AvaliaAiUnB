"""Garante a padronização do nome público nas páginas, sem renomear identificadores."""
import unittest
from pathlib import Path

from app import create_app
from tests.fake_supabase import ClienteFalso


RAIZ = Path(__file__).resolve().parent.parent
TEMPLATES = RAIZ / "app" / "templates"


class TestIdentidadeVisual(unittest.TestCase):
    def test_telas_nao_exibem_nome_antigo(self):
        for caminho in sorted(TEMPLATES.glob("*.html")):
            with self.subTest(tela=caminho.name):
                self.assertNotIn("AvaliaAi", caminho.read_text(encoding="utf-8"))

    def test_identidade_publica_presente_nas_telas_principais(self):
        for nome in ("index.html", "login.html", "perfil.html"):
            with self.subTest(tela=nome):
                texto = (TEMPLATES / nome).read_text(encoding="utf-8")
                self.assertIn("AvaliaUnb", texto)

    def test_urls_e_identificadores_tecnicos_permanecem_originais(self):
        readme = (RAIZ / "README.md").read_text(encoding="utf-8")
        self.assertIn("https://github.com/unb-mds/2026-2-AvaliaUnB", readme)
        self.assertIn("cd 2026-2-AvaliaUnB", readme)


class TestLogo(unittest.TestCase):
    """A logo (docs/logo) aparece no topo, no login e como favicon, seguindo o tema."""

    def setUp(self):
        app = create_app({'TESTING': True, 'SECRET_KEY': 'teste-logo',
                          'SUPABASE_CLIENT': ClienteFalso()})
        self.web = app.test_client()

    def test_topo_e_login_usam_a_logo_com_cores_por_classe(self):
        for caminho in ('/', '/sobre', '/login'):
            with self.subTest(tela=caminho):
                html = self.web.get(caminho).get_data(as_text=True)
                self.assertIn('Avalia<span class="logo-destaque">UnB</span>', html)
                # Tema escuro: capelo branco da nova interface (PNG)
                self.assertIn('class="logo-simbolo logo-tema-escuro" src="/static/logo-chapeu-modelo.png"', html)
                # Tema claro: desenho vetorial antigo, cores pelos tokens --cor-logo-*
                simbolo = html.split('class="logo-simbolo logo-tema-claro"')[1].split('</svg>')[0]
                for parte in ('logo-capelo', 'logo-base', 'logo-cordao', 'logo-estrela'):
                    self.assertIn(f'class="{parte}"', simbolo)
                self.assertNotIn('fill="#', simbolo)
                self.assertNotIn('style=', html)

    def test_favicon_em_todas_as_telas_e_servido(self):
        for caminho in ('/', '/login', '/professores', '/ranking', '/sobre'):
            with self.subTest(tela=caminho):
                self.assertIn('rel="icon" type="image/svg+xml" href="/static/favicon.svg"',
                              self.web.get(caminho).get_data(as_text=True))
        resposta = self.web.get('/static/favicon.svg')
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('image/svg+xml', resposta.content_type)
        resposta.close()

    def test_tokens_da_logo_nos_dois_temas(self):
        css = (RAIZ / 'app' / 'static' / 'base.css').read_text(encoding='utf-8')
        claro = css[css.index(':root[data-theme="light"]'):]
        for token in ('--cor-logo-texto', '--cor-logo-destaque', '--cor-logo-capelo',
                      '--cor-logo-base', '--cor-logo-estrela', '--cor-logo-contorno'):
            with self.subTest(token=token):
                self.assertIn(f'{token}:', css[:css.index(':root[data-theme="light"]')])
                self.assertIn(f'{token}:', claro)
