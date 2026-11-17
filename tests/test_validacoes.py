import unittest

from app.utils import normalizar_busca
from app.validacoes import CRITERIOS, validar_avaliacao


class TestAvaliacao(unittest.TestCase):
    def test_notas_validas_e_invalidas(self):
        notas, erros = validar_avaliacao({c: '4' for c in CRITERIOS})
        self.assertEqual((erros, set(notas.values())), ({}, {4}))
        for invalido in ('0', '6', 'x', '', '4.5'):
            _, erros = validar_avaliacao({**{c: '4' for c in CRITERIOS}, 'clareza': invalido})
            self.assertEqual(list(erros), ['clareza'])


class TestBusca(unittest.TestCase):
    def test_normalizar(self):
        self.assertEqual(normalizar_busca(' JOSÉ  Ávila '), 'joseavila')


if __name__ == '__main__':
    unittest.main()
