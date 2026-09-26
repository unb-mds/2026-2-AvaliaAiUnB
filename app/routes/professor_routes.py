"""Integra as telas do PR #50 ao catálogo e às médias por disciplina."""
from flask import Blueprint, abort, jsonify, redirect, render_template, request, url_for

from app.controllers.session_controller import login_required, obter_usuario_atual
from app.repositorio import AvaliacaoRepository, ProfessorRepository
from app.validacoes import CRITERIOS, validar_avaliacao

professor_bp = Blueprint('professores', __name__)
professores = ProfessorRepository()
avaliacoes = AvaliacaoRepository()


def carregar_perfil(professor_id):
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


@professor_bp.get('/professores')
def listar():
    catalogo = [(professor, professores.listar_disciplinas(professor['id']))
                for professor in professores.listar()]
    return render_template('lista_professores.html', catalogo=catalogo)


@professor_bp.get('/professores/<int:professor_id>')
def perfil(professor_id):
    professor, disciplinas, disciplina = carregar_perfil(professor_id)
    indicadores = avaliacoes.calcular_medias(professor_id, disciplina['id']) if disciplina else None
    return render_template('perfil_professor.html', professor=professor, disciplinas=disciplinas,
                           disciplina=disciplina, indicadores=indicadores, criterios=CRITERIOS)


@professor_bp.route('/avaliar/<int:professor_id>', methods=['GET', 'POST'])
@login_required
def avaliar(professor_id):
    professor, _, disciplina = carregar_perfil(professor_id)
    if disciplina is None:
        abort(404, description='Professor sem disciplinas disponíveis.')
    erros, status = {}, 200
    if request.method == 'POST':
        notas, erros = validar_avaliacao(request.form)
        if erros:
            status = 400
        elif not avaliacoes.salvar(obter_usuario_atual()['id'], professor_id, disciplina['id'], notas):
            erros = {'avaliacao': 'Você já avaliou este professor nesta disciplina.'}
            status = 409
        else:
            return redirect(url_for('professores.perfil', professor_id=professor_id,
                                    disciplina_id=disciplina['id']), code=303)
        if request.accept_mimetypes.best == 'application/json':
            return jsonify({'erros': erros}), status
    return render_template('avaliacao.html', professor=professor, disciplina=disciplina,
                           criterios=CRITERIOS, erros=erros, dados=request.form), status
