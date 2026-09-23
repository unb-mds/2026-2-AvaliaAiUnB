class Usuario:
    def __init__(self, nome, email, senha, id=None):
        self.id = id
        self.nome = nome
        self.email = email
        self.senha = senha
class Avaliacao:
    def __init__(self, nota, comentario, usuario_id, professor_id=None, id=None):
        self.id = id
        self.nota = nota
        self.comentario = comentario
        self.usuario_id = usuario_id
        self.professor_id = professor_id

    def to_dict(self):
        return {
            "id": self.id,
            "nota": self.nota,
            "comentario": self.comentario,
            "usuario_id": self.usuario_id,
            "professor_id": self.professor_id
        }

    def to_dict(self):
        # Transforma o objeto em dicionário para facilitar o envio para o frontend depois
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email
            # A senha NUNCA vai no to_dict por segurança
        }