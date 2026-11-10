"""Garante a padronização do nome público nas páginas, sem renomear identificadores."""
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parent.parent
TEMPLATES = RAIZ / "app" / "templates"


class TestIdentidadeVisual(unittest.TestCase):
    def test_telas_nao_exibem_nome_antigo(self):
        for caminho in sorted(TEMPLATES.glob("*.html")):
            with self.subTest(tela=caminho.name):
                self.assertNotIn("AvaliaAi", caminho.read_text(encoding="utf-8"))

    def test_identidade_publica_presente_nas_telas_principais(self):
        for nome in ("index.html", "login.html", "cadastro.html", "perfil.html"):
            with self.subTest(tela=nome):
                texto = (TEMPLATES / nome).read_text(encoding="utf-8")
                self.assertIn("AvaliaUnb", texto)

    def test_urls_e_identificadores_tecnicos_permanecem_originais(self):
        readme = (RAIZ / "README.md").read_text(encoding="utf-8")
        self.assertIn("https://github.com/unb-mds/2026-2-AvaliaAiUnB", readme)
        self.assertIn("cd 2026-2-AvaliaAiUnB", readme)
