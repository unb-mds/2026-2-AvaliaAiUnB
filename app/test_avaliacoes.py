import sqlite3
import unittest

class TestAvaliacoes(unittest.TestCase):
    def setUp(self):
        # Cria uma base de dados em memória que desaparece após o teste (ótimo para não sujar o banco real)
        self.conexao = sqlite3.connect(':memory:')
        self.cursor = self.conexao.cursor()
        
        # Cria as tabelas básicas
        self.cursor.execute('''
            CREATE TABLE usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT)
        ''')
        self.cursor.execute('''
            CREATE TABLE avaliacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nota INTEGER,
                comentario TEXT,
                usuario_id INTEGER
            )
        ''')
        
        # Cria um aluno falso para podermos associar a avaliação
        self.cursor.execute('INSERT INTO usuarios (nome) VALUES ("Aluno Teste")')
        self.usuario_id = self.cursor.lastrowid
        self.conexao.commit()

    def test_inserir_e_buscar_avaliacao(self):
        # 1. Simula o envio de uma avaliação (Nota 5)
        self.cursor.execute('''
            INSERT INTO avaliacoes (nota, comentario, usuario_id)
            VALUES (?, ?, ?)
        ''', (5, "Excelente didática!", self.usuario_id))
        self.conexao.commit()
        
        # 2. Vai à base de dados procurar a avaliação que acabou de ser inserida
        self.cursor.execute('SELECT nota, comentario FROM avaliacoes WHERE usuario_id = ?', (self.usuario_id,))
        resultado = self.cursor.fetchone()
        
        # 3. Verifica se o sistema guardou tudo corretamente (Asserts)
        self.assertIsNotNone(resultado, "A avaliação não foi encontrada na base de dados.")
        self.assertEqual(resultado[0], 5, "A nota guardada é diferente da nota enviada.")
        self.assertEqual(resultado[1], "Excelente didática!", "O comentário guardado está incorreto.")

    def tearDown(self):
        # Fecha a ligação no final
        self.conexao.close()

if __name__ == '__main__':
    unittest.main()