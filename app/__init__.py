# app/__init__.py
from flask import Flask

from app.database import inicializar_banco
from app.routes.auth_routes import auth_bp
from app.routes.professor_routes import professor_bp


def create_app(config=None) -> Flask:
    app = Flask(__name__)
    if config:
        app.config.update(config)
    app.register_blueprint(auth_bp)
    app.register_blueprint(professor_bp)

    with app.app_context():
        inicializar_banco()

    return app
