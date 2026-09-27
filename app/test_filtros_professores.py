"""Testes da issue #31: filtros de busca por nome do professor e por disciplina."""
import unittest

from app.repositorio import ProfessorRepository
from app.test_implementacao import BancoIsolado


class TestFiltrarProfessores(BancoIsolado):
    def filtrar(self, **filtros):
        with self.app.app_context():
            return [p['nome'] for p in ProfessorRepository().filtrar(**filtros)]

    def test_filtra_por_trecho_do_nome_ignorando_caixa(self):
        for pid, nome in ((1, 'Carlos Lima'), (2, 'Ana Silva'), (3, 'Bruno Silveira')):
            self.sql('INSERT INTO professores VALUES (?, ?, ?)', (pid, nome, 'CIC'))

        self.assertEqual(self.filtrar(nome='SILV'), ['Ana Silva', 'Bruno Silveira'])

    def test_filtra_por_nome_ou_codigo_da_disciplina_sem_duplicar_professor(self):
        self.catalogo()  # Professor 1: MDS10 e MDS20; Professor 2: só MDS10

        self.assertEqual(self.filtrar(disciplina='disciplina 20'), ['Professor 1'])
        self.assertEqual(self.filtrar(disciplina='mds20'), ['Professor 1'])
        self.assertEqual(self.filtrar(disciplina='MDS'), ['Professor 1', 'Professor 2'])

    def test_nome_e_disciplina_combinam_com_e(self):
        self.catalogo()

        self.assertEqual(self.filtrar(nome='professor 1', disciplina='MDS10'), ['Professor 1'])
        self.assertEqual(self.filtrar(nome='professor 2', disciplina='MDS20'), [])

    def test_sem_filtros_ou_so_espacos_lista_todos_inclusive_sem_disciplinas(self):
        self.catalogo()
        self.sql('INSERT INTO professores VALUES (?, ?, ?)', (3, 'Professor 3', 'FCTE'))

        todos = ['Professor 1', 'Professor 2', 'Professor 3']
        self.assertEqual(self.filtrar(), todos)
        self.assertEqual(self.filtrar(nome='  ', disciplina='  '), todos)

    def test_curingas_do_sql_sao_tratados_como_texto(self):
        for pid, nome in ((1, 'Ana 100%'), (2, 'Ana_Maria'), (3, 'Ana Souza'), (4, 'Ana\\Luz')):
            self.sql('INSERT INTO professores VALUES (?, ?, ?)', (pid, nome, 'CIC'))
        self.sql('INSERT INTO disciplinas VALUES (?, ?, ?)', (1, 'Cálculo 1', 'MAT_01'))
        self.sql('INSERT INTO disciplinas VALUES (?, ?, ?)', (2, 'Física 1', 'FIS001'))
        self.sql('INSERT INTO professor_disciplinas VALUES (?, ?)', (3, 1))
        self.sql('INSERT INTO professor_disciplinas VALUES (?, ?)', (1, 2))

        self.assertEqual(self.filtrar(nome='%'), ['Ana 100%'])
        self.assertEqual(self.filtrar(nome='_'), ['Ana_Maria'])
        self.assertEqual(self.filtrar(nome='\\'), ['Ana\\Luz'])
        self.assertEqual(self.filtrar(disciplina='%'), [])
        self.assertEqual(self.filtrar(disciplina='MAT_'), ['Ana Souza'])
        self.assertEqual(self.filtrar(disciplina='FIS_01'), [])

    def test_espacos_nas_pontas_sao_ignorados(self):
        self.catalogo()

        self.assertEqual(self.filtrar(nome=' professor 1 ', disciplina=' mds20 '), ['Professor 1'])


class TestPaginaComFiltros(BancoIsolado):
    def pagina(self, **filtros):
        resposta = self.client.get('/professores', query_string=filtros)
        return resposta, resposta.get_data(as_text=True)

    def test_filtro_por_nome_mostra_so_professores_correspondentes(self):
        for pid, nome in ((1, 'Carlos Lima'), (2, 'Ana Silva')):
            self.sql('INSERT INTO professores VALUES (?, ?, ?)', (pid, nome, 'CIC'))

        resposta, html = self.pagina(nome='ANA')

        self.assertEqual(resposta.status_code, 200)
        self.assertIn('Ana Silva', html)
        self.assertNotIn('Carlos Lima', html)

    def test_filtro_por_disciplina_aceita_nome_ou_codigo_e_mantem_as_disciplinas_do_professor(self):
        self.catalogo()  # Professor 1: 10 e 20; Professor 2: só 10

        for busca in ('disciplina 20', 'mds20'):
            with self.subTest(busca=busca):
                _, html = self.pagina(disciplina=busca)

                self.assertIn('Professor 1', html)
                self.assertNotIn('Professor 2', html)
                self.assertIn('MDS10', html)
                self.assertIn('MDS20', html)

    def test_pagina_tem_formulario_get_com_campos_de_nome_e_disciplina(self):
        _, html = self.pagina()

        self.assertIn('<form method="get" action="/professores"', html)
        self.assertRegex(html, r'<label[^>]*for="nome"')
        self.assertRegex(html, r'<input[^>]*name="nome"')
        self.assertRegex(html, r'<label[^>]*for="disciplina"')
        self.assertRegex(html, r'<input[^>]*name="disciplina"')

    def test_campos_voltam_preenchidos_e_escapados(self):
        _, html = self.pagina(nome='  Ana "<b>  ', disciplina='MDS10')

        self.assertIn('value="Ana &#34;&lt;b&gt;"', html)
        self.assertIn('value="MDS10"', html)
        self.assertNotIn('<b>', html)

    def test_sem_resultados_com_filtro_mostra_aviso_e_link_para_limpar(self):
        self.catalogo()

        for filtros in ({'nome': 'inexistente'}, {'disciplina': 'inexistente'}):
            with self.subTest(filtros=filtros):
                resposta, html = self.pagina(**filtros)

                self.assertEqual(resposta.status_code, 200)
                self.assertIn('role="status"', html)
                self.assertIn('Nenhum professor encontrado para os filtros informados.', html)
                self.assertIn('href="/professores">Limpar filtros', html)
                self.assertNotIn('Ainda não há professores cadastrados', html)

    def test_sem_filtro_e_sem_professores_mantem_a_mensagem_do_catalogo_vazio(self):
        _, html = self.pagina(nome='  ')

        self.assertIn('Ainda não há professores cadastrados', html)
        self.assertNotIn('Nenhum professor encontrado', html)
        self.assertNotIn('Limpar filtros', html)


if __name__ == '__main__':
    unittest.main()
