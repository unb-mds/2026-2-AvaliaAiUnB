"""Cliente Supabase falso em memória (tabelas + Auth), para testar sem rede nem banco real."""
import itertools
import uuid
from types import SimpleNamespace

from supabase_auth.errors import AuthApiError


class Resposta:
    def __init__(self, data):
        self.data = data


class Consulta:
    def __init__(self, tabelas, nome, registro_upserts=None):
        self.tabelas, self.nome = tabelas, nome
        self.registro_upserts = registro_upserts
        self.linhas_upsert, self.conflito = None, None
        self.filtros, self.ordem, self.faixa, self.limite = [], [], None, None
        self.novo, self.apagar = None, False

    def select(self, _colunas):
        return self

    def eq(self, coluna, valor):
        self.filtros.append((coluna, valor))
        return self

    def order(self, coluna):
        self.ordem.append(coluna)
        return self

    def range(self, inicio, fim):
        self.faixa = (inicio, fim)
        return self

    def limit(self, quantidade):
        self.limite = quantidade
        return self

    def insert(self, linha):
        self.novo = linha
        return self

    def upsert(self, linhas, on_conflict):
        self.linhas_upsert, self.conflito = linhas, on_conflict
        return self

    def delete(self):
        self.apagar = True
        return self

    def execute(self):
        tabela = self.tabelas[self.nome]
        if self.linhas_upsert is not None:
            colunas = self.conflito.split(',')
            if self.registro_upserts is not None:
                self.registro_upserts.append((self.nome, self.conflito))
            gravadas = []
            for linha in self.linhas_upsert:
                existente = next((l for l in tabela
                                  if all(l.get(c) == linha.get(c) for c in colunas)), None)
                if existente is None:
                    existente = {'id': max((l['id'] for l in tabela), default=0) + 1}
                    tabela.append(existente)
                existente.update(linha)
                gravadas.append(dict(existente))
            return Resposta(gravadas)
        if self.novo is not None:
            if self.nome == 'perfis' and any(l['username'] == self.novo['username'] for l in tabela):
                raise RuntimeError('duplicate key value violates unique constraint "perfis_username_key"')
            tabela.append({'id': len(tabela) + 1, **self.novo} if self.nome != 'perfis' else dict(self.novo))
            return Resposta([self.novo])
        if self.apagar:
            tabela[:] = [l for l in tabela if not all(l.get(c) == v for c, v in self.filtros)]
            return Resposta([])
        linhas = [dict(l) for l in tabela if all(l.get(c) == v for c, v in self.filtros)]
        for coluna in reversed(self.ordem):
            linhas.sort(key=lambda l: l[coluna])
        if self.faixa:
            linhas = linhas[self.faixa[0]:self.faixa[1] + 1]
        if self.limite is not None:
            linhas = linhas[:self.limite]
        return Resposta(linhas)


class AdminFalso:
    def __init__(self, auth):
        self.auth = auth

    def create_user(self, atributos):
        if any(u['email'] == atributos['email'] for u in self.auth.usuarios.values()):
            raise AuthApiError('A user with this email address has already been registered',
                               422, 'email_exists')
        uid = str(uuid.uuid4())
        self.auth.usuarios[uid] = {'id': uid, 'email': atributos['email'],
                                   'senha': atributos['password'],
                                   'user_metadata': atributos.get('user_metadata', {})}
        return SimpleNamespace(user=self.auth._usuario(uid))

    def get_user_by_id(self, uid):
        if uid not in self.auth.usuarios:
            raise AuthApiError('User not found', 404, 'user_not_found')
        return SimpleNamespace(user=self.auth._usuario(uid))

    def delete_user(self, uid):
        self.auth.usuarios.pop(uid, None)

    def sign_out(self, token):
        self.auth.tokens.pop(token, None)


class AuthFalso:
    def __init__(self):
        self.usuarios, self.tokens, self.refresh = {}, {}, {}
        self.contador = itertools.count(1)
        self.admin = AdminFalso(self)

    def _usuario(self, uid):
        u = self.usuarios[uid]
        return SimpleNamespace(id=uid, email=u['email'], user_metadata=u['user_metadata'])

    def _nova_sessao(self, uid):
        n = next(self.contador)
        acesso, renovacao = f'acesso-{n}', f'renovacao-{n}'
        self.tokens[acesso] = uid
        self.refresh[renovacao] = uid
        return SimpleNamespace(session=SimpleNamespace(access_token=acesso, refresh_token=renovacao),
                               user=self._usuario(uid))

    def sign_in_with_password(self, credenciais):
        for uid, u in self.usuarios.items():
            if u['email'] == credenciais['email'] and u['senha'] == credenciais['password']:
                return self._nova_sessao(uid)
        raise AuthApiError('Invalid login credentials', 400, 'invalid_credentials')

    def get_user(self, token):
        if token not in self.tokens:
            raise AuthApiError('invalid JWT', 401, 'bad_jwt')
        return SimpleNamespace(user=self._usuario(self.tokens[token]))

    def refresh_session(self, refresh_token):
        if refresh_token not in self.refresh:
            raise AuthApiError('Invalid Refresh Token', 400, 'refresh_token_not_found')
        return self._nova_sessao(self.refresh[refresh_token])

    def expirar_acesso(self):
        self.tokens.clear()


class ClienteFalso:
    def __init__(self):
        self.auth = AuthFalso()
        self.upserts = []  # (tabela, on_conflict) de cada upsert executado
        self.tabelas = {
            'professores': [
                {'id': 1, 'nome': 'JOSÉ ÁVILA', 'departamento': 'FCTE'},
                {'id': 2, 'nome': 'MARIA LIMA', 'departamento': 'FCTE'},
                {'id': 3, 'nome': 'SEM TURMA', 'departamento': 'FCTE'},
            ],
            'vw_professor_disciplina': [
                {'professor_id': 1, 'disciplina_id': 10, 'codigo_disciplina': 'FGA0001',
                 'disciplina': 'CÁLCULO 1', 'ano': 2026, 'periodo': 1},
                {'professor_id': 1, 'disciplina_id': 10, 'codigo_disciplina': 'FGA0001',
                 'disciplina': 'CÁLCULO 1', 'ano': 2026, 'periodo': 2},
                {'professor_id': 2, 'disciplina_id': 20, 'codigo_disciplina': 'FGA0002',
                 'disciplina': 'FÍSICA 1', 'ano': 2026, 'periodo': 2},
            ],
            'disciplinas': [],
            'turmas': [],
            'avaliacoes': [],
            'perfis': [],
        }

    def table(self, nome):
        return Consulta(self.tabelas, nome, self.upserts)
