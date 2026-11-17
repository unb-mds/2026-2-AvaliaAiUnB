import unittest

from app.utils import normalizar_busca
from app.validacoes import CRITERIOS, validar_avaliacao, validar_comentario


class TestAvaliacao(unittest.TestCase):
    def test_notas_validas_e_invalidas(self):
        notas, erros = validar_avaliacao({c: '4' for c in CRITERIOS})
        self.assertEqual((erros, set(notas.values())), ({}, {4}))
        for invalido in ('0', '6', 'x', '', '4.5'):
            _, erros = validar_avaliacao({**{c: '4' for c in CRITERIOS}, 'clareza': invalido})
            self.assertEqual(list(erros), ['clareza'])


class TestComentario(unittest.TestCase):
    def test_um_caractere_e_recusado(self):
        _, erro = validar_comentario('a')
        self.assertIn('pelo menos 2', erro)

    def test_dois_caracteres_passam(self):
        self.assertEqual(validar_comentario('ok'), ('ok', None))

    def test_mil_passam_e_mil_e_um_nao(self):
        self.assertIsNone(validar_comentario('a' * 1000)[1])
        _, erro = validar_comentario('a' * 1001)
        self.assertIn('no máximo 1000', erro)

    def test_vazio_nulo_e_so_espacos_sao_recusados(self):
        for texto in ('', '   ', '\t\n  \r\n', None):
            with self.subTest(texto=texto):
                self.assertIsNotNone(validar_comentario(texto)[1])

    def test_espacos_das_extremidades_nao_contam(self):
        self.assertEqual(validar_comentario('  oi \n'), ('oi', None))
        self.assertIsNotNone(validar_comentario('  a  ')[1])
        self.assertIsNone(validar_comentario(' ' + 'a' * 1000 + ' ')[1])

    def test_quebra_crlf_conta_como_um_caractere(self):
        texto, erro = validar_comentario('a\r\nb')
        self.assertEqual((texto, erro), ('a\nb', None))
        # 499 + CRLF + 500 = 1000 caracteres depois de normalizar (1001 se contasse 2).
        self.assertIsNone(validar_comentario('a' * 499 + '\r\n' + 'b' * 500)[1])
        self.assertIsNotNone(validar_comentario('a' * 500 + '\r\n' + 'b' * 500)[1])

    def test_html_e_tratado_como_texto_sem_alteracao(self):
        texto, erro = validar_comentario('<script>alert(1)</script> **negrito**')
        self.assertEqual((texto, erro), ('<script>alert(1)</script> **negrito**', None))


class TestBusca(unittest.TestCase):
    def test_normalizar(self):
        self.assertEqual(normalizar_busca(' JOSÉ  Ávila '), 'joseavila')


if __name__ == '__main__':
    unittest.main()
