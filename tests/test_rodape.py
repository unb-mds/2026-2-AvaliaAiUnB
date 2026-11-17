import unittest
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent.parent / "app" / "templates"


class TestRodape(unittest.TestCase):
    def test_paginas_incluem_rodape(self):
        paginas = [p for p in TEMPLATES.glob("*.html") if not p.name.startswith("_")]
        self.assertTrue(paginas)
        for pagina in paginas:
            with self.subTest(pagina=pagina.name):
                texto = pagina.read_text(encoding="utf-8")
                self.assertIn("_rodape.html", texto)

    def test_link_de_feedback_seguro(self):
        texto = (TEMPLATES / "_rodape.html").read_text(encoding="utf-8")
        self.assertIn('target="_blank"', texto)
        self.assertIn('rel="noopener noreferrer"', texto)


if __name__ == "__main__":
    unittest.main()
