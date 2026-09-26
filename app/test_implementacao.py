"""Testes de integração das issues #26, #36 e #37, sem usar banco.db real."""
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from contextlib import closing
from pathlib import Path

from werkzeug.security import check_password_hash

from app import create_app
from app.database import get_db_connection, inicializar_banco
from app.repositorio import AvaliacaoRepository
from app.validacoes import CRITERIOS


class BancoIsolado(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.caminho = str(Path(self.temp.name) / 'teste.db')
        self.app = create_app({'TESTING': True, 'DATABASE': self.caminho})
        banco = patch('app.database.CAMINHO_BANCO', self.caminho)
        banco.start()
        self.addCleanup(banco.stop)
        self.client = self.app.test_client()

    def sql(self, comando, parametros=()):
        conexao = get_db_connection()
        try:
            cursor = conexao.execute(comando, parametros)
            linhas = cursor.fetchall()
            conexao.commit()
            return linhas
        finally:
            conexao.close()

    def cadastro(self, **campos):
        dados = dict(nome='Ana Souza', email='ana+teste@example.com',
                     senha='senha123', confirmar_senha='senha123')
        dados.update(campos)
        return self.client.post('/cadastro', data=dados)

    def catalogo(self):
        for pid in (1, 2):
            self.sql('INSERT INTO professores VALUES (?, ?, ?)', (pid, f'Professor {pid}', 'FCTE'))
        for did in (10, 20):
            self.sql('INSERT INTO disciplinas VALUES (?, ?, ?)', (did, f'Disciplina {did}', f'MDS{did}'))
        for pid, did in ((1, 10), (1, 20), (2, 10)):
            self.sql('INSERT INTO professor_disciplinas VALUES (?, ?)', (pid, did))
        for uid in range(1, 5):
            self.sql('INSERT INTO usuarios VALUES (?, ?, ?, ?)',
                     (uid, f'Aluno Privado {uid}', f'privado{uid}@example.com', 'hash'))


class TestCadastro(BancoIsolado):
    def test_cadastro_valido_hash_e_espacos(self):
        resposta = self.cadastro(nome='  Ana Souza  ', email='  ana+teste@example.com  ')
        self.assertEqual(resposta.status_code, 201)
        usuario = self.sql('SELECT * FROM usuarios')[0]
        self.assertEqual(usuario['nome'], 'Ana Souza')
        self.assertEqual(usuario['email'], 'ana+teste@example.com')
        self.assertTrue(check_password_hash(usuario['senha'], 'senha123'))
        self.assertNotIn('senha', resposta.get_data(as_text=True))

    def test_nome_vazio(self):
        self.assertEqual(self.cadastro(nome='').status_code, 400)
        self.assertEqual(len(self.sql('SELECT * FROM usuarios')), 0)

    def test_nome_espacos(self):
        self.assertEqual(self.cadastro(nome='   ').status_code, 400)

    def test_email_vazio(self):
        self.assertEqual(self.cadastro(email='').status_code, 400)

    def test_emails_invalidos(self):
        for email in ('ana', 'a@@b.com', 'a b@example.com', 'a@b', 'a@.com',
                      '.a@b.com', 'a..b@c.com', 'a@-b.com', 'a@b..com'):
            with self.subTest(email=email):
                self.assertEqual(self.cadastro(email=email).status_code, 400)

    def test_senha_vazia(self):
        self.assertEqual(self.cadastro(senha='', confirmar_senha='').status_code, 400)

    def test_senha_espacos(self):
        self.assertEqual(self.cadastro(senha='        ', confirmar_senha='        ').status_code, 400)

    def test_senha_curta(self):
        self.assertEqual(self.cadastro(senha='1234567', confirmar_senha='1234567').status_code, 400)

    def test_confirmacao_diferente(self):
        self.assertEqual(self.cadastro(confirmar_senha='outrasenha').status_code, 400)

    def test_campos_ausentes(self):
        resposta = self.client.post('/cadastro', data={})
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(set(resposta.json['erros']), {'nome', 'email', 'senha', 'confirmar_senha'})

    def test_email_duplicado(self):
        self.assertEqual(self.cadastro().status_code, 201)
        self.assertEqual(self.cadastro().status_code, 409)
        self.assertEqual(len(self.sql('SELECT * FROM usuarios')), 1)

    def test_email_duplicado_com_caixa_diferente(self):
        self.cadastro(email='Ana@example.com')
        self.assertEqual(self.cadastro(email='ana@EXAMPLE.com').status_code, 409)

    def test_html_preserva_nome_email_sem_senha(self):
        resposta = self.client.post('/cadastro', headers={'Accept': 'text/html'},
            data={'nome': '<script>teste</script>', 'email': 'ana@example.com',
                  'senha': 'secreto', 'confirmar_senha': 'secreto'})
        html = resposta.get_data(as_text=True)
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('ana@example.com', html)
        self.assertNotIn('secreto', html)

    def test_sucesso_e_duplicidade_html(self):
        dados = dict(nome='Ana', email='ana@example.com', senha='senha123', confirmar_senha='senha123')
        for status in (200, 409):
            resposta = self.client.post('/cadastro', data=dados, headers={'Accept': 'text/html'})
            self.assertEqual(resposta.status_code, status)
            self.assertIn('text/html', resposta.content_type)

    def test_login_perfil_logout_existentes(self):
        self.cadastro()
        resposta = self.client.post('/login', data={'email': 'ANA+TESTE@example.com', 'senha': 'senha123'})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(self.client.get('/perfil').status_code, 200)
        self.assertEqual(self.client.post('/logout').status_code, 200)
        self.assertEqual(self.client.get('/perfil', headers={'Accept': 'application/json'}).status_code, 401)

    def test_formulario_html_com_accept_generico(self):
        resposta = self.cadastro(formato='html')
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('Usuário criado com sucesso', resposta.get_data(as_text=True))
        self.assertIn('text/html', resposta.content_type)


class BaseAvaliacoes(BancoIsolado):
    def setUp(self):
        super().setUp()
        self.catalogo()
        self.repo = AvaliacaoRepository()

    def avaliar(self, usuario=1, professor=1, disciplina=10, nota=4, **notas):
        dados = {c: nota for c in CRITERIOS}
        dados.update(notas)
        return self.repo.salvar(usuario, professor, disciplina, dados)


class TestMedias(BaseAvaliacoes):
    def test_nenhuma_avaliacao(self):
        indicadores = self.repo.calcular_medias(1, 10)
        self.assertEqual(indicadores['quantidade'], 0)
        self.assertTrue(all(m is None for m in indicadores['medias'].values()))

    def test_uma_avaliacao(self):
        self.avaliar(nota=5, dificuldade=1)
        resultado = self.repo.calcular_medias(1, 10)
        self.assertEqual(resultado['quantidade'], 1)
        self.assertEqual(resultado['medias']['didatica'], 5)
        self.assertEqual(resultado['medias']['dificuldade'], 1)
        self.assertEqual(resultado['medias']['avaliacao_geral'], 5)

    def test_varias_avaliacoes_e_criterios_independentes(self):
        for usuario, nota in enumerate((5, 4, 3), 1):
            self.avaliar(usuario=usuario, nota=nota, organizacao=2, dificuldade=1)
        resultado = self.repo.calcular_medias(1, 10)
        self.assertEqual(resultado['quantidade'], 3)
        self.assertEqual(resultado['medias']['didatica'], 4)
        self.assertEqual(resultado['medias']['organizacao'], 2)
        self.assertEqual(resultado['medias']['dificuldade'], 1)
        self.assertEqual(resultado['medias']['avaliacao_geral'], 4)

    def test_fracao_sem_arredondamento_na_consulta(self):
        for usuario, nota in enumerate((5, 4, 4), 1):
            self.avaliar(usuario=usuario, nota=nota)
        self.assertAlmostEqual(self.repo.calcular_medias(1, 10)['medias']['didatica'], 13 / 3)

    def test_separa_professores_e_disciplinas(self):
        self.avaliar(nota=2)
        self.avaliar(professor=2, nota=5)
        self.avaliar(disciplina=20, nota=1)
        resultado = self.repo.calcular_medias(1, 10)
        self.assertEqual(resultado['quantidade'], 1)
        self.assertEqual(resultado['medias']['didatica'], 2)

    def test_recusa_duplicada(self):
        self.assertTrue(self.avaliar())
        self.assertFalse(self.avaliar(nota=1))
        self.assertEqual(self.repo.calcular_medias(1, 10)['quantidade'], 1)

    def test_valores_invalidos(self):
        for valor in (0, 6, 3.5, None, '5', True):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                self.avaliar(didatica=valor)

    def test_vinculo_inexistente(self):
        with self.assertRaises(ValueError):
            self.avaliar(professor=2, disciplina=20)

    def test_atualiza_apos_edicao_e_exclusao(self):
        self.avaliar(nota=5)
        self.avaliar(usuario=2, nota=3)
        self.sql('UPDATE avaliacoes SET nota = 1 WHERE usuario_id = 1')
        self.assertEqual(self.repo.calcular_medias(1, 10)['medias']['avaliacao_geral'], 2)
        self.sql('DELETE FROM avaliacoes WHERE usuario_id = 2')
        self.assertEqual(self.repo.calcular_medias(1, 10)['medias']['avaliacao_geral'], 1)

    def test_dados_legados_incompletos_nao_fabricam_medias(self):
        self.sql('INSERT INTO avaliacoes(nota, professor_id, usuario_id) VALUES (5, 1, 1)')
        self.sql('INSERT INTO avaliacoes(nota, professor_id, usuario_id, disciplina_id) VALUES (5, 1, 2, 10)')
        self.assertEqual(self.repo.calcular_medias(1, 10)['quantidade'], 0)


class TestPerfil(BaseAvaliacoes):
    def test_perfil_publico_sem_avaliacoes(self):
        resposta = self.client.get('/professores/1?disciplina_id=10')
        self.assertEqual(resposta.status_code, 200)
        html = resposta.get_data(as_text=True)
        self.assertIn('Ainda não há avaliações', html)
        self.assertNotIn('0,0 / 5', html)

    def test_perfil_medias_quantidade_anonimato(self):
        self.avaliar(nota=5)
        self.avaliar(usuario=2, nota=4)
        html = self.client.get('/professores/1?disciplina_id=10').get_data(as_text=True)
        self.assertIn('4,5 / 5', html)
        self.assertIn('2 avaliações', html)
        for titulo in CRITERIOS.values():
            self.assertIn(titulo, html)
        self.assertNotIn('privado1@example.com', html)
        self.assertNotIn('Aluno Privado', html)
        self.assertNotIn('comentario', html)

    def test_troca_disciplina(self):
        self.avaliar(nota=5)
        html = self.client.get('/professores/1?disciplina_id=20').get_data(as_text=True)
        self.assertIn('Ainda não há avaliações', html)
        self.assertIn('Disciplina 20', html)

    def test_professor_inexistente(self):
        self.assertEqual(self.client.get('/professores/999').status_code, 404)

    def test_disciplina_invalida(self):
        self.assertEqual(self.client.get('/professores/1?disciplina_id=abc').status_code, 400)
        self.assertEqual(self.client.get('/professores/1?disciplina_id=999').status_code, 404)

    def test_professor_sem_disciplinas(self):
        self.sql('INSERT INTO professores VALUES (3, "Sem disciplinas", "FCTE")')
        resposta = self.client.get('/professores/3')
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('Ainda não há disciplinas', resposta.get_data(as_text=True))

    def test_avaliacao_exige_login(self):
        self.assertEqual(self.client.get('/avaliar/1?disciplina_id=10').status_code, 302)
        self.assertEqual(self.client.post('/avaliar/1', headers={'Accept': 'application/json'}).status_code, 401)

    def test_fluxo_submissao_ate_indicadores(self):
        self.cadastro()
        self.client.post('/login', data={'email': 'ana+teste@example.com', 'senha': 'senha123'})
        resposta = self.client.get('/avaliar/1?disciplina_id=10')
        self.assertEqual(resposta.status_code, 200)
        dados = {c: '5' for c in CRITERIOS}
        dados['disciplina_id'] = '10'
        self.assertEqual(self.client.post('/avaliar/1', data={**dados, 'didatica': '6'}).status_code, 400)
        self.assertEqual(self.repo.calcular_medias(1, 10)['quantidade'], 0)
        resposta = self.client.post('/avaliar/1', data=dados, follow_redirects=True)
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('5,0 / 5', resposta.get_data(as_text=True))
        self.assertEqual(self.client.post('/avaliar/1', data=dados).status_code, 409)
        self.assertEqual(self.client.post('/avaliar/1', data={c: '5' for c in CRITERIOS}).status_code, 400)


class TestMigracao(unittest.TestCase):
    def test_migracao_legada_preserva_dados_e_e_idempotente(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = str(Path(pasta) / 'legado.db')
            with closing(sqlite3.connect(caminho)) as conexao:
                conexao.executescript("""
                    CREATE TABLE usuarios(id INTEGER PRIMARY KEY, nome TEXT, email TEXT UNIQUE, senha TEXT);
                    CREATE TABLE avaliacoes(id INTEGER PRIMARY KEY, nota INTEGER NOT NULL,
                        comentario TEXT, usuario_id INTEGER, professor_id INTEGER);
                    INSERT INTO usuarios VALUES (1, 'Legado', 'legado@example.com', 'hash');
                    INSERT INTO avaliacoes VALUES (1, 4, 'Legado preservado', 1, 123);
                """)
            app = create_app({'TESTING': True, 'DATABASE': caminho})
            with app.app_context():
                inicializar_banco()
                conexao = get_db_connection()
                try:
                    linha = conexao.execute('SELECT * FROM avaliacoes').fetchone()
                    self.assertEqual(linha['nota'], 4)
                    self.assertEqual(linha['comentario'], 'Legado preservado')
                    self.assertIsNone(linha['disciplina_id'])
                    self.assertIsNone(linha['didatica'])
                finally:
                    conexao.close()


if __name__ == '__main__':
    unittest.main()
