# run.py
"""
Ponto de entrada do projeto.

IMPORTANTE: esse arquivo se chama run.py (e não app.py) de propósito.
Como já existe uma pasta app/ (o pacote da aplicação), ter também um
arquivo app.py na raiz causaria conflito de nomes na hora do import.

Rodar:
    pip install flask
    python run.py
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    # debug=True apenas em desenvolvimento
    app.run(debug=True)