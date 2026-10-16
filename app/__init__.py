# app/__init__.py
from flask import Flask

from app.controllers.session_controller import registrar_renovacao
from app.repositorio import configurar_repositorios
from app.routes.auth_routes import auth_bp
from app.routes.main_routes import main_bp
from app.routes.professor_routes import professor_bp


def create_app(config=None) -> Flask:
    app = Flask(__name__)

    if config:
        app.config.update(config)
    configurar_repositorios(app)
    registrar_renovacao(app)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(professor_bp)

    return app
