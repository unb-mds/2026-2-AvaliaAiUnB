"""Estilos do autocompletar (campo-busca.js) carregados pelas telas que o usam.

A mescla da nova interface (#246) apagou essas regras do base.css e a lista de
sugestões passou a aparecer sem estilo (com marcadores e textos colados) na
Consulta e na Comparação."""
import re
import unittest
from pathlib import Path

from app import create_app
from tests.fake_supabase import ClienteFalso

ESTATICOS = Path(__file__).resolve().parent.parent / 'app' / 'static'
CLASSES = ('.campo-sugestoes', '.lista-sugestoes', '.sugestao', '.sugestao-texto',
           '.sugestao-detalhe', '.sugestao-tipo', '.sugestao-disciplinas')


class TestEstiloSugestoes(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                               'SUPABASE_CLIENT': ClienteFalso()})
        self.web = self.app.test_client()

    def css_da_pagina(self, caminho):
        html = self.web.get(caminho, headers={'Accept': 'text/html'}).get_data(as_text=True)
        arquivos = re.findall(r'href="/static/([^"?]+\.css)', html)
        return '\n'.join((ESTATICOS / nome).read_text(encoding='utf-8') for nome in arquivos)

    def test_telas_com_autocompletar_carregam_os_estilos(self):
        for caminho in ('/comparar', '/comparar?modo=livre', '/professores', '/'):
            css = self.css_da_pagina(caminho)
            for classe in CLASSES:
                with self.subTest(caminho=caminho, classe=classe):
                    self.assertRegex(css, re.escape(classe) + r'\b[^{]*\{')

    def test_lista_flutua_sem_marcadores(self):
        css = self.css_da_pagina('/comparar')
        regra = re.search(r'\.lista-sugestoes\s*\{([^}]*)\}', css).group(1)
        self.assertIn('position: absolute', regra)
        self.assertIn('list-style: none', regra)


if __name__ == '__main__':
    unittest.main()
