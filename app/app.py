# app.py
"""
Ponto de entrada mínimo para testar o controlador de sessão localmente.

Rodar:
    pip install flask
    python app.py
"""

from flask import Flask

from database import init_db
from routes.auth_routes import auth_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(auth_bp)

    with app.app_context():
        init_db()

    return app


if __name__ == "__main__":
    app = create_app()
    # debug=True apenas em desenvolvimento
    app.run(debug=True)