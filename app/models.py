class Usuario:
    def __init__(self, nome, email, senha, id=None):
        self.id = id
        self.nome = nome
        self.email = email
        self.senha = senha

    def to_dict(self):
        # Transforma o objeto em dicionário para facilitar o envio para o frontend depois
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email
            # A senha NUNCA vai no to_dict por segurança
        }

class Professor:
    def __init__(self, nome, departamento='', id=None):
        self.id = id
        self.nome = nome
        self.departamento = departamento

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "departamento": self.departamento
        }

class Disciplina:
    def __init__(self, nome, codigo=None, id=None):
        self.id = id
        self.nome = nome
        self.codigo = codigo

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "codigo": self.codigo
        }

class Avaliacao:
    """Espelha a tabela avaliacoes. `nota` guarda a avaliação geral (campo legado)."""

    def __init__(self, usuario_id=None, professor_id=None, disciplina_id=None, nota=None,
                 didatica=None, organizacao=None, disponibilidade=None, dificuldade=None,
                 id=None):
        self.id = id
        self.usuario_id = usuario_id
        self.professor_id = professor_id
        self.disciplina_id = disciplina_id
        self.nota = nota
        self.didatica = didatica
        self.organizacao = organizacao
        self.disponibilidade = disponibilidade
        self.dificuldade = dificuldade

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "professor_id": self.professor_id,
            "disciplina_id": self.disciplina_id,
            "nota": self.nota,
            "didatica": self.didatica,
            "organizacao": self.organizacao,
            "disponibilidade": self.disponibilidade,
            "dificuldade": self.dificuldade,
        }
