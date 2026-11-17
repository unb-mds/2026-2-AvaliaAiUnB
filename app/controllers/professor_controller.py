"""Lógica de professores e avaliações: resolve o que as rotas exibem e registra avaliações."""
from flask import abort, request

from app.repositorio import MINIMO_AVALIACOES_RANKING, repositorios
from app.validacoes import CRITERIOS, validar_avaliacao


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
    professores = sorted((p for p, _ in repos.professores.catalogo()),
                         key=lambda p: (p['nome'] or '', p['id']))
    por_id = {p['id']: p for p in professores}
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
        comparacao = [{**por_id[p], 'indicadores': repos.avaliacoes.calcular_medias(p)}
                      for p in selecionados.values()]
    return dict(professores=professores, selecionados=selecionados,
                erros=erros, comparacao=comparacao, criterios=CRITERIOS, modo_legado=True)


def carregar_comparacao(dados):
    if 'disciplina_id' not in dados and 'professor_2' in dados:
        return _carregar_comparacao_legada(dados)

    repos = repositorios()
    catalogo = repos.professores.catalogo()
    disciplinas = {str(d['id']): d for _, vinculos in catalogo for d in vinculos}
    disciplina_id = dados.get('disciplina_id', '')
    erros = {}

    selecao_previa = dados.get('professor_1', '').strip()
    professor_previo = next(
        ((p, vinculos) for p, vinculos in catalogo if str(p['id']) == selecao_previa),
        None,
    )
    if selecao_previa and not professor_previo:
        erros['professores'] = 'Professor não encontrado.'
        selecao_previa = ''

    if not disciplina_id and professor_previo:
        _, vinculos_previos = professor_previo
        for d in sorted(vinculos_previos, key=lambda item: (item['nome'] or '', item['id'])):
            d_id = str(d['id'])
            total_na_disciplina = sum(
                1 for _, v in catalogo if any(str( vinc['id']) == d_id for vinc in v)
            )
            if total_na_disciplina >= 2:
                disciplina_id = d_id
                break
        if not disciplina_id:
            return _carregar_comparacao_legada(dados)

    disciplina = disciplinas.get(disciplina_id)
    if disciplina_id and not disciplina:
        erros['disciplina'] = 'Disciplina não encontrada.'

    professores = {
        str(p['id']): p for p, vinculos in catalogo
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
                comparacao = [{**professores[p], 'indicadores': medias[professores[p]['id']]}
                              for p in ids]

    return dict(disciplinas=sorted(disciplinas.values(), key=lambda d: (d['nome'] or '', d['id'])),
                disciplina=disciplina, professores=sorted(professores.values(),
                    key=lambda p: (p['nome'] or '', p['id'])),
                selecao_previa=selecao_previa, campos=(selecionados + ['', ''])[:max(2, len(selecionados))],
                erros=erros, comparacao=comparacao, criterios=CRITERIOS)


def carregar_ranking():
    return repositorios().professores.ranking(), MINIMO_AVALIACOES_RANKING


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
