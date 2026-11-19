import httpx
from flask import Blueprint, current_app, render_template
from postgrest.exceptions import APIError

from app.controllers import professor_controller
from app.controllers.session_controller import obter_usuario_atual

main_bp = Blueprint('main', __name__)


@main_bp.get('/')
def index():
    usuario = obter_usuario_atual()
    try:
        destaques = [
            {**professor, 'media': professor['media_geral'],
             'quantidade': professor['total_avaliacoes']}
            for professor, _ in professor_controller.catalogo()
            if professor['media_geral'] is not None
        ][:3]
    except (APIError, httpx.HTTPError, RuntimeError) as erro:
        current_app.logger.warning('Destaques indisponíveis na home (%s)', type(erro).__name__)
        destaques = None
    return render_template('index.html', usuario=usuario, destaques=destaques)


@main_bp.get('/sobre')
def sobre():
    return render_template('sobre.html', usuario=obter_usuario_atual())


@main_bp.get("/privacidade")
def privacidade():
    return render_template("privacidade.html", usuario=obter_usuario_atual())
