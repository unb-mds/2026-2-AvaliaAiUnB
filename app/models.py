"""Estruturas de dados do domínio, espelhando as tabelas do Supabase."""


class Usuario:
    """Conta do Supabase Auth (id uuid) com os dados de perfil (tabela perfis)."""

    def __init__(self, nome, email, username, id=None):
        self.id = id
        self.nome = nome
        self.email = email
        self.username = username

    def to_dict(self):
        # A senha nunca é guardada nem exposta aqui: quem a trata é o Supabase Auth.
        return {"id": self.id, "nome": self.nome, "email": self.email, "username": self.username}


class Professor:
    def __init__(self, nome, departamento='', id=None):
        self.id = id
        self.nome = nome
        self.departamento = departamento

    def to_dict(self):
        return {"id": self.id, "nome": self.nome, "departamento": self.departamento}


class Disciplina:
    def __init__(self, nome, codigo=None, id=None):
        self.id = id
        self.nome = nome
        self.codigo = codigo

    def to_dict(self):
        return {"id": self.id, "nome": self.nome, "codigo": self.codigo}


class Turma:
    """Espelha a tabela turmas (vínculo professor, disciplina, ano e período)."""

    def __init__(self, professor_id=None, disciplina_id=None, ano=None, periodo=None, id=None):
        self.id = id
        self.professor_id = professor_id
        self.disciplina_id = disciplina_id
        self.ano = ano
        self.periodo = periodo

    def to_dict(self):
        return dict(vars(self))


class Avaliacao:
    """Espelha a tabela avaliacoes (notas inteiras de 1 a 5)."""

    def __init__(self, usuario_id=None, professor_id=None, disciplina_id=None, didatica=None,
                 clareza=None, organizacao=None, disponibilidade=None, dificuldade=None,
                 ano=None, periodo=None, id=None):
        self.id = id
        self.usuario_id = usuario_id
        self.professor_id = professor_id
        self.disciplina_id = disciplina_id
        self.didatica = didatica
        self.clareza = clareza
        self.organizacao = organizacao
        self.disponibilidade = disponibilidade
        self.dificuldade = dificuldade
        self.ano = ano
        self.periodo = periodo

    def to_dict(self):
        return dict(vars(self))
