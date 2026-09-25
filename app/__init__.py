# app/__init__.py
from flask import Flask

from app.database import inicializar_banco
from app.routes.auth_routes import auth_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(auth_bp)

    with app.app_context():
        inicializar_banco()

    return app