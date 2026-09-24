from app.models import Usuario
from app.database import get_db_connection


class UsuarioRepository:

    # Requisito 1 e 3: Criação no SQLite e Tratamento de usuário existente
    def criar_usuario(self, usuario):
        conexao = get_db_connection()

        try:
            cursor = conexao.execute('''
                INSERT INTO usuarios (nome, email, senha)
                VALUES (?, ?, ?)
            ''', (usuario.nome, usuario.email, usuario.senha))
            conexao.commit()

            # Atualiza o ID do objeto com o ID gerado pelo banco
            usuario.id = cursor.lastrowid
            return True, "Usuário criado com sucesso!"

        except conexao.IntegrityError:
            # O SQLite vai disparar este erro se tentarmos usar um e-mail que já
            # existe (porque definimos como UNIQUE na Issue 24)
            return False, "Erro: Este e-mail já está cadastrado."

        finally:
            conexao.close()

    # Requisito 2: Consulta por identificador
    def buscar_usuario_por_id(self, id_usuario):
        conexao = get_db_connection()
        linha = conexao.execute(
            'SELECT id, nome, email, senha FROM usuarios WHERE id = ?',
            (id_usuario,)
        ).fetchone()
        conexao.close()

        if linha:
            return Usuario(id=linha["id"], nome=linha["nome"], email=linha["email"], senha=linha["senha"])
        return None

    # Necessário para o login: encontrar o usuário a partir do e-mail
    # digitado no formulário, para então validar a senha.
    def buscar_usuario_por_email(self, email):
        conexao = get_db_connection()
        linha = conexao.execute(
            'SELECT id, nome, email, senha FROM usuarios WHERE email = ?',
            (email,)
        ).fetchone()
        conexao.close()

        if linha:
            return Usuario(id=linha["id"], nome=linha["nome"], email=linha["email"], senha=linha["senha"])
        return None