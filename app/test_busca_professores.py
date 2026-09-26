"""Testes da issue #42: casos de borda da busca de professores."""
import unittest

from app.repositorio import ProfessorRepository
from app.test_implementacao import BancoIsolado


class TestBordasFiltrarProfessores(BancoIsolado):
    def filtrar(self, **filtros):
        with self.app.app_context():
            return [p['nome'] for p in ProfessorRepository().filtrar(**filtros)]

    def test_professor_com_muitas_disciplinas_aparece_uma_vez(self):
        self.sql('INSERT INTO professores VALUES (?, ?, ?)', (1, 'Ana Silva', 'CIC'))
        for did in range(1, 6):
            self.sql('INSERT INTO disciplinas VALUES (?, ?, ?)', (did, f'Tópico {did}', f'MDS{did}'))
            self.sql('INSERT INTO professor_disciplinas VALUES (?, ?)', (1, did))

        self.assertEqual(self.filtrar(disciplina='MDS'), ['Ana Silva'])
        self.assertEqual(self.filtrar(disciplina='tópico 3'), ['Ana Silva'])

    def test_disciplina_inexistente_nao_retorna_ninguem(self):
        self.catalogo()

        self.assertEqual(self.filtrar(disciplina='XYZ999'), [])
        self.assertEqual(self.filtrar(nome='professor 1', disciplina='XYZ999'), [])

    def test_professor_sem_disciplinas_so_aparece_na_busca_por_nome(self):
        self.catalogo()
        self.sql('INSERT INTO professores VALUES (?, ?, ?)', (3, 'Professor 3', 'FCTE'))

        self.assertEqual(self.filtrar(nome='professor 3'), ['Professor 3'])
        self.assertEqual(self.filtrar(nome='professor 3', disciplina='MDS'), [])
        self.assertNotIn('Professor 3', self.filtrar(disciplina='MDS'))

    def test_tab_e_quebra_de_linha_nas_pontas_sao_ignorados(self):
        self.catalogo()

        self.assertEqual(self.filtrar(nome='\tprofessor 1\n', disciplina='\nmds20\t'), ['Professor 1'])
        self.assertEqual(self.filtrar(nome='\t\n', disciplina='\n\t'), ['Professor 1', 'Professor 2'])

    def test_aspas_e_comandos_sql_sao_texto_e_nao_alteram_o_banco(self):
        self.catalogo()

        for termo in ("' OR 1=1 --", '"; DROP TABLE professores;--', "'); DELETE FROM professores;--"):
            with self.subTest(termo=termo):
                self.assertEqual(self.filtrar(nome=termo), [])
                self.assertEqual(self.filtrar(disciplina=termo), [])

        self.assertEqual(self.filtrar(), ['Professor 1', 'Professor 2'])

    def test_apostrofo_no_nome_e_encontrado(self):
        self.sql('INSERT INTO professores VALUES (?, ?, ?)', (1, "Maria D'Ávila", 'CIC'))

        self.assertEqual(self.filtrar(nome="d'Ávila"), ["Maria D'Ávila"])

    def test_emoji_e_termo_muito_longo_nao_quebram_a_busca(self):
        self.catalogo()

        for termo in ('😀', 'a' * 10_000):
            with self.subTest(termo=termo[:10]):
                self.assertEqual(self.filtrar(nome=termo), [])
                self.assertEqual(self.filtrar(disciplina=termo), [])

    def test_filtro_de_nome_nao_casa_com_o_departamento(self):
        self.sql('INSERT INTO professores VALUES (?, ?, ?)', (1, 'Ana Silva', 'CIC'))

        self.assertEqual(self.filtrar(nome='CIC'), [])

    def test_homonimos_saem_ordenados_por_id(self):
        for pid in (3, 1, 2):
            self.sql('INSERT INTO professores VALUES (?, ?, ?)', (pid, 'Ana Silva', f'DEP{pid}'))

        with self.app.app_context():
            ids = [p['id'] for p in ProfessorRepository().filtrar(nome='ana')]

        self.assertEqual(ids, [1, 2, 3])

    # Comportamento esperado ainda não atendido: o LIKE ... COLLATE NOCASE do SQLite só
    # ignora caixa em ASCII e não há normalização de espaços internos.
    def test_ignora_caixa_de_letras_acentuadas(self):
        self.sql('INSERT INTO professores VALUES (?, ?, ?)', (1, 'José Álvaro', 'CIC'))

        self.assertEqual(self.filtrar(nome='JOSÉ ÁLVARO'), ['José Álvaro'])

    def test_busca_sem_acento_encontra_nome_e_disciplina_acentuados(self):
        self.sql('INSERT INTO professores VALUES (?, ?, ?)', (1, 'José Álvaro', 'CIC'))
        self.sql('INSERT INTO disciplinas VALUES (?, ?, ?)', (1, 'Cálculo 1', 'MAT001'))
        self.sql('INSERT INTO professor_disciplinas VALUES (?, ?)', (1, 1))

        self.assertEqual(self.filtrar(nome='jose alvaro'), ['José Álvaro'])
        self.assertEqual(self.filtrar(disciplina='calculo'), ['José Álvaro'])

    def test_espacos_internos_repetidos_sao_normalizados(self):
        self.sql('INSERT INTO professores VALUES (?, ?, ?)', (1, 'Ana Silva', 'CIC'))

        self.assertEqual(self.filtrar(nome='Ana   Silva'), ['Ana Silva'])


class TestBordasPaginaBusca(BancoIsolado):
    def pagina(self, query_string):
        resposta = self.client.get('/professores', query_string=query_string)
        return resposta, resposta.get_data(as_text=True)

    def test_nome_e_disciplina_juntos_exigem_os_dois(self):
        self.catalogo()  # Professor 1: MDS10 e MDS20; Professor 2: só MDS10

        _, html = self.pagina({'nome': 'professor', 'disciplina': 'MDS20'})
        self.assertIn('Professor 1', html)
        self.assertNotIn('Professor 2', html)

        _, html = self.pagina({'nome': 'professor 2', 'disciplina': 'MDS20'})
        self.assertNotIn('Professor 1', html)
        self.assertNotIn('Professor 2', html)
        self.assertIn('Nenhum professor encontrado', html)

    def test_curingas_na_query_string_sao_texto(self):
        self.sql('INSERT INTO professores VALUES (?, ?, ?)', (1, 'Ana 100%', 'CIC'))
        self.sql('INSERT INTO professores VALUES (?, ?, ?)', (2, 'Ana_Maria', 'CIC'))
        self.sql('INSERT INTO professores VALUES (?, ?, ?)', (3, 'Ana Souza', 'CIC'))

        for busca, esperado, ausentes in (('%', 'Ana 100%', ('Ana_Maria', 'Ana Souza')),
                                          ('_', 'Ana_Maria', ('Ana 100%', 'Ana Souza'))):
            with self.subTest(busca=busca):
                resposta, html = self.pagina({'nome': busca})

                self.assertEqual(resposta.status_code, 200)
                self.assertIn(esperado, html)
                for ausente in ausentes:
                    self.assertNotIn(ausente, html)

    def test_parametro_repetido_ou_desconhecido_nao_gera_erro(self):
        self.catalogo()

        for query in ('nome=professor&nome=inexistente', 'nome=professor&outro=1', 'so_desconhecido=x'):
            with self.subTest(query=query):
                resposta, html = self.pagina(query)

                self.assertEqual(resposta.status_code, 200)
                self.assertIn('Professor 1', html)

    def test_nome_com_html_aparece_escapado_no_resultado(self):
        self.sql('INSERT INTO professores VALUES (?, ?, ?)', (1, '<script>alert(1)</script>', 'CIC'))

        _, html = self.pagina({'nome': 'script'})

        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', html)
        self.assertNotIn('<script>alert(1)', html)


if __name__ == '__main__':
    unittest.main()
