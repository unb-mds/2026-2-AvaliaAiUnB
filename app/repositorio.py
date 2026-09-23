import sqlite3
from app.models import Usuario

class UsuarioRepository:
    def __init__(self):
        self.db_path = 'banco.db'

    # Requisito 1 e 3: Criação no SQLite e Tratamento de usuário existente
    def criar_usuario(self, usuario):
        conexao = sqlite3.connect(self.db_path)
        cursor = conexao.cursor()

        try:
            cursor.execute('''
                INSERT INTO usuarios (nome, email, senha)
                VALUES (?, ?, ?)
            ''', (usuario.nome, usuario.email, usuario.senha))
            conexao.commit()
            
            # Atualiza o ID do objeto com o ID gerado pelo banco
            usuario.id = cursor.lastrowid
            return True, "Usuário criado com sucesso!"
            
        except sqlite3.IntegrityError:
            # O SQLite vai disparar este erro se tentarmos usar um e-mail que já existe (porque definimos como UNIQUE na Issue 24)
            return False, "Erro: Este e-mail já está cadastrado."
            
        finally:
            conexao.close()

    # Requisito 2: Consulta por identificador
    def buscar_usuario_por_id(self, id_usuario):
        conexao = sqlite3.connect(self.db_path)
        cursor = conexao.cursor()

        cursor.execute('SELECT id, nome, email, senha FROM usuarios WHERE id = ?', (id_usuario,))
        linha = cursor.fetchone()
        conexao.close()

        if linha:
            # Reconstrói o objeto Usuario com os dados do banco
            # linha[0] = id, linha[1] = nome, linha[2] = email, linha[3] = senha
            return Usuario(id=linha[0], nome=linha[1], email=linha[2], senha=linha[3])
        return None