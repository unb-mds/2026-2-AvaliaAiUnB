import sqlite3

CAMINHO_BANCO = 'banco.db'


def get_db_connection():
    """
    Abre uma conexao com o banco ja configurada para uso nos controllers
    e repositorios:
    - row_factory = sqlite3.Row permite acessar colunas por nome (ex: usuario["email"])
    - PRAGMA foreign_keys garante que os relacionamentos (FOREIGN KEY) sejam respeitados
    """
    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def inicializar_banco():
    conexao = sqlite3.connect(CAMINHO_BANCO)
    cursor = conexao.cursor()

    # Cria a tabela de Usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    ''')

    # Cria a tabela de Avaliacoes com o relacionamento (Foreign Key)
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

    # Cria a tabela de Sessoes, usada pelo session_controller para
    # criacao de sessao, identificacao do usuario logado e logout.
    # O token em si NUNCA e salvo aqui, so o seu hash (SHA-256).
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_hash TEXT NOT NULL UNIQUE,
            usuario_id INTEGER NOT NULL,
            criado_em TEXT NOT NULL DEFAULT (datetime('now')),
            expira_em TEXT NOT NULL,
            user_agent TEXT,
            ip_origem TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
        )
    ''')

    conexao.commit()
    conexao.close()


# Roda a funcao para criar o arquivo banco.db
if __name__ == "__main__":
    inicializar_banco()
    print("Banco de dados e tabelas criados com sucesso!")