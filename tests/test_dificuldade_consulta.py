"""Dificuldade média e quantidade de avaliações por disciplina na lista de Consulta (issue #201)."""
import re
import unittest

from app import create_app
from app.controllers import professor_controller as controller
from app.validacoes import CRITERIOS
from tests.fake_supabase import ClienteFalso, Consulta


class ClienteContador(ClienteFalso):
    """Conta as consultas feitas à tabela de avaliações."""

    def __init__(self):
        super().__init__()
        self.consultas_avaliacoes = 0

    def table(self, nome):
        if nome == 'avaliacoes':
            self.consultas_avaliacoes += 1
        return Consulta(self.tabelas, nome, self.upserts)


def avaliacao(professor_id, disciplina_id, dificuldade, **extra):
    return {'id': 0, 'usuario_id': 'u', 'professor_id': professor_id,
            'disciplina_id': disciplina_id, 'ano': 2026, 'periodo': 1,
            **{c: 4 for c in CRITERIOS}, 'dificuldade': dificuldade, **extra}


class BaseConsulta(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteContador()
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                               'SUPABASE_CLIENT': self.cliente})

    def avaliar(self, professor_id, disciplina_id, *dificuldades, **extra):
        tabela = self.cliente.tabelas['avaliacoes']
        for d in dificuldades:
            tabela.append({**avaliacao(professor_id, disciplina_id, d, **extra), 'id': len(tabela) + 1})

    def dificuldades(self, pagina=None, **filtros):
        with self.app.app_context():
            catalogo = controller.catalogo(**filtros)
            self.cliente.consultas_avaliacoes = 0
            return controller.dificuldades_da_pagina(catalogo, pagina)


class TestDificuldadePorDisciplina(BaseConsulta):
    def setUp(self):
        super().setUp()
        # Professor 1 passa a dar duas disciplinas (10 e 11).
        self.cliente.tabelas['vw_professor_disciplina'].append(
            {'professor_id': 1, 'disciplina_id': 11, 'codigo_disciplina': 'FGA0003',
             'disciplina': 'ÁLGEBRA', 'ano': 2026, 'periodo': 1})

    def test_disciplinas_do_mesmo_professor_sao_independentes(self):
        self.avaliar(1, 10, 1, 2)       # média 1,5
        self.avaliar(1, 11, 5)          # média 5
        resultado = self.dificuldades()[1]

        self.assertEqual(resultado[10]['valor'], 1.5)
        self.assertEqual(resultado[10]['texto_avaliacoes'], '2 avaliações')
        self.assertEqual(resultado[11]['valor'], 5.0)
        self.assertEqual(resultado[11]['texto_avaliacoes'], '1 avaliação')

    def test_professores_diferentes_nao_se_misturam(self):
        self.avaliar(1, 10, 2)
        self.avaliar(2, 20, 4)
        resultado = self.dificuldades()

        self.assertEqual(resultado[1][10]['valor'], 2.0)
        self.assertEqual(resultado[2][20]['valor'], 4.0)

    def test_disciplina_sem_avaliacao_fica_sem_numero(self):
        self.avaliar(1, 10, 3)
        resultado = self.dificuldades()[1]

        self.assertIsNone(resultado[11]['valor'])
        self.assertIsNone(resultado[11]['texto_dificuldade'])
        self.assertEqual(resultado[11]['texto_avaliacoes'], '0 avaliações')
        self.assertEqual(self.dificuldades()[3], {})   # professor sem disciplinas

    def test_avaliacao_com_nota_nula_nao_conta_nem_entra_na_media(self):
        self.avaliar(1, 10, 4)
        self.avaliar(1, 10, None)       # como a página do professor: ignorada
        resultado = self.dificuldades()[1][10]

        self.assertEqual(resultado['valor'], 4.0)
        self.assertEqual(resultado['texto_avaliacoes'], '1 avaliação')

    def test_so_nulas_fica_sem_numero(self):
        self.avaliar(1, 10, None)
        resultado = self.dificuldades()[1][10]

        self.assertIsNone(resultado['valor'])
        self.assertEqual(resultado['texto_avaliacoes'], '0 avaliações')


class TestTextos(BaseConsulta):
    def test_singular_e_plural(self):
        self.avaliar(1, 10, 3)
        self.avaliar(2, 20, 3, ), self.avaliar(2, 20, 4)
        resultado = self.dificuldades()

        self.assertEqual(resultado[1][10]['texto_avaliacoes'], '1 avaliação')
        self.assertEqual(resultado[2][20]['texto_avaliacoes'], '2 avaliações')

    def test_arredondamento_a_uma_casa_com_virgula(self):
        self.avaliar(1, 10, 2, 2, 3)    # 2,333... -> 2,3
        self.avaliar(2, 20, 4, 4, 5)    # 4,333... -> 4,3
        resultado = self.dificuldades()

        self.assertEqual(resultado[1][10]['valor'], 2.3)
        self.assertEqual(resultado[1][10]['texto_dificuldade'], 'Dificuldade 2,3/5')
        self.assertEqual(resultado[2][20]['texto_dificuldade'], 'Dificuldade 4,3/5')

    def test_meio_arredonda_para_cima_como_a_pagina_do_professor(self):
        self.avaliar(1, 10, 2, 3, 3, 4, 4, 4, 4, 4)   # 28/8 = 3,5 exato
        self.avaliar(2, 20, 1, 1, 1, 2)               # 1,25 -> 1,3
        resultado = self.dificuldades()

        self.assertEqual(resultado[1][10]['texto_dificuldade'], 'Dificuldade 3,5/5')
        self.assertEqual(resultado[2][20]['texto_dificuldade'], 'Dificuldade 1,3/5')


class TestIgualAPaginaDoProfessor(BaseConsulta):
    def test_mesmo_valor_que_a_pagina_do_professor(self):
        self.avaliar(1, 10, 2, 2, 3)
        self.avaliar(1, 10, 4, 1, 5)
        valor = self.dificuldades()[1][10]['valor']

        html = self.app.test_client().get('/professores/1?disciplina_id=10').get_data(as_text=True)
        rotulo = re.search(r'aria-label="Dificuldade ([\d,]+) de 5', html).group(1)
        quantidade = re.search(r'· (\d+) avaliações', html).group(1)

        self.assertEqual(str(valor).replace('.', ','), rotulo)
        self.assertEqual(self.dificuldades()[1][10]['texto_avaliacoes'], f'{quantidade} avaliações')

    def test_mesma_regra_da_media_do_repositorio(self):
        self.avaliar(1, 10, 2, 5, 4)
        with self.app.app_context():
            exata = controller.indicadores(1, 10)['medias']['dificuldade']
        self.assertEqual(self.dificuldades()[1][10]['valor'], round(exata + 1e-9, 1))


class TestUmaConsultaSo(BaseConsulta):
    def consultas_com(self, quantidade):
        self.cliente.tabelas['professores'] = [
            {'id': i, 'nome': f'PROFESSOR {i:03d}', 'departamento': 'FCTE'}
            for i in range(1, quantidade + 1)]
        self.cliente.tabelas['vw_professor_disciplina'] = [
            {'professor_id': i, 'disciplina_id': 10 + i, 'codigo_disciplina': f'FGA{i:04d}',
             'disciplina': f'DISC {i}', 'ano': 2026, 'periodo': 1}
            for i in range(1, quantidade + 1)]
        self.cliente.tabelas['avaliacoes'] = []
        for i in range(1, quantidade + 1):
            self.avaliar(i, 10 + i, 3)
        self.app.extensions['repositorios'].professores.invalidar_cache()
        resultado = self.dificuldades()
        self.assertEqual(len(resultado), min(quantidade, 100))
        return self.cliente.consultas_avaliacoes

    def test_numero_de_consultas_nao_cresce_com_os_professores(self):
        self.assertEqual(self.consultas_com(3), 1)
        self.assertEqual(self.consultas_com(60), 1)

    def test_so_calcula_para_os_professores_da_pagina(self):
        self.consultas_com(120)
        pagina_2 = self.dificuldades(pagina='2')

        self.assertEqual(len(pagina_2), 20)     # 100 na 1ª página, 20 na 2ª
        self.assertEqual(len(self.dificuldades(pagina='abc')), 100)


if __name__ == '__main__':
    unittest.main()
