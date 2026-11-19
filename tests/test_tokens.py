"""Garante que todo token CSS usado com var(--nome) esteja definido no :root de base.css."""
import re
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parent.parent
ESTATICOS = RAIZ / "app" / "static"
BASE_CSS = ESTATICOS / "base.css"

COMENTARIO = re.compile(r"/\*.*?\*/", re.DOTALL)
BLOCO_ROOT = re.compile(r":root[^{]*\{([^{}]*)\}")
DEFINICAO = re.compile(r"(--[\w-]+)\s*:")
USO_SEM_RESERVA = re.compile(r"var\(\s*(--[\w-]+)\s*\)")


def ler_css(caminho):
    return COMENTARIO.sub("", caminho.read_text(encoding="utf-8"))


def tokens_definidos_no_root(texto):
    definidos = set()
    for bloco in BLOCO_ROOT.findall(texto):
        definidos.update(DEFINICAO.findall(bloco))
    return definidos


class TestTokensCss(unittest.TestCase):
    def test_tokens_usados_estao_definidos_no_root_da_base(self):
        definidos = tokens_definidos_no_root(ler_css(BASE_CSS))
        definidos.update(tokens_definidos_no_root(ler_css(ESTATICOS / "modelo-editorial.css")))
        self.assertTrue(definidos, "Nenhum token encontrado no :root de base.css")

        faltando = []
        for caminho in sorted(ESTATICOS.glob("*.css")):
            texto = ler_css(caminho)
            locais = set(DEFINICAO.findall(texto))  # declarados em qualquer seletor do próprio arquivo
            for token in sorted(set(USO_SEM_RESERVA.findall(texto))):
                if token not in definidos and token not in locais:
                    faltando.append(f"{token} (usado em {caminho.name})")

        self.assertEqual(
            [],
            faltando,
            "Tokens usados mas não definidos no :root de base.css nem no próprio arquivo: "
            + "; ".join(faltando),
        )


if __name__ == "__main__":
    unittest.main()
