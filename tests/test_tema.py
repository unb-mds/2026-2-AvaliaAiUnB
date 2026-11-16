"""Garante o botão de tema: script no <head> de todas as páginas, JS seguro e botão acessível."""
import re
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parent.parent
TEMPLATES = RAIZ / "app" / "templates"
SCRIPT = RAIZ / "app" / "static" / "tema.js"
PARCIAL = TEMPLATES / "_tema.html"

HEAD = re.compile(r"<head\b[^>]*>(.*?)</head>", re.DOTALL | re.IGNORECASE)


class TestTemaTemplates(unittest.TestCase):
    def test_toda_pagina_completa_inclui_o_parcial_de_tema_no_head(self):
        paginas = []
        for caminho in sorted(TEMPLATES.glob("*.html")):
            if caminho.name.startswith("_"):
                continue
            texto = caminho.read_text(encoding="utf-8")
            head = HEAD.search(texto)
            if not head:
                continue
            paginas.append(caminho.name)
            with self.subTest(template=caminho.name):
                self.assertIn("{% include '_tema.html' %}", head.group(1))

        self.assertTrue(paginas, "Nenhuma página completa encontrada")

    def test_parcial_carrega_o_script_sem_defer_nem_async(self):
        texto = PARCIAL.read_text(encoding="utf-8")
        self.assertIn("url_for('static', filename='tema.js')", texto)
        self.assertNotIn("defer", texto)
        self.assertNotIn("async", texto)
        self.assertNotIn("<script>", texto)  # nada de script inline (CSP)

    def test_topo_tem_o_botao_de_tema_acessivel(self):
        topo = (TEMPLATES / "_topo.html").read_text(encoding="utf-8")
        botao = re.search(r"<button\b[^>]*\bclass=\"[^\"]*\bbotao-tema\b[^\"]*\"[^>]*>", topo)
        self.assertIsNotNone(botao, "Botão .botao-tema não encontrado em _topo.html")
        self.assertIn("aria-pressed=", botao.group(0))
        self.assertIn("aria-label=", botao.group(0))


class TestTemaScript(unittest.TestCase):
    def setUp(self):
        self.codigo = SCRIPT.read_text(encoding="utf-8")

    def test_nao_usa_recursos_inseguros_nem_urls_externas(self):
        for proibido in ("eval(", "new Function", "innerHTML", "http://", "https://"):
            with self.subTest(proibido=proibido):
                self.assertNotIn(proibido, self.codigo)

    def test_acessa_local_storage_apenas_dentro_de_try(self):
        codigo = re.sub(r"/\*.*?\*/|//[^\n]*", "", self.codigo, flags=re.DOTALL)  # ignora comentários
        usos = len(re.findall(r"localStorage", codigo))
        usos_em_try = len(re.findall(r"try\s*\{[^}]*localStorage", codigo))
        self.assertGreater(usos, 0)
        self.assertEqual(usos, usos_em_try, "Há acesso a localStorage fora de try/catch")

    def test_nao_segue_o_tema_do_sistema(self):
        self.assertNotIn("prefers-color-scheme", self.codigo)


if __name__ == "__main__":
    unittest.main()
