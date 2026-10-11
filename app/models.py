class Usuario:
    def __init__(self, nome, email, senha, id=None):
        self.id = id
        self.nome = nome
        self.email = email
        self.senha = senha
class Avaliacao:
    def __init__(self, criterio_1=None, criterio_2=None, criterio_3=None, usuario_id=None, professor_id=None, id=None):
        self.id = id
        self.criterio_1 = criterio_1  # Representa a nota em estrelas da 1ª valência
        self.criterio_2 = criterio_2  # Representa a nota em estrelas da 2ª valência
        self.criterio_3 = criterio_3  # Representa a nota em estrelas da 3ª valência
        #PODEMOS CRIAR MAIS MEIOS DE AVALIÇÃO COM O DECORRER DO TRABALHO!
        self.usuario_id = usuario_id
        self.professor_id = professor_id

    def to_dict(self):
        return {
            "id": self.id,
            "criterio_1": self.criterio_1,
            "criterio_2": self.criterio_2,
            "criterio_3": self.criterio_3,
            "usuario_id": self.usuario_id,
            "professor_id": self.professor_id
        }

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