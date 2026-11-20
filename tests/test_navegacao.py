"""Abas do topo (Consulta, Ranking, Sobre, Perfil/Entrar) e página Sobre."""
import re
import unittest

from app import create_app
from tests.fake_supabase import ClienteFalso, entrar_pela_web


def aba_ativa(html):
    encontrada = re.search(r'class="aba" href="[^"]*" aria-current="page">[\s\S]*?<span>([^<]+)</span>', html)
    return encontrada.group(1) if encontrada else None


class TestNavegacao(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.web = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                               'SUPABASE_CLIENT': self.cliente}).test_client()

    def html(self, caminho):
        resposta = self.web.get(caminho, headers={'Accept': 'text/html'})
        self.assertEqual(resposta.status_code, 200, caminho)
        return resposta.get_data(as_text=True)

    def test_abas_para_visitante(self):
        html = self.html('/')
        abas = re.findall(r'class="aba" href="([^"]+)"[^>]*>[\s\S]*?<span>([^<]+)</span>', html)
        self.assertEqual(abas, [('/', 'Início'), ('/professores', 'Explorar'), ('/ranking', 'Ranking'), ('/comparar', 'Comparar'), ('/sobre', 'Sobre')])
        self.assertNotIn('botao-sair', html)
        self.assertEqual(aba_ativa(html), 'Início')

    def test_abas_para_usuario_logado(self):
        entrar_pela_web(self.web, self.cliente)
        html = self.html('/')
        self.assertIn('href="/perfil" aria-current', self.html('/perfil'))
        self.assertRegex(html, r'href="/perfil"[\s\S]*?Perfil')
        self.assertNotIn('>Entrar<', html)
        self.assertIn('botao-sair', html)

    def test_aba_ativa_conforme_a_pagina(self):
        for caminho, esperada in (('/professores', 'Explorar'), ('/professores/1', 'Explorar'),
                                  ('/comparar', 'Comparar'), ('/ranking', 'Ranking'),
                                  ('/sobre', 'Sobre')):
            with self.subTest(caminho=caminho):
                self.assertEqual(aba_ativa(self.html(caminho)), esperada)

    def test_pagina_sobre(self):
        html = self.html('/sobre')
        for trecho in ('Critérios de avaliação', 'Didática', 'Dificuldade', 'conta Google',
                       'Envie seu feedback'):
            self.assertIn(trecho, html)

    def test_pagina_sobre(self):
        html = self.html('/sobre')
        for trecho in ('Critérios de avaliação', 'Didática', 'Dificuldade', 'conta Google',
                       'Envie seu feedback'):
            self.assertIn(trecho, html)

    def test_pagina_sobre_link_repositorio(self):
        html = self.html('/sobre')
        self.assertRegex(
            html,
            r'<a[^>]*href="https://github\.com/unb-mds/2026-2-AvaliaUnB"[^>]*target="_blank"[^>]*rel="noopener noreferrer"[^>]*>',
        )


if __name__ == '__main__':
    unittest.main()

