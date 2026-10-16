import unittest

from app.utils import normalizar_busca
from app.validacoes import CRITERIOS, validar_avaliacao, validar_cadastro


def formulario(**campos):
    dados = dict(nome='Ana Souza', username='ana.souza', email='ana+uni@gmail.com',
                 senha='senha123', confirmar_senha='senha123')
    dados.update(campos)
    return dados


class TestCadastro(unittest.TestCase):
    def test_valido_normaliza_campos(self):
        dados, erros = validar_cadastro(formulario(nome='  Ana  ', username=' Ana.Souza ',
                                                   email=' Ana@GMAIL.com '))
        self.assertEqual(erros, {})
        self.assertEqual((dados['nome'], dados['username'], dados['email']),
                         ('Ana', 'ana.souza', 'ana@gmail.com'))

    def test_exige_gmail(self):
        for email in ('ana@unb.br', 'ana@hotmail.com', 'ana@gmail.com.br', 'ana@mail.gmail.com'):
            self.assertIn('email', validar_cadastro(formulario(email=email))[1], email)
        self.assertEqual(validar_cadastro(formulario(email='ana@gmail.com'))[1], {})

    def test_email_malformado(self):
        for email in ('', 'ana', '@gmail.com', 'a..b@gmail.com', '.a@gmail.com', 'a b@gmail.com'):
            self.assertIn('email', validar_cadastro(formulario(email=email))[1], email)

    def test_username(self):
        for username in ('', 'ab', 'a' * 31, 'com espaco', 'acentuação', 'a@b'):
            self.assertIn('username', validar_cadastro(formulario(username=username))[1], username)

    def test_nome_e_senha(self):
        self.assertIn('nome', validar_cadastro(formulario(nome='   '))[1])
        self.assertIn('senha', validar_cadastro(formulario(senha='curta', confirmar_senha='curta'))[1])
        self.assertIn('confirmar_senha', validar_cadastro(formulario(confirmar_senha='outra123'))[1])


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
