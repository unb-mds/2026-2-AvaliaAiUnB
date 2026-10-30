"""Telas de professores: listagem, perfil com médias por disciplina e avaliação."""
from flask import Blueprint, abort, jsonify, redirect, render_template, request, url_for

from app.controllers import professor_controller as controller
from app.controllers.session_controller import login_required, obter_usuario_atual

professor_bp = Blueprint('professores', __name__)

CAMPOS_FILTRO = ('nome', 'disciplina', 'departamento')


@professor_bp.get('/comparar')
def comparar():
    contexto = controller.carregar_comparacao(request.args)
    return render_template('comparacao.html', **contexto), 400 if contexto['erros'] else 200


@professor_bp.get('/professores')
def listar():
    filtros = {campo: request.args.get(campo, '').strip() for campo in CAMPOS_FILTRO}
    return render_template('lista_professores.html', catalogo=controller.catalogo(**filtros),
                           filtros=filtros, departamentos=controller.departamentos())


@professor_bp.get('/professores/<int:professor_id>')
def perfil(professor_id):
    professor, disciplinas, disciplina = controller.carregar_perfil(professor_id)
    indicadores = controller.indicadores(professor_id, disciplina['id']) if disciplina else None
    return render_template('perfil_professor.html', professor=professor, disciplinas=disciplinas,
                           disciplina=disciplina, indicadores=indicadores,
                           criterios=controller.criterios())


@professor_bp.route('/avaliar/<int:professor_id>', methods=['GET', 'POST'])
@login_required
def avaliar(professor_id):
    professor, _, disciplina = controller.carregar_perfil(professor_id)
    if disciplina is None:
        abort(404, description='Professor sem disciplinas disponíveis.')
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
                                    disciplina_id=disciplina['id']), code=303)
        if request.accept_mimetypes.best == 'application/json':
            return jsonify({'erros': erros}), status
    return render_template('avaliacao.html', professor=professor, disciplina=disciplina, criterios=controller.criterios(), erros=erros, dados=request.form), status                       


@professor_bp.route('/avaliacoes/<int:avaliacao_id>/editar', methods=['GET', 'POST'])
@login_required
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
    ), status


@professor_bp.post('/avaliacoes/<int:avaliacao_id>/excluir')
@login_required
def excluir_avaliacao(avaliacao_id):
    controller.excluir_avaliacao(avaliacao_id, obter_usuario_atual())
    if request.accept_mimetypes.best == 'application/json':
        return jsonify({'mensagem': 'Avaliação excluída com sucesso.'}), 200
    return redirect(url_for('auth.perfil'), code=303)

