"""Telas de professores: listagem, perfil com médias por disciplina e avaliação."""
from flask import Blueprint, abort, jsonify, redirect, render_template, request, url_for

from app.controllers import professor_controller as controller
from app.controllers.session_controller import (login_required, obter_usuario_atual,
                                                sanitizar_destino)
from app.seguranca import limitar_avaliacao, limitar_comentario, is_safe_url

professor_bp = Blueprint('professores', __name__)

CAMPOS_FILTRO = ('nome', 'disciplina', 'departamento')


@professor_bp.get('/comparar')
def comparar():
    contexto = controller.carregar_comparacao(request.args)
    return render_template('comparacao.html', **contexto,
                           usuario=obter_usuario_atual()), 400 if contexto['erros'] else 200
@professor_bp.get('/ranking')
def ranking():
    professores, minimo_avaliacoes = controller.carregar_ranking()
    return render_template('ranking.html', ranking=professores,
                           minimo_avaliacoes=minimo_avaliacoes,
                           usuario=obter_usuario_atual())


@professor_bp.get('/professores')
def listar():
    filtros = {campo: request.args.get(campo, '').strip() for campo in CAMPOS_FILTRO}
    return render_template('lista_professores.html', catalogo=controller.catalogo(**filtros),
                           filtros=filtros, departamentos=controller.departamentos(),
                           usuario=obter_usuario_atual())


def _next_seguro(valor):
    """Destino do "Voltar": o informado se for seguro, senão a consulta."""
    return valor if is_safe_url(valor) else url_for('professores.listar')


def _url_perfil(professor_id, next_url, disciplina, filtro):
    """URL do perfil (com #comentarios) preservando next, a disciplina das médias e o filtro."""
    return url_for('professores.perfil', professor_id=professor_id, next=next_url,
                   disciplina_id=disciplina['id'] if disciplina else None,
                   comentarios_disciplina=filtro, _anchor='comentarios')


def _renderizar_perfil(professor, disciplinas, disciplina, next_url, filtro_bruto,
                       status=200, **extra):
    """Monta a página do perfil. `extra` traz o estado do formulário de comentário em caso de erro."""
    professor_id = professor['id']
    usuario = obter_usuario_atual()
    comentarios = controller.carregar_comentarios(professor_id, disciplinas, filtro_bruto, usuario)
    login_url = None
    if usuario is None:
        destino = sanitizar_destino(_url_perfil(professor_id, next_url, disciplina,
                                                comentarios['filtro_comentarios']))
        login_url = url_for('auth.login', next=destino) if destino else url_for('auth.login')
    contexto = dict(erros_comentario={}, texto_form='', disciplina_form=None)
    contexto.update(extra)
    pagina = render_template(
        'perfil_professor.html', professor=professor, disciplinas=disciplinas,
        disciplina=disciplina,
        indicadores=controller.indicadores(professor_id, disciplina['id']) if disciplina else None,
        criterios=controller.criterios(), next_url=next_url,
        geral=controller.indicadores(professor_id, None),
        usuario=usuario, login_url=login_url, **comentarios, **contexto)
    return pagina, status


@professor_bp.get('/professores/<int:professor_id>')
def perfil(professor_id):
    professor, disciplinas, disciplina = controller.carregar_perfil(professor_id)
    return _renderizar_perfil(professor, disciplinas, disciplina,
                              _next_seguro(request.args.get('next')),
                              request.args.get('comentarios_disciplina'))


@professor_bp.post('/professores/<int:professor_id>/comentarios')
@login_required
@limitar_comentario
def comentar(professor_id):
    # Sem carregar_perfil: ele lê request.form['disciplina_id'] (aqui é a disciplina do
    # comentário, não a das médias) e aborta com 400 se faltar.
    usuario = obter_usuario_atual()
    professor = controller.carregar_professor(professor_id)
    disciplinas = controller.listar_disciplinas(professor_id)
    texto = request.form.get('texto', '')
    disciplina_id, erros = controller.validar_novo_comentario(
        disciplinas, request.form.get('disciplina_id'), texto)
    if not erros:
        try:
            # O autor vem só da sessão; um usuario_id enviado no formulário é ignorado.
            controller.publicar_comentario(usuario, professor_id, disciplina_id, texto)
        except ValueError as erro:
            erros['texto'] = str(erro)

    next_url = _next_seguro(request.form.get('next'))
    disciplina_medias = controller.disciplina_das_medias(
        disciplinas, request.form.get('disciplina_medias'))
    filtro_bruto = request.form.get('comentarios_disciplina')
    if not erros:
        filtro = controller.filtro_de_comentarios(filtro_bruto, disciplinas)
        return redirect(_url_perfil(professor_id, next_url, disciplina_medias, filtro), code=303)
    return _renderizar_perfil(professor, disciplinas, disciplina_medias, next_url, filtro_bruto,
                              status=400, erros_comentario=erros, texto_form=texto,
                              disciplina_form=disciplina_id)


def _contexto_do_comentario(comentario_id, usuario, origem):
    """(comentario, professor, disciplinas, next_url, filtro, url_voltar) de um comentário do
    usuário logado. 404 se não for dele. `origem` é request.args (GET) ou request.form (POST)."""
    comentario = controller.carregar_comentario_do_usuario(comentario_id, usuario)
    professor = controller.carregar_professor(comentario['professor_id'])
    disciplinas = controller.listar_disciplinas(professor['id'])
    next_url = _next_seguro(origem.get('next'))
    filtro = controller.filtro_de_comentarios(origem.get('comentarios_disciplina'), disciplinas)
    return (comentario, professor, disciplinas, next_url, filtro,
            _url_perfil(professor['id'], next_url, None, filtro))


@professor_bp.route('/comentarios/<int:comentario_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_comentario(comentario_id):
    usuario = obter_usuario_atual()
    origem = request.form if request.method == 'POST' else request.args
    comentario, professor, disciplinas, next_url, filtro, url_voltar = _contexto_do_comentario(
        comentario_id, usuario, origem)
    texto, disciplina_form, erros, status = comentario['texto'], comentario['disciplina_id'], {}, 200
    if request.method == 'POST':
        # Só texto e disciplina mudam; professor_id e usuario_id do formulário são ignorados.
        texto = request.form.get('texto', '')
        disciplina_form, erros = controller.validar_novo_comentario(
            disciplinas, request.form.get('disciplina_id'), texto)
        if not erros:
            try:
                controller.editar_comentario(comentario_id, usuario, disciplina_form, texto)
            except ValueError as erro:
                erros['texto'] = str(erro)
            else:
                return redirect(url_voltar, code=303)
        status = 400
    return render_template('editar_comentario.html', professor=professor, disciplinas=disciplinas,
                           comentario=comentario, texto_form=texto, disciplina_form=disciplina_form,
                           erros_comentario=erros, next_url=next_url, filtro_comentarios=filtro,
                           url_voltar=url_voltar, usuario=usuario), status


@professor_bp.route('/comentarios/<int:comentario_id>/excluir', methods=['GET', 'POST'])
@login_required
def excluir_comentario(comentario_id):
    usuario = obter_usuario_atual()
    origem = request.form if request.method == 'POST' else request.args
    comentario, professor, _, next_url, filtro, url_voltar = _contexto_do_comentario(
        comentario_id, usuario, origem)
    if request.method == 'POST':
        controller.excluir_comentario(comentario_id, usuario)
        if request.accept_mimetypes.best == 'application/json':
            return jsonify({'mensagem': 'Comentário excluído com sucesso.'}), 200
        return redirect(url_voltar, code=303)
    return render_template('excluir_comentario.html', professor=professor, comentario=comentario,
                           next_url=next_url, filtro_comentarios=filtro, url_voltar=url_voltar,
                           usuario=usuario)


@professor_bp.route('/avaliar/<int:professor_id>', methods=['GET', 'POST'])
@login_required
@limitar_avaliacao
def avaliar(professor_id):
    professor, _, disciplina = controller.carregar_perfil(professor_id)
    if disciplina is None:
        abort(404, description='Professor sem disciplinas disponíveis.')

    next_url = request.args.get('next')
    if not is_safe_url(next_url):
        next_url = url_for('professores.perfil', professor_id=professor_id)

    erros, status = {}, 200
    if request.method == 'POST':
        notas, erros = controller.validar_notas(request.form)
        if erros:
            status = 400
        elif not controller.registrar_avaliacao(obter_usuario_atual(), professor_id,
                                                disciplina['id'], notas):
            erros = {'avaliacao': 'Você já avaliou este professor nesta disciplina.'}
            status = 409
        else:
            return redirect(url_for('professores.perfil', professor_id=professor_id,
                                    disciplina_id=disciplina['id'], next=next_url), code=303)
        if request.accept_mimetypes.best == 'application/json':
            return jsonify({'erros': erros}), status
            
    return render_template('avaliacao.html', professor=professor, disciplina=disciplina, 
                           criterios=controller.criterios(), erros=erros, dados=request.form, 
                           next_url=next_url, usuario=obter_usuario_atual()), status


@professor_bp.route('/avaliacoes/<int:avaliacao_id>/editar', methods=['GET', 'POST'])
@login_required
@limitar_avaliacao
def editar_avaliacao(avaliacao_id):
    usuario = obter_usuario_atual()
    avaliacao = controller.carregar_avaliacao_do_usuario(avaliacao_id, usuario)
    professor = {'id': avaliacao['professor_id'], 'nome': avaliacao['professor_nome']}
    disciplina = {
        'id': avaliacao['disciplina_id'],
        'nome': avaliacao['disciplina_nome'],
        'codigo': avaliacao['codigo_disciplina'],
    }
    erros, status = {}, 200
    dados = {c: str(avaliacao[c]) for c in controller.criterios()}
    if request.method == 'POST':
        dados = request.form
        notas, erros = controller.validar_notas(request.form)
        if erros:
            status = 400
        else:
            controller.editar_avaliacao(avaliacao_id, usuario, notas)
            return redirect(url_for('auth.perfil'), code=303)
        if request.accept_mimetypes.best == 'application/json':
            return jsonify({'erros': erros}), status
    return render_template(
        'avaliacao.html',
        professor=professor,
        disciplina=disciplina,
        criterios=controller.criterios(),
        erros=erros,
        dados=dados,
        modo_edicao=True,
        acao_form=url_for('professores.editar_avaliacao', avaliacao_id=avaliacao_id),
        usuario=usuario,
    ), status


@professor_bp.post('/avaliacoes/<int:avaliacao_id>/excluir')
@login_required
@limitar_avaliacao
def excluir_avaliacao(avaliacao_id):
    controller.excluir_avaliacao(avaliacao_id, obter_usuario_atual())
    if request.accept_mimetypes.best == 'application/json':
        return jsonify({'mensagem': 'Avaliação excluída com sucesso.'}), 200
    return redirect(url_for('auth.perfil'), code=303)