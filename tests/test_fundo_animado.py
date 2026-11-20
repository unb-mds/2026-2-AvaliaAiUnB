"""Garante o fundo animado dentro das regras de acessibilidade e da CSP do projeto."""
import re
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "app" / "static" / "fundo-animado.js"
TEMPLATES = RAIZ / "app" / "templates"

CANVAS = re.compile(r"<canvas\b[^>]*\bclass=\"[^\"]*\bfundo-animado\b[^\"]*\"[^>]*>")
CARREGA_SCRIPT = re.compile(
    r"<script\b[^>]*\bsrc=\"\{\{\s*url_for\(\s*'static'\s*,\s*filename\s*=\s*'fundo-animado\.js'\s*\)\s*\}\}\""
)


class TestFundoAnimadoScript(unittest.TestCase):
    def setUp(self):
        self.codigo = SCRIPT.read_text(encoding="utf-8")

    def test_respeita_movimento_reduzido_e_pausa_quando_nao_visivel(self):
        for trecho in ("prefers-reduced-motion", "visibilitychange", "IntersectionObserver"):
            with self.subTest(trecho=trecho):
                self.assertIn(trecho, self.codigo)

    def test_nao_usa_recursos_inseguros_nem_urls_externas(self):
        for proibido in ("eval(", "new Function", "innerHTML", "http://", "https://"):
            with self.subTest(proibido=proibido):
                self.assertNotIn(proibido, self.codigo)


class TestFundoAnimadoTemplates(unittest.TestCase):
    def test_todo_template_com_canvas_carrega_o_script_e_esconde_do_leitor_de_tela(self):
        com_canvas = []
        for caminho in sorted(TEMPLATES.glob("*.html")):
            texto = caminho.read_text(encoding="utf-8")
            canvases = CANVAS.findall(texto)
            if not canvases:
                continue
            com_canvas.append(caminho.name)
            with self.subTest(template=caminho.name):
                self.assertRegex(texto, CARREGA_SCRIPT, "falta o <script> via url_for")
                for tag in canvases:
                    self.assertIn('aria-hidden="true"', tag)

        self.assertEqual(com_canvas, [], "O modelo editorial substitui o fundo de partículas")


if __name__ == "__main__":
    unittest.main()
