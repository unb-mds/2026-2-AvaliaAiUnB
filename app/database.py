import sqlite3

def inicializar_banco():
    conexao = sqlite3.connect('banco.db')
    cursor = conexao.cursor()

    # Cria a tabela de Usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    ''')

    # Cria a tabela de Avaliações com o relacionamento (Foreign Key)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS avaliacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nota INTEGER NOT NULL,
            comentario TEXT,
            usuario_id INTEGER,
            professor_id INTEGER,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')

    conexao.commit()
    conexao.close()

# Roda a função para criar o arquivo banco.db
if __name__ == "__main__":
    inicializar_banco()
    print("Banco de dados e tabelas criados com sucesso!")