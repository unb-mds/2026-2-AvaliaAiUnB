"""Lógica de professores e avaliações: resolve o que as rotas exibem e registra avaliações."""
import math

from flask import abort, current_app, request, url_for

from app.repositorio import (CRITERIOS_RANKING, LIMITE_COMENTARIOS, LIMITE_SUGESTOES,
                             MAXIMO_SUGESTOES, MINIMO_AVALIACOES_RANKING,
                             ComentarioRepository, repositorios)
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


def catalogo(nome='', disciplina='', departamento='', q=''):
    """Lista [(professor, disciplinas)] ordenada pela quantidade de avaliações.
    `q` é a busca unificada (professor, disciplina ou departamento)."""
    return repositorios().professores.catalogo(nome, disciplina, departamento, termo=q)


PROFESSORES_POR_PAGINA = 100   # mesmo tamanho de página usado em lista_professores.html


def paginar_catalogo(itens, pagina_bruta):
    """Paginação da Consulta: pagina, total_paginas, total, inicio, fim (índices de fatia)
    e os `itens` da página. Página ilegível ou fora do intervalo vira a mais próxima."""
    total = len(itens)
    total_paginas = max(1, (total + PROFESSORES_POR_PAGINA - 1) // PROFESSORES_POR_PAGINA)
    pagina = min(max(_inteiro_ou_none(pagina_bruta) or 1, 1), total_paginas)
    inicio = (pagina - 1) * PROFESSORES_POR_PAGINA
    fim = min(inicio + PROFESSORES_POR_PAGINA, total)
    return dict(pagina=pagina, total_paginas=total_paginas, total=total,
                inicio=inicio, fim=fim, itens=itens[inicio:fim])


def _professores_da_pagina(itens, pagina_bruta):
    return paginar_catalogo(itens, pagina_bruta)['itens']


def _texto_avaliacoes(quantidade):
    return f"{quantidade} {'avaliação' if quantidade == 1 else 'avaliações'}"


def dificuldades_da_pagina(itens, pagina_bruta):
    """{professor_id: {disciplina_id: {valor, texto_dificuldade, texto_avaliacoes}}} para
    cada disciplina dos professores da página da Consulta (uma consulta só ao banco).

    `valor` (1 a 5, uma casa) alimenta a barra; sem avaliação de dificuldade ele é None
    e `texto_dificuldade` também."""
    pagina = _professores_da_pagina(itens, pagina_bruta)
    medias = repositorios().avaliacoes.dificuldade_por_professor_disciplina(
        [professor['id'] for professor, _ in pagina])
    resultado = {}
    for professor, disciplinas in pagina:
        do_professor = medias.get(professor['id'], {})
        resultado[professor['id']] = {}
        for disciplina in disciplinas:
            dado = do_professor.get(disciplina['id'], {'media': None, 'quantidade': 0})
            valor = dado['media']
            resultado[professor['id']][disciplina['id']] = {
                'valor': valor,
                'texto_dificuldade': (None if valor is None
                                      else f"Dificuldade {valor:.1f}".replace('.', ',') + '/5'),
                'quantidade': dado['quantidade'],
                'texto_avaliacoes': _texto_avaliacoes(dado['quantidade'])}
    return resultado


MAXIMO_DISCIPLINAS_SEM_EXTRAS = 5   # até aqui o cartão mostra todas as disciplinas
DISCIPLINAS_COM_EXTRAS = 4          # acima disso, só estas aparecem; o resto vai no <details>


def organizar_disciplinas(itens, dificuldades):
    """{professor_id: {'visiveis': [...], 'extras': [...]}} para os cartões da Consulta.

    Nenhuma disciplina some. Ordem: mais avaliações primeiro, depois as sem avaliações;
    empate por nome. Até MAXIMO_DISCIPLINAS_SEM_EXTRAS ficam todas visíveis; com mais,
    só as DISCIPLINAS_COM_EXTRAS primeiras e as demais em `extras`."""
    resultado = {}
    for professor, disciplinas in itens:
        do_professor = dificuldades.get(professor['id'], {})
        ordenadas = sorted(disciplinas, key=lambda d: (
            -(do_professor.get(d['id']) or {}).get('quantidade', 0),
            normalizar_busca(d['nome']), d['id']))
        if len(ordenadas) <= MAXIMO_DISCIPLINAS_SEM_EXTRAS:
            resultado[professor['id']] = {'visiveis': ordenadas, 'extras': []}
        else:
            resultado[professor['id']] = {'visiveis': ordenadas[:DISCIPLINAS_COM_EXTRAS],
                                          'extras': ordenadas[DISCIPLINAS_COM_EXTRAS:]}
    return resultado


ROTULOS_TIPO = {'professor': 'Professor', 'disciplina': 'Disciplina',
                'departamento': 'Departamento'}
# Contextos da busca unificada: tipos sugeridos e para onde cada sugestão leva.
CONTEXTOS_BUSCA = {
    'consulta': ('professor', 'disciplina', 'departamento'),
    'comparacao': ('professor', 'disciplina'),
}


def _url_da_sugestao(sugestao, contexto):
    tipo, valor = sugestao['tipo'], sugestao['id']
    if contexto == 'comparacao':
        campo = 'professor_1' if tipo == 'professor' else 'disciplina_id'
        return url_for('professores.comparar', **{campo: valor})
    if tipo == 'professor':
        return url_for('professores.perfil', professor_id=valor)
    if tipo == 'disciplina':
        return url_for('professores.listar', disciplina=sugestao['detalhe'] or sugestao['texto'])
    return url_for('professores.listar', departamento=valor)


def sugestoes(termo, limite_bruto=None, contexto_bruto=None):
    """Sugestões da busca unificada prontas para o JSON: cada uma com tipo, rótulo do
    tipo, texto, detalhe e a URL de destino no contexto (Consulta ou Comparação)."""
    contexto = contexto_bruto if contexto_bruto in CONTEXTOS_BUSCA else 'consulta'
    limite = _inteiro_ou_none(limite_bruto)
    limite = LIMITE_SUGESTOES if limite is None else max(1, min(limite, MAXIMO_SUGESTOES))
    encontradas = repositorios().professores.sugerir(
        (termo or '')[:100], limite, CONTEXTOS_BUSCA[contexto])
    return [{'tipo': s['tipo'], 'tipo_rotulo': ROTULOS_TIPO[s['tipo']], 'texto': s['texto'],
             'detalhe': s['detalhe'], 'url': _url_da_sugestao(s, contexto)}
            for s in encontradas]


MAXIMO_DISCIPLINAS_NA_SUGESTAO = 3  # disciplinas citadas ao lado do nome; o resto vira "+N"


def resumir_disciplinas(disciplinas, maximo=MAXIMO_DISCIPLINAS_NA_SUGESTAO):
    """'CÁLCULO 1 (FGA0001), FÍSICA 1 (FGA0002) +2' para mostrar ao lado do professor."""
    textos = [f"{d['nome']} ({d['codigo']})" if d.get('codigo') else d['nome']
              for d in disciplinas[:maximo]]
    extras = len(disciplinas) - maximo
    return ', '.join(textos) + (f' +{extras}' if extras > 0 else '')


def sugestoes_professores(termo, limite_bruto=None, departamento=''):
    """Professores para os campos de seleção da comparação (JSON): id, nome,
    departamento e um resumo das disciplinas que ministra."""
    limite = _inteiro_ou_none(limite_bruto)
    limite = LIMITE_SUGESTOES if limite is None else max(1, min(limite, MAXIMO_SUGESTOES))
    encontrados = repositorios().professores.sugerir_professores(
        (termo or '')[:100], limite, (departamento or '')[:200])
    return [{'id': p['id'], 'texto': p['nome'], 'detalhe': p['departamento'],
             'disciplinas': resumir_disciplinas(p['disciplinas']),
             'casou_disciplina': p['casou_disciplina']}
            for p in encontrados]


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

        # Filtro por departamento (#239): encurta a lista de opções, inclusive sem
        # JavaScript. Professores já escolhidos continuam como opção, mesmo de outro
        # departamento, para a seleção não se perder ao filtrar.
        departamentos = repos.professores.listar_departamentos()
        pedido = normalizar_busca(dados.get('departamento', ''))
        departamento = next((d for d in departamentos if normalizar_busca(d) == pedido), '')
        opcoes = [p for p in todos_professores_lista
                  if not departamento or str(p['id']) in campos
                  or normalizar_busca(p.get('departamento')) == pedido]

        # Departamento e disciplinas de cada professor já escolhido, mostrados abaixo do campo.
        escolhidos = {p: ' · '.join(filter(None, (
                          todos_professores[p].get('departamento'),
                          resumir_disciplinas(sorted(
                              disciplinas_por_professor.get(p, []),
                              key=lambda d: (normalizar_busca(d['nome']), d['id']))))))
                      for p in campos if p in todos_professores}

        return dict(
            disciplinas=sorted(disciplinas.values(), key=lambda d: (d['nome'] or '', d['id'])),
            disciplina=None,
            professores=opcoes,
            escolhidos=escolhidos,
            total_professores=len(todos_professores_lista),
            departamentos=departamentos,
            departamento=departamento,
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
        contexto['reacoes_disponiveis'] = True
        try:
            reacoes = repositorios().comentarios.reacoes(
                [c['id'] for c in comentarios], usuario['id'] if usuario else None)
            for comentario in comentarios:
                comentario.update(reacoes[comentario['id']])
        except Exception as erro:
            # A página segue acessível quando a migração das reações ainda não foi aplicada.
            current_app.logger.warning('Reações indisponíveis (%s).', type(erro).__name__)
            contexto['reacoes_disponiveis'] = False
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
