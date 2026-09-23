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