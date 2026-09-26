import sqlite3
from flask import current_app, has_app_context

CAMINHO_BANCO = 'banco.db'


def get_db_connection():
    """
    Abre uma conexao com o banco ja configurada para uso nos controllers
    e repositorios:
    - row_factory = sqlite3.Row permite acessar colunas por nome (ex: usuario["email"])
    - PRAGMA foreign_keys garante que os relacionamentos (FOREIGN KEY) sejam respeitados
    """
    caminho = current_app.config.get('DATABASE', CAMINHO_BANCO) if has_app_context() else CAMINHO_BANCO
    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def inicializar_banco():
    conexao = get_db_connection()
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

    # Estrutura mínima para consultar o perfil por professor + disciplina.
    # A população do catálogo continua sob responsabilidade da importação (#29/#30).
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS professores (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            departamento TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS disciplinas (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL,
            codigo TEXT UNIQUE
        );
        CREATE TABLE IF NOT EXISTS professor_disciplinas (
            professor_id INTEGER NOT NULL REFERENCES professores(id),
            disciplina_id INTEGER NOT NULL REFERENCES disciplinas(id),
            PRIMARY KEY (professor_id, disciplina_id)
        );
    ''')
    # Migração aditiva e idempotente: nota representa a avaliação geral.
    # Registros legados ficam intactos, sem inventar disciplina ou critérios.
    colunas = {linha['name'] for linha in cursor.execute('PRAGMA table_info(avaliacoes)')}
    novas_colunas = {
        'disciplina_id': 'INTEGER REFERENCES disciplinas(id)',
        'didatica': 'INTEGER CHECK (didatica BETWEEN 1 AND 5)',
        'organizacao': 'INTEGER CHECK (organizacao BETWEEN 1 AND 5)',
        'disponibilidade': 'INTEGER CHECK (disponibilidade BETWEEN 1 AND 5)',
        'dificuldade': 'INTEGER CHECK (dificuldade BETWEEN 1 AND 5)',
    }
    for nome, definicao in novas_colunas.items():
        if nome not in colunas:
            cursor.execute(f'ALTER TABLE avaliacoes ADD COLUMN {nome} {definicao}')
    cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS avaliacao_usuario_professor_disciplina
                      ON avaliacoes(usuario_id, professor_id, disciplina_id)
                      WHERE disciplina_id IS NOT NULL''')
    conexao.commit()
    conexao.close()


# Roda a funcao para criar o arquivo banco.db
if __name__ == "__main__":
    inicializar_banco()
    print("Banco de dados e tabelas criados com sucesso!")
