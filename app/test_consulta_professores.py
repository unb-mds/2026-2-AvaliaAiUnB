"""Testes da issue #30: consulta (listagem) de professores."""
import unittest

from app.repositorio import ProfessorRepository
from app.test_implementacao import BancoIsolado


class TestListarProfessores(BancoIsolado):
    def test_listar_retorna_professores_em_ordem_de_nome(self):
        for pid, nome in ((1, 'Carlos Lima'), (2, 'Ana Silva'), (3, 'Bruno Costa')):
            self.sql('INSERT INTO professores VALUES (?, ?, ?)', (pid, nome, 'CIC'))

        with self.app.app_context():
            nomes = [p['nome'] for p in ProfessorRepository().listar()]

        self.assertEqual(nomes, ['Ana Silva', 'Bruno Costa', 'Carlos Lima'])


class TestPaginaProfessores(BancoIsolado):
    def pagina(self):
        resposta = self.client.get('/professores')
        return resposta, resposta.get_data(as_text=True)

    def test_lista_e_publica_e_ordenada_por_nome(self):
        for pid, nome in ((1, 'Carlos Lima'), (2, 'Ana Silva')):
            self.sql('INSERT INTO professores VALUES (?, ?, ?)', (pid, nome, 'CIC'))

        resposta, html = self.pagina()

        self.assertEqual(resposta.status_code, 200)
        self.assertLess(html.index('Ana Silva'), html.index('Carlos Lima'))
        self.assertIn('CIC', html)

    def test_exibe_nome_e_codigo_das_disciplinas_de_cada_professor(self):
        self.catalogo()  # Professor 1: 10 e 20; Professor 2: só 10

        _, html = self.pagina()

        prof1, prof2 = html.split('Professor 2')
        self.assertIn('Disciplina 10', prof1)
        self.assertIn('MDS10', prof1)
        self.assertIn('Disciplina 20', prof1)
        self.assertIn('MDS20', prof1)
        self.assertIn('MDS10', prof2)
        self.assertNotIn('MDS20', prof2)

    def test_cada_professor_tem_link_para_o_perfil(self):
        self.catalogo()

        _, html = self.pagina()

        self.assertIn('href="/professores/1"', html)
        self.assertIn('href="/professores/2"', html)
        self.assertEqual(self.client.get('/professores/1').status_code, 200)

    def test_professor_sem_disciplinas_aparece_com_aviso(self):
        self.sql('INSERT INTO professores VALUES (?, ?, ?)', (1, 'Ana Silva', 'CIC'))

        _, html = self.pagina()

        self.assertIn('Ana Silva', html)
        self.assertIn('Ainda não há disciplinas cadastradas', html)

    def test_catalogo_vazio_mostra_mensagem(self):
        resposta, html = self.pagina()

        self.assertEqual(resposta.status_code, 200)
        self.assertIn('role="status"', html)
        self.assertIn('Ainda não há professores cadastrados', html)


if __name__ == '__main__':
    unittest.main()
