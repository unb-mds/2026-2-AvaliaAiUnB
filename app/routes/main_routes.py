from flask import Blueprint, render_template

from app.controllers.session_controller import obter_usuario_atual

main_bp = Blueprint('main', __name__)


@main_bp.get('/')
def index():
    return render_template('index.html', usuario=obter_usuario_atual())


@main_bp.get('/privacidade')
def privacidade():
    return render_template('privacidade.html', usuario=obter_usuario_atual())