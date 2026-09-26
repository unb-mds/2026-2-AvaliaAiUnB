"""Demonstração local com dados fictícios em banco temporário; não altera banco.db."""
import tempfile
from contextlib import closing
from pathlib import Path

from app import create_app
from app.database import get_db_connection
from app.repositorio import AvaliacaoRepository
from app.validacoes import CRITERIOS


def criar_demo(caminho):
    app = create_app({'DATABASE': str(caminho)})
    with app.app_context():
        with closing(get_db_connection()) as conexao, conexao:
            conexao.execute("INSERT INTO professores VALUES (1, 'Professor de demonstração', 'Departamento de demonstração')")
            conexao.executemany('INSERT INTO disciplinas VALUES (?, ?, ?)',
                               [(1, 'Disciplina com avaliações', 'DEMO01'),
                                (2, 'Disciplina sem avaliações', 'DEMO02')])
            conexao.executemany('INSERT INTO professor_disciplinas VALUES (1, ?)', [(1,), (2,)])
            for usuario in (1, 2, 3):
                conexao.execute('INSERT INTO usuarios VALUES (?, ?, ?, ?)',
                                (usuario, f'Exemplo {usuario}', f'exemplo{usuario}@example.com', '!sem-login'))
        repo = AvaliacaoRepository()
        for usuario, nota in enumerate((5, 4, 4), 1):
            notas = {criterio: nota for criterio in CRITERIOS}
            notas['dificuldade'] = usuario
            repo.salvar(usuario, 1, 1, notas)
    return app


if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='avaliaai-demo-') as pasta:
        app = criar_demo(Path(pasta) / 'demo.db')
        print('Dados fictícios e temporários. Perfil: http://localhost:5050/professores/1')
        print('Cadastro: http://localhost:5050/cadastro')
        app.run(host='127.0.0.1', port=5050, debug=False)
