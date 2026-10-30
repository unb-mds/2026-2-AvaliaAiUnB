"""Repositórios sobre o Supabase: usuários (Auth + perfis), professores e avaliações.

Tabelas usadas: auth.users (via Supabase Auth), perfis, professores, disciplinas,
turmas, avaliacoes e a view vw_professor_disciplina. `repositorios()` entrega as
instâncias configuradas em create_app.
"""
import time
from collections import Counter

from flask import current_app
from supabase_auth.errors import AuthError

from app.supabase_db import get_supabase, novo_cliente
from app.utils import normalizar_busca
from app.validacoes import CRITERIOS

TAMANHO_PAGINA = 1000          # limite padrão de linhas por requisição do PostgREST
VALIDADE_CATALOGO = 300        # segundos de cache da listagem completa
MINIMO_AVALIACOES_RANKING = 5
CRITERIOS_RANKING = tuple(c for c in CRITERIOS if c != 'dificuldade')


def _paginar(montar_consulta):
    linhas, inicio = [], 0
    while True:
        lote = montar_consulta().range(inicio, inicio + TAMANHO_PAGINA - 1).execute().data
        linhas.extend(lote)
        if len(lote) < TAMANHO_PAGINA:
            return linhas
        inicio += TAMANHO_PAGINA


def _sessao_para_dict(resposta):
    sessao = getattr(resposta, 'session', None)
    if sessao is None:
        return None
    return {'access_token': sessao.access_token, 'refresh_token': sessao.refresh_token}


class UsuarioRepository:
    """Contas no Supabase Auth; nome e username ficam no user_metadata e na tabela perfis."""

    def __init__(self, cliente, fabrica_cliente=novo_cliente):
        self.cliente = cliente
        self.fabrica_cliente = fabrica_cliente

    def criar(self, nome, username, email, senha):
        """Retorna (True, id) ou (False, campo_com_erro, mensagem)."""
        if self.cliente.table('perfis').select('id').eq('username', username).limit(1).execute().data:
            return False, 'username', 'Este nome de usuário já está em uso.'
        try:
            resposta = self.cliente.auth.admin.create_user({
                'email': email, 'password': senha, 'email_confirm': True,
                'user_metadata': {'nome': nome, 'username': username}})
        except AuthError as erro:
            if getattr(erro, 'code', '') in ('email_exists', 'user_already_exists') \
                    or 'already' in str(erro).lower():
                return False, 'email', 'Este e-mail já está cadastrado.'
            raise
        usuario_id = str(resposta.user.id)
        try:
            self.cliente.table('perfis').insert(
                {'id': usuario_id, 'username': username, 'nome_completo': nome}).execute()
        except Exception:
            self.cliente.auth.admin.delete_user(usuario_id)   # não deixa conta sem perfil
            if self.cliente.table('perfis').select('id').eq('username', username).execute().data:
                return False, 'username', 'Este nome de usuário já está em uso.'
            raise
        return True, usuario_id

    def autenticar(self, username, senha):
        """Valida username + senha. Retorna {'access_token', 'refresh_token'} ou None."""
        perfil = (self.cliente.table('perfis').select('id').eq('username', username.strip().lower())
                  .limit(1).execute().data)
        if not perfil:
            return None
        try:
            email = self.cliente.auth.admin.get_user_by_id(perfil[0]['id']).user.email
            # Cliente descartável: o login não pode alterar a sessão do cliente principal.
            resposta = self.fabrica_cliente().auth.sign_in_with_password(
                {'email': email, 'password': senha})
        except AuthError:
            return None
        return _sessao_para_dict(resposta)

    def usuario_do_token(self, access_token):
        """Dados do usuário dono do token, ou None se inválido/expirado/revogado."""
        try:
            resposta = self.cliente.auth.get_user(access_token)
        except AuthError:
            return None
        usuario = getattr(resposta, 'user', None)
        if usuario is None:
            return None
        meta = usuario.user_metadata or {}
        return {'id': str(usuario.id), 'email': usuario.email,
                'nome': meta.get('nome', ''), 'username': meta.get('username', '')}

    def renovar(self, refresh_token):
        try:
            return _sessao_para_dict(self.fabrica_cliente().auth.refresh_session(refresh_token))
        except AuthError:
            return None

    def encerrar(self, access_token):
        """Revoga a sessão no servidor do Supabase (logout real)."""
        try:
            self.cliente.auth.admin.sign_out(access_token)
        except AuthError:
            pass


class ProfessorRepository:
    def __init__(self, cliente):
        self.cliente = cliente
        self._catalogo = None
        self._catalogo_em = 0.0

    def buscar_por_id(self, professor_id):
        dados = (self.cliente.table('professores').select('id,nome,departamento')
                 .eq('id', professor_id).limit(1).execute().data)
        return dados[0] if dados else None

    def listar_disciplinas(self, professor_id):
        linhas = (self.cliente.table('vw_professor_disciplina')
                  .select('disciplina_id,codigo_disciplina,disciplina')
                  .eq('professor_id', professor_id).execute().data)
        return self._disciplinas_unicas(linhas)

    @staticmethod
    def _disciplinas_unicas(linhas):
        # A view traz uma linha por turma (ano/período); o perfil usa uma por disciplina.
        unicas = {l['disciplina_id']: {'id': l['disciplina_id'], 'nome': l['disciplina'],
                                       'codigo': l['codigo_disciplina']} for l in linhas}
        return sorted(unicas.values(), key=lambda d: (d['nome'] or '', d['id']))

    def invalidar_cache(self):
        self._catalogo = None

    def _carregar_catalogo(self):
        if self._catalogo is not None and time.monotonic() - self._catalogo_em < VALIDADE_CATALOGO:
            return self._catalogo
        professores = _paginar(lambda: self.cliente.table('professores')
                               .select('id,nome,departamento').order('id'))
        vinculos = _paginar(lambda: self.cliente.table('vw_professor_disciplina')
                            .select('professor_id,disciplina_id,codigo_disciplina,disciplina')
                            .order('professor_id').order('disciplina_id'))
        avaliados = _paginar(lambda: self.cliente.table('avaliacoes')
                             .select('professor_id').order('id'))
        total = Counter(l['professor_id'] for l in avaliados)
        por_professor = {}
        for linha in vinculos:
            por_professor.setdefault(linha['professor_id'], []).append(linha)
        self._catalogo = [({**p, 'total_avaliacoes': total.get(p['id'], 0)},
                           self._disciplinas_unicas(por_professor.get(p['id'], [])))
                          for p in professores]
        self._catalogo_em = time.monotonic()
        return self._catalogo

    def listar_departamentos(self):
        """Departamentos distintos (opções do filtro), em ordem alfabética sem acento."""
        unicos = {}
        for professor, _ in self._carregar_catalogo():
            departamento = (professor.get('departamento') or '').strip()
            if departamento:
                unicos.setdefault(normalizar_busca(departamento), departamento)
        return [unicos[chave] for chave in sorted(unicos)]

    def catalogo(self, nome='', disciplina='', departamento=''):
        """[(professor, disciplinas)] filtrado sem distinguir acento/caixa/espaços,
        ordenado do mais avaliado para o menos avaliado (desempate: nome)."""
        nome_n, disciplina_n = normalizar_busca(nome), normalizar_busca(disciplina)
        departamento_n = normalizar_busca(departamento)
        resultado = []
        for professor, disciplinas in self._carregar_catalogo():
            if departamento_n and normalizar_busca(professor.get('departamento')) != departamento_n:
                continue
            if nome_n not in normalizar_busca(professor['nome']):
                continue
            if disciplina_n and not any(
                    disciplina_n in normalizar_busca(d['nome'])
                    or disciplina_n in normalizar_busca(d['codigo']) for d in disciplinas):
                continue
            resultado.append((professor, disciplinas))
        return sorted(resultado, key=lambda i: (-i[0]['total_avaliacoes'], i[0]['nome'] or '', i[0]['id']))

    def ranking(self):
        colunas = ','.join(('professor_id', *CRITERIOS))
        avaliacoes = _paginar(lambda: self.cliente.table('avaliacoes')
                             .select(colunas).order('id'))
        totais = {}
        for avaliacao in avaliacoes:
            if not all(type(avaliacao.get(c)) is int and 1 <= avaliacao[c] <= 5
                       for c in CRITERIOS):
                continue
            total = totais.setdefault(avaliacao['professor_id'], {'soma': 0, 'quantidade': 0})
            total['soma'] += sum(avaliacao[c] for c in CRITERIOS_RANKING)
            total['quantidade'] += 1
        elegiveis = {p: t for p, t in totais.items()
                     if t['quantidade'] >= MINIMO_AVALIACOES_RANKING}
        if not elegiveis:
            return []
        professores = _paginar(lambda: self.cliente.table('professores')
                               .select('id,nome,departamento').order('id'))
        resultado = []
        for professor in professores:
            total = elegiveis.get(professor['id'])
            if total:
                resultado.append({**professor, 'quantidade': total['quantidade'],
                                  'media': total['soma'] / (total['quantidade'] * len(CRITERIOS_RANKING))})
        resultado.sort(key=lambda p: (-p['media'], -p['quantidade'],
                                     normalizar_busca(p['nome']), p['id']))
        return [{**professor, 'posicao': posicao}
                for posicao, professor in enumerate(resultado, start=1)]


class AvaliacaoRepository:
    def __init__(self, cliente):
        self.cliente = cliente

    def calcular_medias(self, professor_id, disciplina_id=None):
        colunas = ','.join(CRITERIOS)
        def consulta():
            consulta = self.cliente.table('avaliacoes').select(colunas).eq('professor_id', professor_id)
            if disciplina_id is not None:
                consulta = consulta.eq('disciplina_id', disciplina_id)
            return consulta.order('id')
        linhas = _paginar(consulta)
        validas = [l for l in linhas
                   if all(type(l.get(c)) is int and 1 <= l[c] <= 5 for c in CRITERIOS)]
        medias = {c: (sum(l[c] for l in validas) / len(validas) if validas else None)
                  for c in CRITERIOS}
        return {'quantidade': len(validas), 'medias': medias}

    def salvar(self, usuario_id, professor_id, disciplina_id, notas):
        """Grava a avaliação. Retorna False se o usuário já avaliou o par professor/disciplina."""
        if any(type(notas.get(c)) is not int or not 1 <= notas[c] <= 5 for c in CRITERIOS):
            raise ValueError('Todos os critérios devem ter notas inteiras de 1 a 5.')
        turmas = (self.cliente.table('vw_professor_disciplina').select('ano,periodo')
                  .eq('professor_id', professor_id).eq('disciplina_id', disciplina_id)
                  .execute().data)
        if not turmas:
            raise ValueError('Disciplina não vinculada ao professor.')
        existente = (self.cliente.table('avaliacoes').select('id').eq('usuario_id', usuario_id)
                     .eq('professor_id', professor_id).eq('disciplina_id', disciplina_id)
                     .limit(1).execute().data)
        if existente:
            return False
        recente = max(turmas, key=lambda t: (t['ano'] or 0, t['periodo'] or 0))
        self.cliente.table('avaliacoes').insert({
            'usuario_id': usuario_id, 'professor_id': professor_id,
            'disciplina_id': disciplina_id, 'ano': recente['ano'],
            'periodo': recente['periodo'], **{c: notas[c] for c in CRITERIOS},
        }).execute()
        return True

    def _enriquecer_avaliacoes(self, avaliacoes):
        if not avaliacoes:
            return []
        professores = {
            p['id']: p['nome']
            for p in _paginar(lambda: self.cliente.table('professores').select('id,nome').order('id'))
        }
        vinculos = _paginar(
            lambda: self.cliente.table('vw_professor_disciplina')
            .select('professor_id,disciplina_id,codigo_disciplina,disciplina')
            .order('disciplina_id')
        )
        disciplinas = {}
        for v in vinculos:
            disciplinas[v['disciplina_id']] = (v.get('disciplina', ''), v.get('codigo_disciplina', ''))
        resultado = []
        for av in avaliacoes:
            disc_nome, disc_codigo = disciplinas.get(av['disciplina_id'], ('', ''))
            resultado.append({
                **av,
                'professor_nome': professores.get(av['professor_id'], ''),
                'disciplina_nome': disc_nome,
                'codigo_disciplina': disc_codigo,
            })
        return resultado

    def listar_por_usuario(self, usuario_id):
        """Lista as avaliações feitas pelo usuário com nomes de professor e disciplina."""
        linhas = _paginar(
            lambda: self.cliente.table('avaliacoes')
            .select('*')
            .eq('usuario_id', usuario_id)
            .order('id')
        )
        return self._enriquecer_avaliacoes(linhas)

    def buscar_por_id_e_usuario(self, avaliacao_id, usuario_id):
        """Retorna a avaliação enriquecida se pertencer ao usuário, ou None."""
        dados = (
            self.cliente.table('avaliacoes')
            .select('*')
            .eq('id', avaliacao_id)
            .eq('usuario_id', usuario_id)
            .limit(1)
            .execute()
            .data
        )
        if not dados:
            return None
        return self._enriquecer_avaliacoes(dados)[0]

    def atualizar(self, avaliacao_id, usuario_id, notas):
        """Atualiza as notas de uma avaliação se o usuario_id for o autor."""
        if any(type(notas.get(c)) is not int or not 1 <= notas[c] <= 5 for c in CRITERIOS):
            raise ValueError('Todos os critérios devem ter notas inteiras de 1 a 5.')
        existente = self.buscar_por_id_e_usuario(avaliacao_id, usuario_id)
        if not existente:
            return False
        payloads = {c: notas[c] for c in CRITERIOS}
        (
            self.cliente.table('avaliacoes')
            .update(payloads)
            .eq('id', avaliacao_id)
            .eq('usuario_id', usuario_id)
            .execute()
        )
        return True

    def excluir(self, avaliacao_id, usuario_id):
        """Remove a avaliação se o usuario_id for o autor."""
        existente = self.buscar_por_id_e_usuario(avaliacao_id, usuario_id)
        if not existente:
            return False
        (
            self.cliente.table('avaliacoes')
            .delete()
            .eq('id', avaliacao_id)
            .eq('usuario_id', usuario_id)
            .execute()
        )
        return True

class Repositorios:
    def __init__(self, usuarios, professores, avaliacoes):
        self.usuarios = usuarios
        self.professores = professores
        self.avaliacoes = avaliacoes


def configurar_repositorios(app):
    """Monta os repositórios do app. SUPABASE_CLIENT na config permite injetar um cliente (testes)."""
    injetado = app.config.get('SUPABASE_CLIENT')
    cliente = injetado or get_supabase()
    fabrica = (lambda: injetado) if injetado else novo_cliente
    app.extensions['repositorios'] = Repositorios(
        UsuarioRepository(cliente, fabrica), ProfessorRepository(cliente), AvaliacaoRepository(cliente))


def repositorios() -> Repositorios:
    return current_app.extensions['repositorios']
