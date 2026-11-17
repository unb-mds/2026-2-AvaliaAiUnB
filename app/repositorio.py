"""Repositórios sobre o Supabase: usuários (Auth + perfis), professores e avaliações.

Tabelas usadas: auth.users (via Supabase Auth), perfis, professores, disciplinas,
turmas, avaliacoes e a view vw_professor_disciplina. `repositorios()` entrega as
instâncias configuradas em create_app.
"""
import re
import secrets
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from flask import current_app
from httpx import RequestError
from supabase_auth.errors import AuthError
from supabase_auth.helpers import generate_pkce_challenge, generate_pkce_verifier

from app.supabase_db import get_supabase, novo_cliente
from app.utils import normalizar_busca
from app.validacoes import CRITERIOS, validar_comentario

LIMITE_COMENTARIOS = 50        # comentários por listagem; o "ver mais" fica para depois
COLUNAS_AVALIACAO = ','.join(('id', 'usuario_id', 'professor_id', 'disciplina_id',
                                  'ano', 'periodo', *CRITERIOS))
MAXIMO_NOME_PERFIL = 100      # perfis.nome_completo é VARCHAR(100)
TENTATIVAS_USERNAME = 5
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


def _username_base(email):
    """Parte local do e-mail no formato aceito para username (3 a 30 de [a-z0-9._])."""
    local = re.sub(r'[^a-z0-9._]', '', (email or '').split('@')[0].lower())[:30]
    return local if len(local) >= 3 else 'estudante'


def _nome_do_google(meta, email):
    nome = (meta.get('full_name') or meta.get('name') or (email or '').split('@')[0]).strip()
    return (nome or 'Estudante')[:MAXIMO_NOME_PERFIL]


class UsuarioRepository:
    """Contas no Supabase Auth (só login com Google); nome e username ficam no user_metadata e em perfis."""

    def __init__(self, cliente, fabrica_cliente=novo_cliente):
        self.cliente = cliente
        self.fabrica_cliente = fabrica_cliente

    def email_verificado(self, usuario_id, endereco_sha256):
        resposta = (self.cliente.table('emails_verificados').select('usuario_id')
                    .eq('usuario_id', usuario_id).eq('endereco_sha256', endereco_sha256)
                    .limit(1).execute())
        return bool(resposta.data)

    def gravar_email_verificado(self, usuario_id, endereco_sha256):
        self.cliente.table('emails_verificados').upsert([{
            'usuario_id': usuario_id, 'endereco_sha256': endereco_sha256,
        }], on_conflict='usuario_id').execute()

    def url_login_google(self, redirect_to):
        """(url, verificador) para iniciar o login com Google no Supabase Auth.

        Fluxo PKCE: o verificador fica com o servidor (sessão do Flask) e só ele
        consegue trocar o código devolvido pelo Supabase por uma sessão.
        """
        verificador = generate_pkce_verifier()
        parametros = urlencode({
            'provider': 'google',
            'redirect_to': redirect_to,
            'code_challenge': generate_pkce_challenge(verificador),
            'code_challenge_method': 's256',
        })
        return f'{self.cliente.auth_url}/authorize?{parametros}', verificador

    def entrar_com_google(self, codigo, verificador):
        """Troca o código do retorno do Google por uma sessão e garante o perfil.

        Quem já tem conta com o mesmo e-mail é vinculado pelo próprio Supabase à
        conta existente (mesmo id), então perfil e avaliações continuam os mesmos.
        """
        try:
            resposta = self.fabrica_cliente().auth.exchange_code_for_session(
                {'auth_code': codigo, 'code_verifier': verificador})
        except AuthError as erro:
            current_app.logger.warning("Falha no login com Google: %s", type(erro).__name__)
            return None
        sessao = _sessao_para_dict(resposta)
        usuario = getattr(resposta, 'user', None)
        if sessao is None or usuario is None:
            return None
        self._garantir_perfil(usuario)
        return sessao

    def _garantir_perfil(self, usuario):
        """Cria o perfil de quem entrou pelo Google pela primeira vez e sincroniza o metadata."""
        usuario_id = str(usuario.id)
        meta = usuario.user_metadata or {}
        perfil = (self.cliente.table('perfis').select('username,nome_completo')
                  .eq('id', usuario_id).limit(1).execute().data)
        if perfil:
            username, nome = perfil[0]['username'], perfil[0]['nome_completo']
        else:
            nome = _nome_do_google(meta, usuario.email)
            username = self._inserir_perfil(usuario_id, nome, usuario.email)
        if meta.get('username') != username or not meta.get('nome'):
            self.cliente.auth.admin.update_user_by_id(
                usuario_id, {'user_metadata': {'nome': meta.get('nome') or nome,
                                               'username': username}})

    def _inserir_perfil(self, usuario_id, nome, email):
        """Insere o perfil com um username livre derivado do e-mail. Retorna o username."""
        base = _username_base(email)
        for tentativa in range(TENTATIVAS_USERNAME):
            username = base if tentativa == 0 else f'{base[:25]}{secrets.randbelow(10 ** 5):05d}'
            if self.cliente.table('perfis').select('id').eq('username', username).limit(1).execute().data:
                continue
            try:
                self.cliente.table('perfis').insert(
                    {'id': usuario_id, 'username': username, 'nome_completo': nome}).execute()
                return username
            except Exception:
                # Corrida: outro retorno do mesmo usuário criou o perfil antes deste.
                existente = (self.cliente.table('perfis').select('username')
                             .eq('id', usuario_id).limit(1).execute().data)
                if existente:
                    return existente[0]['username']
        raise RuntimeError('Não foi possível gerar um nome de usuário livre.')

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
                'nome': meta.get('nome') or meta.get('full_name') or meta.get('name') or '',
                'username': meta.get('username', '')}

    def renovar(self, refresh_token):
        try:
            return _sessao_para_dict(self.fabrica_cliente().auth.refresh_session(refresh_token))
        except AuthError:
            return None

    def encerrar(self, access_token):
        """Revoga a sessão no servidor do Supabase (logout real)."""
        try:
            self.cliente.auth.admin.sign_out(access_token)
        except (AuthError, RequestError) as erro:
            current_app.logger.warning("Falha ao revogar a sessão no Supabase (%s).",
                                       type(erro).__name__)


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
                             .select(','.join(('professor_id', *CRITERIOS))).order('id'))
        total = Counter(l['professor_id'] for l in avaliados)
        # Média geral como no ranking: critérios sem a dificuldade, só avaliações válidas.
        somas = {}
        for l in avaliados:
            if all(type(l.get(c)) is int and 1 <= l[c] <= 5 for c in CRITERIOS):
                soma = somas.setdefault(l['professor_id'], [0, 0])
                soma[0] += sum(l[c] for c in CRITERIOS_RANKING)
                soma[1] += 1
        medias = {pid: s / (n * len(CRITERIOS_RANKING)) for pid, (s, n) in somas.items()}
        por_professor = {}
        for linha in vinculos:
            por_professor.setdefault(linha['professor_id'], []).append(linha)
        self._catalogo = [({**p, 'total_avaliacoes': total.get(p['id'], 0),
                            'media_geral': medias.get(p['id'])},
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
        return self._resumir_notas(linhas)

    def calcular_medias_por_disciplina(self, disciplina_id, professor_ids):
        colunas = ','.join(('professor_id', *CRITERIOS))
        linhas = _paginar(lambda: self.cliente.table('avaliacoes').select(colunas)
                          .eq('disciplina_id', disciplina_id).order('id'))
        por_professor = {professor_id: [] for professor_id in professor_ids}
        for linha in linhas:
            if linha['professor_id'] in por_professor:
                por_professor[linha['professor_id']].append(linha)
        return {professor_id: self._resumir_notas(notas)
                for professor_id, notas in por_professor.items()}

    @staticmethod
    def _resumir_notas(linhas):
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
            .select(COLUNAS_AVALIACAO)
            .eq('usuario_id', usuario_id)
            .order('id')
        )
        return self._enriquecer_avaliacoes(linhas)

    def buscar_por_id_e_usuario(self, avaliacao_id, usuario_id):
        """Retorna a avaliação enriquecida se pertencer ao usuário, ou None."""
        dados = (
            self.cliente.table('avaliacoes')
            .select(COLUNAS_AVALIACAO)
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

class ComentarioRepository:
    """Comentários no perfil do professor (tabela comentarios).

    O backend usa a service key, que ignora RLS: toda regra de autoria e de vínculo
    entre professor e disciplina é conferida aqui. O e-mail e o id da conta do autor
    nunca saem deste repositório; só o username público.
    """

    def __init__(self, cliente):
        self.cliente = cliente

    def _disciplinas_do_professor(self, professor_id):
        """{disciplina_id: (nome, codigo)} das disciplinas ministradas pelo professor."""
        linhas = (self.cliente.table('vw_professor_disciplina')
                  .select('disciplina_id,codigo_disciplina,disciplina')
                  .eq('professor_id', professor_id).execute().data)
        return {l['disciplina_id']: (l['disciplina'], l['codigo_disciplina']) for l in linhas}

    @staticmethod
    def _ler_data(valor):
        """datetime de uma data ISO 8601 do PostgREST, ou None se não der para ler.

        Aceita 1 a 6 casas decimais nos segundos e o sufixo Z (o PostgREST corta zeros
        à direita das frações, e o fromisoformat de versões antigas exige 3 ou 6 casas).
        """
        if not isinstance(valor, str):
            return None
        texto = valor.strip()
        if texto[-1:] in ('Z', 'z'):
            texto = texto[:-1] + '+00:00'
        texto = re.sub(r'(\.\d{1,6})\d*', lambda m: m.group(1).ljust(7, '0'), texto, count=1)
        try:
            return datetime.fromisoformat(texto)
        except ValueError:
            return None

    @classmethod
    def formatar_data(cls, valor):
        """dd/mm/aaaa no horário de Brasília (UTC-3, sem horário de verão); '' se ilegível."""
        data = cls._ler_data(valor)
        if data is None:
            return ''
        if data.tzinfo is None:
            data = data.replace(tzinfo=timezone.utc)
        return data.astimezone(timezone(timedelta(hours=-3))).strftime('%d/%m/%Y')

    @classmethod
    def _foi_editado(cls, linha):
        """True se atualizado_em for depois de criado_em. Data ilegível: False, sem exceção."""
        criado = cls._ler_data(linha.get('criado_em'))
        atualizado = cls._ler_data(linha.get('atualizado_em'))
        if criado is None or atualizado is None:
            return False
        try:
            return atualizado > criado
        except TypeError:      # uma com fuso e outra sem
            return False

    def listar_por_professor(self, professor_id, disciplina_id=None, usuario_atual_id=None):
        """(comentarios, ha_mais): os LIMITE_COMENTARIOS mais recentes não ocultados.

        disciplina_id=None lista todas as disciplinas. `ha_mais` é True quando existem
        comentários além do limite (busca-se um a mais só para saber isso).
        """
        consulta = (self.cliente.table('comentarios')
                    .select('id,usuario_id,disciplina_id,texto,criado_em,atualizado_em')
                    .eq('professor_id', professor_id).is_('ocultado_em', 'null'))
        if disciplina_id is not None:
            consulta = consulta.eq('disciplina_id', disciplina_id)
        linhas = (consulta.order('criado_em', desc=True).order('id', desc=True)
                  .limit(LIMITE_COMENTARIOS + 1).execute().data)
        ha_mais = len(linhas) > LIMITE_COMENTARIOS
        linhas = linhas[:LIMITE_COMENTARIOS]
        if not linhas:
            return [], False

        ids_autores = sorted({l['usuario_id'] for l in linhas})
        autores = {p['id']: p['username'] for p in
                   self.cliente.table('perfis').select('id,username')
                   .in_('id', ids_autores).execute().data}
        disciplinas = self._disciplinas_do_professor(professor_id)
        comentarios = []
        for l in linhas:
            nome, codigo = disciplinas.get(l['disciplina_id'], ('', ''))
            comentarios.append({
                'id': l['id'],
                'texto': l['texto'],
                'username': autores.get(l['usuario_id'], ''),
                'disciplina_nome': nome,
                'disciplina_codigo': codigo,
                'criado_em': l['criado_em'],
                'editado': self._foi_editado(l),
                'e_meu': usuario_atual_id is not None and l['usuario_id'] == usuario_atual_id,
            })
        return comentarios, ha_mais

    def buscar_do_usuario(self, comentario_id, usuario_id):
        """Comentário se pertencer ao usuário, senão None (a rota responde 404)."""
        dados = (self.cliente.table('comentarios')
                 .select('id,professor_id,disciplina_id,texto')
                 .eq('id', comentario_id).eq('usuario_id', usuario_id).limit(1).execute().data)
        if not dados:
            return None
        linha = dados[0]
        nome, codigo = self._disciplinas_do_professor(linha['professor_id']).get(
            linha['disciplina_id'], ('', ''))
        return {'id': linha['id'], 'professor_id': linha['professor_id'],
                'disciplina_id': linha['disciplina_id'], 'texto': linha['texto'],
                'disciplina_nome': nome, 'disciplina_codigo': codigo}

    def criar(self, usuario_id, professor_id, disciplina_id, texto):
        """Grava o comentário do usuário e devolve o id novo.

        ValueError se o texto for inválido ou a disciplina não for do professor.
        """
        texto, erro = validar_comentario(texto)
        if erro:
            raise ValueError(erro)
        if disciplina_id not in self._disciplinas_do_professor(professor_id):
            raise ValueError('Disciplina não vinculada ao professor.')
        criado = self.cliente.table('comentarios').insert({
            'usuario_id': usuario_id, 'professor_id': professor_id,
            'disciplina_id': disciplina_id, 'texto': texto,
        }).execute().data
        return criado[0]['id']

    def atualizar(self, comentario_id, usuario_id, disciplina_id, texto):
        """Muda só texto e disciplina. False se o comentário não é do usuário.

        ValueError se o texto for inválido ou a disciplina não for do professor
        do comentário (o professor nunca muda).
        """
        texto, erro = validar_comentario(texto)
        if erro:
            raise ValueError(erro)
        existente = self.buscar_do_usuario(comentario_id, usuario_id)
        if not existente:
            return False
        if disciplina_id not in self._disciplinas_do_professor(existente['professor_id']):
            raise ValueError('Disciplina não vinculada ao professor.')
        atualizadas = (self.cliente.table('comentarios')
                       .update({'texto': texto, 'disciplina_id': disciplina_id})
                       .eq('id', comentario_id).eq('usuario_id', usuario_id).execute().data)
        return bool(atualizadas)

    def excluir(self, comentario_id, usuario_id):
        """Apaga o comentário se for do usuário. False se nada foi afetado."""
        apagadas = (self.cliente.table('comentarios').delete()
                    .eq('id', comentario_id).eq('usuario_id', usuario_id).execute().data)
        return bool(apagadas)


class Repositorios:
    def __init__(self, usuarios, professores, avaliacoes, comentarios=None):
        self.usuarios = usuarios
        self.professores = professores
        self.avaliacoes = avaliacoes
        self.comentarios = comentarios


def configurar_repositorios(app):
    """Monta os repositórios do app. SUPABASE_CLIENT na config permite injetar um cliente (testes)."""
    injetado = app.config.get('SUPABASE_CLIENT')
    cliente = injetado or get_supabase()
    fabrica = (lambda: injetado) if injetado else novo_cliente
    app.extensions['repositorios'] = Repositorios(
        UsuarioRepository(cliente, fabrica), ProfessorRepository(cliente),
        AvaliacaoRepository(cliente), ComentarioRepository(cliente))


def repositorios() -> Repositorios:
    return current_app.extensions['repositorios']