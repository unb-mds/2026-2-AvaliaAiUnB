# app/__init__.py
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_wtf.csrf import CSRFProtect

from app.controllers.session_controller import registrar_renovacao
from app.repositorio import configurar_repositorios
from app.routes.auth_routes import auth_bp
from app.routes.main_routes import main_bp
from app.routes.professor_routes import professor_bp


def create_app(config=None) -> Flask:
    load_dotenv(Path(__file__).resolve().parent.parent / '.env')
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY'),
        DEBUG=os.getenv('FLASK_DEBUG', '').strip().lower() in {'1', 'true', 'yes', 'on'},
    )

    if config:
        app.config.update(config)
    if not app.config['SECRET_KEY'] or not app.config['SECRET_KEY'].strip():
        raise RuntimeError('Defina a variável de ambiente SECRET_KEY antes de iniciar a aplicação.')

    CSRFProtect(app)
    configurar_repositorios(app)
    registrar_renovacao(app)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(professor_bp)

    return app
