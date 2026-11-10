# run.py
"""
Ponto de entrada do projeto.

IMPORTANTE: esse arquivo se chama run.py (e não app.py) de propósito.
Como já existe uma pasta app/ (o pacote da aplicação), ter também um
arquivo app.py na raiz causaria conflito de nomes na hora do import.

Desenvolvimento:
    pip install -r requirements.txt
    FLASK_DEBUG=1 python run.py

Produção (nunca use app.run / debug em produção):
    gunicorn run:app
"""
import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Debug só liga com FLASK_DEBUG explícito e, nesse caso, só escuta em localhost
    # (o debugger do Werkzeug permite executar código no servidor).
    debug = app.debug
    app.run(host="127.0.0.1" if debug else os.environ.get("HOST", "127.0.0.1"), debug=debug)