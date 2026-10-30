"""Telas de professores: listagem, perfil com médias por disciplina e avaliação."""
from flask import Blueprint, abort, jsonify, redirect, render_template, request, url_for

from app.controllers import professor_controller as controller
from app.controllers.session_controller import login_required, obter_usuario_atual

professor_bp = Blueprint('professores', __name__)


@professor_bp.get('/ranking')
def ranking():
    professores, minimo_avaliacoes = controller.carregar_ranking()
    return render_template('ranking.html', ranking=professores,
                           minimo_avaliacoes=minimo_avaliacoes)


@professor_bp.get('/professores')
def listar():
    filtros = {campo: request.args.get(campo, '').strip() for campo in ('nome', 'disciplina')}
    return render_template('lista_professores.html', catalogo=controller.catalogo(**filtros),
                           filtros=filtros)


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
    return render_template('avaliacao.html', professor=professor, disciplina=disciplina,
                           criterios=controller.criterios(), erros=erros, dados=request.form), status
