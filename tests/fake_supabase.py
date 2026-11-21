"""Cliente Supabase falso em memória (tabelas + Auth), para testar sem rede nem banco real."""
import itertools
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from supabase_auth.errors import AuthApiError


class Resposta:
    def __init__(self, data):
        self.data = data


class _Predicado:
    """Valor de filtro que decide a igualdade (usado por .in_ e .is_ sem mexer nos demais filtros)."""

    def __init__(self, funcao):
        self.funcao = funcao

    def __eq__(self, outro):
        return self.funcao(outro)

    __hash__ = None


_relogio_comentarios = itertools.count(1)


def _agora_comentarios():
    """Instante determinístico e crescente (ISO 8601), no lugar do NOW() do banco."""
    return (datetime(2027, 1, 1, tzinfo=timezone.utc)
            + timedelta(seconds=next(_relogio_comentarios))).isoformat()


class Consulta:
    def __init__(self, tabelas, nome, registro_upserts=None):
        self.tabelas, self.nome = tabelas, nome
        self.registro_upserts = registro_upserts
        self.linhas_upsert, self.conflito, self.ignorar_duplicados = None, None, False
        self.filtros, self.ordem, self.faixa, self.limite = [], [], None, None
        self.novo, self.atualizacao, self.apagar = None, None, False
        self.ordem_decrescente = set()

    def select(self, _colunas):
        return self

    def eq(self, coluna, valor):
        self.filtros.append((coluna, valor))
        return self

    def in_(self, coluna, valores):
        valores = list(valores)
        self.filtros.append((coluna, _Predicado(lambda v: v in valores)))
        return self

    def is_(self, coluna, valor):
        """Como o PostgREST: is_(col, 'null') filtra IS NULL."""
        if valor != 'null':
            raise NotImplementedError('O fake só suporta is_(coluna, "null").')
        self.filtros.append((coluna, _Predicado(lambda v: v is None)))
        return self

    def order(self, coluna, desc=False):
        self.ordem.append(coluna)
        if desc:
            self.ordem_decrescente.add(coluna)
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

    def update(self, dados):
        self.atualizacao = dados
        return self

    def upsert(self, linhas, on_conflict, ignore_duplicates=False):
        self.linhas_upsert, self.conflito = linhas, on_conflict
        self.ignorar_duplicados = ignore_duplicates
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
                    if self.nome == 'favoritos':   # chave composta, sem id; default do banco
                        existente = {'criado_em': _agora_comentarios()}
                    else:
                        existente = {'id': max((l['id'] for l in tabela), default=0) + 1}
                    tabela.append(existente)
                elif self.ignorar_duplicados:
                    continue  # ON CONFLICT DO NOTHING: o Postgres não devolve a linha
                existente.update(linha)
                gravadas.append(dict(existente))
            return Resposta(gravadas)
        if self.novo is not None:
            if self.nome == 'perfis' and any(l['username'] == self.novo['username']
                                             or l['id'] == self.novo['id'] for l in tabela):
                raise RuntimeError('duplicate key value violates unique constraint "perfis_username_key"')
            novo_id = max((l.get('id', 0) for l in tabela if isinstance(l.get('id'), int)), default=0) + 1
            registro = {'id': novo_id, **self.novo} if self.nome != 'perfis' else dict(self.novo)
            if self.nome == 'denuncias_comentarios':
                # índice único parcial: uma denúncia ativa por usuário e comentário
                if any(l['comentario_id'] == self.novo['comentario_id']
                       and l['usuario_id'] == self.novo['usuario_id']
                       and l.get('resolvida_em') is None for l in tabela):
                    raise RuntimeError('duplicate key value violates unique constraint '
                                       '"uq_denuncias_ativa_usuario_comentario" (23505)')
                registro = {'criado_em': _agora_comentarios(), 'resolvida_em': None, **registro}
            if self.nome == 'comentarios':   # defaults do banco
                agora = _agora_comentarios()
                registro = {'criado_em': agora, 'atualizado_em': agora, 'ocultado_em': None, **registro}
            tabela.append(registro)
            return Resposta([dict(registro)])
        if self.atualizacao is not None:
            if self.nome == 'comentarios' and {'texto', 'disciplina_id'} & set(self.atualizacao):
                # trigger set_atualizado_em
                self.atualizacao = {**self.atualizacao, 'atualizado_em': _agora_comentarios()}
            atualizadas = []
            for l in tabela:
                if all(l.get(c) == v for c, v in self.filtros):
                    l.update(self.atualizacao)
                    atualizadas.append(dict(l))
            return Resposta(atualizadas)
        if self.apagar:
            apagadas = [dict(l) for l in tabela if all(l.get(c) == v for c, v in self.filtros)]
            tabela[:] = [l for l in tabela if not all(l.get(c) == v for c, v in self.filtros)]
            return Resposta(apagadas)
        linhas = [dict(l) for l in tabela if all(l.get(c) == v for c, v in self.filtros)]
        for coluna in reversed(self.ordem):
            linhas.sort(key=lambda l: l[coluna], reverse=coluna in self.ordem_decrescente)
        if self.faixa:
            linhas = linhas[self.faixa[0]:self.faixa[1] + 1]
        if self.limite is not None:
            linhas = linhas[:self.limite]
        return Resposta(linhas)


class AdminFalso:
    def __init__(self, auth):
        self.auth = auth

    def get_user_by_id(self, uid):
        if uid not in self.auth.usuarios:
            raise AuthApiError('User not found', 404, 'user_not_found')
        return SimpleNamespace(user=self.auth._usuario(uid))

    def update_user_by_id(self, uid, atributos):
        if uid not in self.auth.usuarios:
            raise AuthApiError('User not found', 404, 'user_not_found')
        self.auth.usuarios[uid]['user_metadata'].update(atributos.get('user_metadata', {}))
        return SimpleNamespace(user=self.auth._usuario(uid))

    def delete_user(self, uid):
        self.auth.usuarios.pop(uid, None)

    def sign_out(self, token):
        usuario_id = self.auth.tokens.get(token)
        if usuario_id is None:
            raise AuthApiError('invalid JWT', 401, 'bad_jwt')
        for tokens in (self.auth.tokens, self.auth.refresh):
            for chave in [chave for chave, dono in tokens.items() if dono == usuario_id]:
                del tokens[chave]


class AuthFalso:
    def __init__(self):
        self.usuarios, self.tokens, self.refresh = {}, {}, {}
        self.codigos_google = {}
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

    def get_user(self, token):
        if token not in self.tokens:
            raise AuthApiError('invalid JWT', 401, 'bad_jwt')
        return SimpleNamespace(user=self._usuario(self.tokens[token]))

    def refresh_session(self, refresh_token):
        if refresh_token not in self.refresh:
            raise AuthApiError('Invalid Refresh Token', 400, 'refresh_token_not_found')
        return self._nova_sessao(self.refresh[refresh_token])

    def preparar_retorno_google(self, codigo, email, metadata, verificador):
        """Simula o Google ter devolvido `codigo` para o fluxo iniciado com `verificador`."""
        self.codigos_google[codigo] = (email, dict(metadata), verificador)

    def exchange_code_for_session(self, parametros):
        dados = self.codigos_google.pop(parametros['auth_code'], None)
        if dados is None or dados[2] != parametros['code_verifier']:
            raise AuthApiError('invalid flow state', 400, 'flow_state_not_found')
        email, metadata, _ = dados
        # Como o Supabase: mesmo e-mail verificado vira a mesma conta (vínculo automático).
        uid = next((uid for uid, u in self.usuarios.items() if u['email'] == email), None)
        if uid is None:
            uid = str(uuid.uuid4())
            self.usuarios[uid] = {'id': uid, 'email': email, 'user_metadata': {}}
        self.usuarios[uid]['user_metadata'].update(metadata)
        return self._nova_sessao(uid)

    def expirar_acesso(self):
        self.tokens.clear()


class ClienteFalso:
    def __init__(self):
        self.auth = AuthFalso()
        self.auth_url = 'https://projeto-falso.supabase.co/auth/v1'
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
            'comentarios': [],
            'denuncias_comentarios': [],
            'favoritos': [],
        }

    def table(self, nome):
        return Consulta(self.tabelas, nome, self.upserts)


VERIFICADOR_TESTE = 'verificador-de-teste'


def sessao_google(cliente, repositorio, email, nome):
    """Login com Google direto no repositório (sem HTTP). Devolve a sessão (dict)."""
    codigo = f'codigo-{next(cliente.auth.contador)}'
    cliente.auth.preparar_retorno_google(codigo, email, {'full_name': nome}, VERIFICADOR_TESTE)
    return repositorio.entrar_com_google(codigo, VERIFICADOR_TESTE)


def entrar_pela_web(web, cliente, email='ana@gmail.com', nome='Ana'):
    """Faz o fluxo HTTP completo /login/google -> retorno no test_client `web`."""
    from app.routes.auth_routes import CHAVE_PKCE_GOOGLE
    web.get('/login/google')
    with web.session_transaction() as sessao:
        verificador = sessao[CHAVE_PKCE_GOOGLE]
    codigo = f'codigo-{next(cliente.auth.contador)}'
    cliente.auth.preparar_retorno_google(codigo, email, {'full_name': nome}, verificador)
    return web.get(f'/login/google/retorno?code={codigo}')
