import sqlite3
import unittest

class TestAvaliacoes(unittest.TestCase):
    def setUp(self):
        # Cria uma base de dados em memória, limpa e isolada para o teste
        self.conexao = sqlite3.connect(':memory:')
        self.cursor = self.conexao.cursor()
        
        # Cria as tabelas básicas
        self.cursor.execute('''
            CREATE TABLE usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT)
        ''')
        
        # Tabela de avaliações já com os novos campos de critérios (estrelas)
        self.cursor.execute('''
            CREATE TABLE avaliacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                criterio_1 INTEGER,
                criterio_2 INTEGER,
                criterio_3 INTEGER,
                usuario_id INTEGER,
                professor_id INTEGER
            )
        ''')
        
        # Cria um aluno falso para associar à avaliação
        self.cursor.execute('INSERT INTO usuarios (nome) VALUES ("Aluno Teste")')
        self.usuario_id = self.cursor.lastrowid
        self.conexao.commit()

    def test_inserir_e_buscar_avaliacao(self):
        # 1. Simula a inserção de uma avaliação com estrelas (ex: 5, 4 e 5 estrelas)
        self.cursor.execute('''
            INSERT INTO avaliacoes (criterio_1, criterio_2, criterio_3, usuario_id)
            VALUES (?, ?, ?, ?)
        ''', (5, 4, 5, self.usuario_id))
        self.conexao.commit()
        
        # 2. Busca a avaliação na base de dados
        self.cursor.execute('SELECT criterio_1, criterio_2, criterio_3 FROM avaliacoes WHERE usuario_id = ?', (self.usuario_id,))
        resultado = self.cursor.fetchone()
        
        # 3. Verifica se os dados guardados estão corretos (Asserts)
        self.assertIsNotNone(resultado, "A avaliação não foi encontrada na base de dados.")
        self.assertEqual(resultado[0], 5, "Erro: A nota do critério 1 guardada é diferente.")
        self.assertEqual(resultado[1], 4, "Erro: A nota do critério 2 guardada é diferente.")
        self.assertEqual(resultado[2], 5, "Erro: A nota do critério 3 guardada é diferente.")

    def tearDown(self):
        # Fecha a ligação no final do teste
        self.conexao.close()

if __name__ == '__main__':
    unittest.main()