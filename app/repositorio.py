from app.models import Usuario
from app.database import get_db_connection
from app.validacoes import CRITERIOS
from contextlib import closing
import sqlite3


class UsuarioRepository:

    # Requisito 1 e 3: Criação no SQLite e Tratamento de usuário existente
    def criar_usuario(self, usuario):
        conexao = get_db_connection()

        try:
            # Serializa a verificação e a inserção, inclusive para e-mails legados
            # com letras maiúsculas. A restrição UNIQUE existente é preservada.
            conexao.execute('BEGIN IMMEDIATE')
            if conexao.execute('SELECT 1 FROM usuarios WHERE email = ? COLLATE NOCASE',
                               (usuario.email,)).fetchone():
                return False, 'Erro: Este e-mail já está cadastrado.'
            cursor = conexao.execute('''
                INSERT INTO usuarios (nome, email, senha)
                VALUES (?, ?, ?)
            ''', (usuario.nome, usuario.email, usuario.senha))
            conexao.commit()

            # Atualiza o ID do objeto com o ID gerado pelo banco
            usuario.id = cursor.lastrowid
            return True, "Usuário criado com sucesso!"

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
            'SELECT id, nome, email, senha FROM usuarios WHERE email = ? COLLATE NOCASE',
            (email,)
        ).fetchone()
        conexao.close()

        if linha:
            return Usuario(id=linha["id"], nome=linha["nome"], email=linha["email"], senha=linha["senha"])
        return None


class ProfessorRepository:
    def criar(self, professor):
        with closing(get_db_connection()) as conexao:
            with conexao:
                cursor = conexao.execute(
                    'INSERT INTO professores (nome, departamento) VALUES (?, ?)',
                    (professor.nome, professor.departamento))
        professor.id = cursor.lastrowid
        return True, 'Professor criado com sucesso!'

    def vincular(self, professor_id, disciplina_id):
        with closing(get_db_connection()) as conexao:
            try:
                with conexao:
                    conexao.execute('''INSERT OR IGNORE INTO professor_disciplinas
                        (professor_id, disciplina_id) VALUES (?, ?)''',
                        (professor_id, disciplina_id))
            except sqlite3.IntegrityError as erro:
                if erro.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_FOREIGNKEY:
                    return False, 'Erro: Professor ou disciplina não encontrado.'
                raise
        return True, 'Professor vinculado à disciplina com sucesso!'

    def buscar_por_id(self, professor_id):
        with closing(get_db_connection()) as conexao:
            return conexao.execute('SELECT id, nome, departamento FROM professores WHERE id = ?',
                                  (professor_id,)).fetchone()

    def buscar_por_nome(self, trecho):
        with closing(get_db_connection()) as conexao:
            return conexao.execute('''SELECT id, nome, departamento FROM professores
                WHERE nome LIKE ? COLLATE NOCASE ORDER BY nome, id''',
                (f'%{trecho}%',)).fetchall()

    def listar_disciplinas(self, professor_id):
        with closing(get_db_connection()) as conexao:
            return conexao.execute('''SELECT d.id, d.nome, d.codigo FROM disciplinas d
                JOIN professor_disciplinas pd ON pd.disciplina_id = d.id
                WHERE pd.professor_id = ? ORDER BY d.nome, d.id''', (professor_id,)).fetchall()


class DisciplinaRepository:
    def criar(self, disciplina):
        with closing(get_db_connection()) as conexao:
            try:
                with conexao:
                    cursor = conexao.execute(
                        'INSERT INTO disciplinas (nome, codigo) VALUES (?, ?)',
                        (disciplina.nome, disciplina.codigo))
            except sqlite3.IntegrityError:
                return False, 'Erro: Este código de disciplina já está cadastrado.'
        disciplina.id = cursor.lastrowid
        return True, 'Disciplina criada com sucesso!'

    def buscar_por_id(self, disciplina_id):
        with closing(get_db_connection()) as conexao:
            return conexao.execute('SELECT id, nome, codigo FROM disciplinas WHERE id = ?',
                                  (disciplina_id,)).fetchone()

    def buscar_por_codigo(self, codigo):
        with closing(get_db_connection()) as conexao:
            return conexao.execute('SELECT id, nome, codigo FROM disciplinas WHERE codigo = ?',
                                  (codigo,)).fetchone()

    def listar_professores(self, disciplina_id):
        with closing(get_db_connection()) as conexao:
            return conexao.execute('''SELECT p.id, p.nome, p.departamento FROM professores p
                JOIN professor_disciplinas pd ON pd.professor_id = p.id
                WHERE pd.disciplina_id = ? ORDER BY p.nome, p.id''', (disciplina_id,)).fetchall()


class AvaliacaoRepository:
    # O campo legado nota contém a avaliação geral, sem misturar dificuldade
    # (em que uma nota maior significa mais difícil) com qualidade.
    COLUNAS = {c: ('nota' if c == 'avaliacao_geral' else c) for c in CRITERIOS}

    def calcular_medias(self, professor_id, disciplina_id):
        agregacoes = ', '.join(f'AVG({coluna}) AS {criterio}'
                              for criterio, coluna in self.COLUNAS.items())
        validas = ' AND '.join(f"typeof({coluna}) = 'integer' AND {coluna} BETWEEN 1 AND 5"
                              for coluna in self.COLUNAS.values())
        with closing(get_db_connection()) as conexao:
            linha = conexao.execute(f'''SELECT COUNT(*) AS quantidade, {agregacoes}
                FROM avaliacoes WHERE professor_id = ? AND disciplina_id = ? AND {validas}''',
                (professor_id, disciplina_id)).fetchone()
        return {'quantidade': linha['quantidade'],
                'medias': {criterio: linha[criterio] for criterio in CRITERIOS}}

    def salvar(self, usuario_id, professor_id, disciplina_id, notas):
        if any(type(notas.get(c)) is not int or not 1 <= notas[c] <= 5 for c in CRITERIOS):
            raise ValueError('Todos os critérios devem ter notas inteiras de 1 a 5.')
        with closing(get_db_connection()) as conexao:
            with conexao:
                vinculo = conexao.execute('''SELECT 1 FROM professor_disciplinas
                    WHERE professor_id = ? AND disciplina_id = ?''',
                    (professor_id, disciplina_id)).fetchone()
                if vinculo is None:
                    raise ValueError('Disciplina não vinculada ao professor.')
                try:
                    conexao.execute('''INSERT INTO avaliacoes
                        (usuario_id, professor_id, disciplina_id, nota, didatica,
                         organizacao, dificuldade, disponibilidade)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                        (usuario_id, professor_id, disciplina_id, notas['avaliacao_geral'],
                         notas['didatica'], notas['organizacao'], notas['dificuldade'],
                         notas['disponibilidade']))
                except sqlite3.IntegrityError as erro:
                    if erro.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
                        return False
                    raise
        return True
