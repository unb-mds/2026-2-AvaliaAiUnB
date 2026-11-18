"""Lógica de professores e avaliações: resolve o que as rotas exibem e registra avaliações."""
import math

from flask import abort, current_app, request

from app.repositorio import (CRITERIOS_RANKING, LIMITE_COMENTARIOS,
                             MINIMO_AVALIACOES_RANKING, ComentarioRepository,
                             repositorios)
from app.utils import normalizar_busca
from app.validacoes import CRITERIOS, validar_avaliacao, validar_comentario

MINIMO_AVALIACOES_COMPARACAO = MINIMO_AVALIACOES_RANKING


def _aplicar_destaques_comparacao(comparacao):
    """Marca quem lidera no geral e por critério entre professores com mínimo de avaliações."""
    for item in comparacao:
        qtd = item['indicadores']['quantidade']
        item['elegivel_destaque'] = qtd >= MINIMO_AVALIACOES_COMPARACAO
        item['media_geral'] = _calcular_media_geral(item['indicadores'])
        item['melhor_geral'] = False
        item['melhores_criterios'] = {c: False for c in CRITERIOS}

    elegiveis = [item for item in comparacao if item['elegivel_destaque']]
    if not elegiveis:
        return comparacao

    maior_geral = max(item['media_geral'] for item in elegiveis)
    for item in elegiveis:
        if math.isclose(item['media_geral'], maior_geral, rel_tol=1e-9, abs_tol=1e-9):
            item['melhor_geral'] = True

    for criterio in CRITERIOS:
        valores = [item['indicadores']['medias'][criterio] for item in elegiveis]
        alvo = min(valores) if criterio == 'dificuldade' else max(valores)
        for item in elegiveis:
            if math.isclose(item['indicadores']['medias'][criterio], alvo, rel_tol=1e-9, abs_tol=1e-9):
                item['melhores_criterios'][criterio] = True

    return comparacao


def _calcular_media_geral(indicadores):
    """Média dos critérios positivos (exclui dificuldade, igual ao ranking)."""
    if not indicadores['quantidade']:
        return None
    medias = indicadores['medias']
    return sum(medias[c] for c in CRITERIOS_RANKING) / len(CRITERIOS_RANKING)


def _possui_disciplinas_diferentes(comparacao):
    """Verdadeiro quando os professores comparados não compartilham nenhuma disciplina."""
    if len(comparacao) < 2:
        return False
    conjuntos = [{d['id'] for d in prof.get('disciplinas', [])} for prof in comparacao]
    return len(set.intersection(*conjuntos)) == 0


def criterios():
    return CRITERIOS


def catalogo(nome='', disciplina='', departamento=''):
    """Lista [(professor, disciplinas)] ordenada pela quantidade de avaliações."""
    return repositorios().professores.catalogo(nome, disciplina, departamento)


def departamentos():
    """Opções do filtro de departamento, vindas dos dados."""
    return repositorios().professores.listar_departamentos()


def _carregar_comparacao_legada(dados):
    repos = repositorios()
    catalogo_completo = repos.professores.catalogo()
    professores = sorted((p for p, _ in catalogo_completo),
                         key=lambda p: (p['nome'] or '', p['id']))
    por_id = {p['id']: p for p in professores}
    disciplinas_por_id = {p['id']: vinculos for p, vinculos in catalogo_completo}
    selecionados, erros = {}, {}
    for campo in ('professor_1', 'professor_2'):
        valor = dados.get(campo, '').strip()
        if not valor:
            if 'professor_2' in dados:
                erros[campo] = 'Selecione um professor.'
            continue
        try:
            professor_id = int(valor)
        except ValueError:
            erros[campo] = 'Professor inválido.'
            continue
        if professor_id not in por_id:
            erros[campo] = 'Professor não encontrado.'
        else:
            selecionados[campo] = professor_id
    if len(selecionados) == 2 and selecionados['professor_1'] == selecionados['professor_2']:
        erros['professor_2'] = 'Selecione dois professores diferentes.'
    comparacao = []
    if len(selecionados) == 2 and not erros:
        comparacao = _aplicar_destaques_comparacao([
            {**por_id[p], 'disciplinas': disciplinas_por_id.get(p, []),
             'indicadores': repos.avaliacoes.calcular_medias(p)}
            for p in selecionados.values()
        ])
    return dict(professores=professores, selecionados=selecionados,
                erros=erros, comparacao=comparacao, criterios=CRITERIOS,
                disciplinas_diferentes=_possui_disciplinas_diferentes(comparacao),
                minimo_avaliacoes_destaque=MINIMO_AVALIACOES_COMPARACAO,
                modo_legado=True, modo_livre=False)


def carregar_comparacao(dados):
    if 'disciplina_id' not in dados and 'professor_2' in dados:
        return _carregar_comparacao_legada(dados)

    repos = repositorios()
    catalogo_completo = repos.professores.catalogo()
    todos_professores_lista = sorted(
        (p for p, _ in catalogo_completo),
        key=lambda p: (p['nome'] or '', p['id']),
    )
    todos_professores = {str(p['id']): p for p in todos_professores_lista}
    disciplinas_por_professor = {str(p['id']): vinculos for p, vinculos in catalogo_completo}
    disciplinas = {str(d['id']): d for _, vinculos in catalogo_completo for d in vinculos}

    modo = dados.get('modo', '').strip()
    disciplina_id = dados.get('disciplina_id', '').strip()
    erros = {}

    selecao_previa = dados.get('professor_1', '').strip()
    professor_previo = next(
        ((p, vinculos) for p, vinculos in catalogo_completo if str(p['id']) == selecao_previa),
        None,
    )
    if selecao_previa and not professor_previo:
        erros['professores'] = 'Professor não encontrado.'
        selecao_previa = ''

    if modo != 'livre' and not disciplina_id and professor_previo:
        _, vinculos_previos = professor_previo
        for d in sorted(vinculos_previos, key=lambda item: (item['nome'] or '', item['id'])):
            d_id = str(d['id'])
            total_na_disciplina = sum(
                1 for _, v in catalogo_completo if any(str(vinc['id']) == d_id for vinc in v)
            )
            if total_na_disciplina >= 2:
                disciplina_id = d_id
                break
        if not disciplina_id:
            return _carregar_comparacao_legada(dados)

    if modo == 'livre':
        selecionados = dados.getlist('professor')
        if not selecionados and selecao_previa in todos_professores:
            selecionados = [selecao_previa]
        campos = (selecionados + ['', ''])[:max(2, len(selecionados))]
        if 'remover' in dados:
            indice = dados.get('remover', type=int)
            if indice is not None and 0 <= indice < len(campos) and len(campos) > 2:
                campos.pop(indice)
        if 'adicionar' in dados and len(campos) < len(todos_professores):
            campos.append('')

        comparacao = []
        if 'comparar' in dados:
            ids = [p for p in campos if p]
            if len(ids) < 2:
                erros['professores'] = 'Selecione pelo menos dois professores.'
            elif len(set(ids)) != len(ids):
                erros['professores'] = 'Selecione professores diferentes.'
            elif any(p not in todos_professores for p in ids):
                erros['professores'] = 'Professor não encontrado.'
            else:
                comparacao = _aplicar_destaques_comparacao([
                    {**todos_professores[p],
                     'disciplinas': disciplinas_por_professor.get(p, []),
                     'indicadores': repos.avaliacoes.calcular_medias(todos_professores[p]['id'])}
                    for p in ids
                ])

        return dict(
            disciplinas=sorted(disciplinas.values(), key=lambda d: (d['nome'] or '', d['id'])),
            disciplina=None,
            professores=todos_professores_lista,
            selecao_previa=selecao_previa,
            campos=campos,
            erros=erros,
            comparacao=comparacao,
            criterios=CRITERIOS,
            disciplinas_diferentes=_possui_disciplinas_diferentes(comparacao),
            minimo_avaliacoes_destaque=MINIMO_AVALIACOES_COMPARACAO,
            modo_livre=True,
            modo_legado=False,
        )

    disciplina = disciplinas.get(disciplina_id)
    if disciplina_id and not disciplina:
        erros['disciplina'] = 'Disciplina não encontrada.'

    professores = {
        str(p['id']): p for p, vinculos in catalogo_completo
        if any(str(d['id']) == disciplina_id for d in vinculos)
    }
    selecionados = dados.getlist('professor')
    comparacao = []
    if disciplina:
        if not selecionados and selecao_previa in professores:
            selecionados = [selecao_previa]
        if 'remover' in dados:
            indice = dados.get('remover', type=int)
            if indice is not None and 0 <= indice < len(selecionados):
                selecionados.pop(indice)
        if 'adicionar' in dados and len(selecionados) < len(professores):
            selecionados.append('')
        if 'comparar' in dados:
            ids = [p for p in selecionados if p]
            if len(ids) < 2:
                erros['professores'] = 'Selecione pelo menos dois professores.'
            elif len(set(ids)) != len(ids):
                erros['professores'] = 'Selecione professores diferentes.'
            elif any(p not in professores for p in ids):
                erros['professores'] = 'Todos os professores devem ministrar a disciplina selecionada.'
            else:
                medias = repos.avaliacoes.calcular_medias_por_disciplina(
                    disciplina['id'], [professores[p]['id'] for p in ids])
                comparacao = _aplicar_destaques_comparacao([
                    {**professores[p], 'disciplinas': [disciplina],
                     'indicadores': medias[professores[p]['id']]}
                    for p in ids
                ])

    return dict(disciplinas=sorted(disciplinas.values(), key=lambda d: (d['nome'] or '', d['id'])),
                disciplina=disciplina, professores=sorted(professores.values(),
                    key=lambda p: (p['nome'] or '', p['id'])),
                selecao_previa=selecao_previa, campos=(selecionados + ['', ''])[:max(2, len(selecionados))],
                erros=erros, comparacao=comparacao, criterios=CRITERIOS,
                disciplinas_diferentes=False, modo_livre=False, modo_legado=False,
                minimo_avaliacoes_destaque=MINIMO_AVALIACOES_COMPARACAO)


def carregar_ranking(departamento=''):
    repos = repositorios()
    lista_departamentos = repos.professores.listar_departamentos()
    chave = normalizar_busca(departamento)
    departamento_ativo = next(
        (dep for dep in lista_departamentos if normalizar_busca(dep) == chave),
        departamento.strip(),
    ) if chave else ''
    return (
        repos.professores.ranking(departamento_ativo),
        MINIMO_AVALIACOES_RANKING,
        lista_departamentos,
        departamento_ativo,
    )

def carregar_perfil(professor_id):
    professores = repositorios().professores
    professor = professores.buscar_por_id(professor_id)
    if professor is None:
        abort(404)
    disciplinas = professores.listar_disciplinas(professor_id)
    origem = request.form if request.method == 'POST' else request.args
    identificador = origem.get('disciplina_id')
    if identificador is None:
        if request.method == 'POST':
            abort(400, description='Informe a disciplina avaliada.')
        disciplina = disciplinas[0] if disciplinas else None
    else:
        try:
            disciplina_id = int(identificador)
        except (ValueError, TypeError):
            abort(400, description='Disciplina inválida.')
        disciplina = next((d for d in disciplinas if d['id'] == disciplina_id), None)
        if disciplina is None:
            abort(404, description='Disciplina não vinculada ao professor.')
    return professor, disciplinas, disciplina


def _inteiro_ou_none(bruto):
    try:
        return int(bruto)
    except (TypeError, ValueError):
        return None


def filtro_de_comentarios(bruto, disciplinas):
    """id da disciplina do filtro, ou None (= todas) se vazio, ilegível ou de outro professor."""
    disciplina_id = _inteiro_ou_none(bruto)
    return disciplina_id if any(d['id'] == disciplina_id for d in disciplinas) else None


def disciplina_das_medias(disciplinas, bruto):
    """Disciplina das médias a mostrar depois de um POST: a informada se for do professor,
    senão a primeira (sem 404, ao contrário de carregar_perfil)."""
    disciplina_id = _inteiro_ou_none(bruto)
    return next((d for d in disciplinas if d['id'] == disciplina_id),
                disciplinas[0] if disciplinas else None)


def carregar_professor(professor_id):
    professor = repositorios().professores.buscar_por_id(professor_id)
    if professor is None:
        abort(404)
    return professor


def listar_disciplinas(professor_id):
    return repositorios().professores.listar_disciplinas(professor_id)


def validar_novo_comentario(disciplinas, disciplina_bruta, texto):
    """(disciplina_id ou None, erros): a disciplina precisa ser uma das do professor."""
    erros = {}
    disciplina_id = _inteiro_ou_none(disciplina_bruta)
    if not any(d['id'] == disciplina_id for d in disciplinas):
        disciplina_id = None
        erros['disciplina'] = 'Escolha a disciplina.'
    _, erro = validar_comentario(texto)
    if erro:
        erros['texto'] = erro
    return disciplina_id, erros


def publicar_comentario(usuario, professor_id, disciplina_id, texto):
    """Grava o comentário do usuário logado. ValueError se o repositório recusar."""
    return repositorios().comentarios.criar(usuario['id'], professor_id, disciplina_id, texto)


def carregar_comentario_do_usuario(comentario_id, usuario):
    """Comentário do usuário logado; 404 se não existir ou for de outra pessoa (nunca 403)."""
    comentario = repositorios().comentarios.buscar_do_usuario(comentario_id, usuario['id'])
    if comentario is None:
        abort(404, description='Comentário não encontrado.')
    return comentario


def editar_comentario(comentario_id, usuario, disciplina_id, texto):
    """Muda só texto e disciplina. 404 se o comentário não for do usuário; ValueError se recusado."""
    if not repositorios().comentarios.atualizar(comentario_id, usuario['id'], disciplina_id, texto):
        abort(404, description='Comentário não encontrado.')
    return True


def excluir_comentario(comentario_id, usuario):
    if not repositorios().comentarios.excluir(comentario_id, usuario['id']):
        abort(404, description='Comentário não encontrado.')
    return True


def carregar_comentarios(professor_id, disciplinas, filtro_bruto, usuario):
    """Contexto da seção de comentários do perfil. Nunca levanta: se a consulta falhar,
    registra o erro e devolve erro_comentarios=True para o resto do perfil continuar."""
    filtro = filtro_de_comentarios(filtro_bruto, disciplinas)
    contexto = dict(comentarios=[], ha_mais=False, filtro_comentarios=filtro,
                    erro_comentarios=False, limite_comentarios=LIMITE_COMENTARIOS)
    try:
        comentarios, ha_mais = repositorios().comentarios.listar_por_professor(
            professor_id, filtro, usuario['id'] if usuario else None)
        for comentario in comentarios:
            comentario['data'] = ComentarioRepository.formatar_data(comentario['criado_em'])
    except Exception:
        current_app.logger.exception('Falha ao carregar os comentários do professor %s', professor_id)
        contexto['erro_comentarios'] = True
    else:
        contexto.update(comentarios=comentarios, ha_mais=ha_mais)
    return contexto


def indicadores(professor_id, disciplina_id):
    return repositorios().avaliacoes.calcular_medias(professor_id, disciplina_id)


def validar_notas(dados):
    return validar_avaliacao(dados, CRITERIOS)


def registrar_avaliacao(usuario, professor_id, disciplina_id, notas):
    """Grava a avaliação do usuário logado. False se ele já avaliou este par."""
    repos = repositorios()
    salvou = repos.avaliacoes.salvar(usuario['id'], professor_id, disciplina_id, notas)
    if salvou:
        repos.professores.invalidar_cache()   # a listagem ordena por total de avaliações
    return salvou


def listar_avaliacoes_usuario(usuario):
    return repositorios().avaliacoes.listar_por_usuario(usuario['id'])


def carregar_avaliacao_do_usuario(avaliacao_id, usuario):
    avaliacao = repositorios().avaliacoes.buscar_por_id_e_usuario(avaliacao_id, usuario['id'])
    if avaliacao is None:
        abort(404, description='Avaliação não encontrada.')
    return avaliacao


def editar_avaliacao(avaliacao_id, usuario, notas):
    repos = repositorios()
    atualizou = repos.avaliacoes.atualizar(avaliacao_id, usuario['id'], notas)
    if not atualizou:
        abort(404, description='Avaliação não encontrada.')
    repos.professores.invalidar_cache()
    return True


def excluir_avaliacao(avaliacao_id, usuario):
    repos = repositorios()
    excluiu = repos.avaliacoes.excluir(avaliacao_id, usuario['id'])
    if not excluiu:
        abort(404, description='Avaliação não encontrada.')
    repos.professores.invalidar_cache()
    return True