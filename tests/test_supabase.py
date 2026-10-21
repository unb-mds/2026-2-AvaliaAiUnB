"""Repositórios e fluxo web sobre o Supabase, com cliente falso em memória."""
import re
import time
import unittest
from unittest.mock import patch

from app import create_app
from app.repositorio import AvaliacaoRepository, ProfessorRepository, UsuarioRepository
from app.validacoes import CRITERIOS
from tests.fake_supabase import ClienteFalso

NOTAS = {c: 4 for c in CRITERIOS}


class TestProfessores(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.professores = ProfessorRepository(self.cliente)
        self.avaliacoes = AvaliacaoRepository(self.cliente)

    def test_catalogo_filtra_ignorando_acento_e_caixa(self):
        (professor, disciplinas), = self.professores.catalogo(nome='jose avila')
        self.assertEqual(professor['id'], 1)
        self.assertEqual([d['id'] for d in disciplinas], [10])
        self.assertEqual([p['id'] for p, _ in self.professores.catalogo(disciplina='fisica')], [2])
        self.assertEqual([p['id'] for p, _ in self.professores.catalogo(disciplina='fga0001')], [1])
        self.assertEqual(self.professores.catalogo(nome='inexistente'), [])

    def test_catalogo_ordenado_por_quantidade_de_avaliacoes(self):
        self.assertEqual([p['id'] for p, _ in self.professores.catalogo()], [1, 2, 3])  # empate: nome
        self.avaliacoes.salvar('u1', 2, 20, NOTAS)
        self.avaliacoes.salvar('u2', 2, 20, NOTAS)
        self.avaliacoes.salvar('u1', 1, 10, NOTAS)
        self.professores.invalidar_cache()
        catalogo = self.professores.catalogo()
        self.assertEqual([(p['id'], p['total_avaliacoes']) for p, _ in catalogo],
                         [(2, 2), (1, 1), (3, 0)])

    def test_buscar_por_id(self):
        self.assertEqual(self.professores.buscar_por_id(2)['nome'], 'MARIA LIMA')
        self.assertIsNone(self.professores.buscar_por_id(99))

    def test_salvar_usa_turma_mais_recente_e_bloqueia_duplicata(self):
        self.assertTrue(self.avaliacoes.salvar('u1', 1, 10, NOTAS))
        gravada = self.cliente.tabelas['avaliacoes'][0]
        self.assertEqual((gravada['ano'], gravada['periodo']), (2026, 2))
        self.assertNotIn('comentario', gravada)
        self.assertFalse(self.avaliacoes.salvar('u1', 1, 10, NOTAS))
        self.assertTrue(self.avaliacoes.salvar('u2', 1, 10, {**NOTAS, 'dificuldade': 2}))

    def test_salvar_rejeita_invalidos(self):
        with self.assertRaises(ValueError):
            self.avaliacoes.salvar('u1', 1, 10, {**NOTAS, 'didatica': 6})
        with self.assertRaises(ValueError):
            self.avaliacoes.salvar('u1', 1, 20, NOTAS)   # disciplina de outro professor
        self.assertEqual(self.cliente.tabelas['avaliacoes'], [])

    def test_medias(self):
        self.assertEqual(self.avaliacoes.calcular_medias(1, 10)['quantidade'], 0)
        self.avaliacoes.salvar('u1', 1, 10, NOTAS)
        self.avaliacoes.salvar('u2', 1, 10, {**NOTAS, 'didatica': 2})
        resultado = self.avaliacoes.calcular_medias(1, 10)
        self.assertEqual(resultado['quantidade'], 2)
        self.assertEqual(resultado['medias']['didatica'], 3)
        self.assertEqual(resultado['medias']['clareza'], 4)


class TestUsuarios(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.usuarios = UsuarioRepository(self.cliente, lambda: self.cliente)

    def criar(self, username='ana', email='ana@gmail.com'):
        return self.usuarios.criar('Ana Souza', username, email, 'senha123')

    def test_criar_grava_auth_e_perfil(self):
        ok, usuario_id = self.criar()
        self.assertTrue(ok)
        self.assertEqual(self.cliente.tabelas['perfis'][0]['id'], usuario_id)
        self.assertEqual(self.cliente.auth.usuarios[usuario_id]['user_metadata']['username'], 'ana')

    def test_conflitos(self):
        self.criar()
        self.assertEqual(self.criar(email='outro@gmail.com')[:2], (False, 'username'))
        self.assertEqual(self.criar(username='outro')[:2], (False, 'email'))
        self.assertEqual(len(self.cliente.auth.usuarios), 1)

    def test_autenticar_por_username(self):
        self.criar()
        self.assertIsNotNone(self.usuarios.autenticar('ANA', 'senha123'))
        self.assertIsNone(self.usuarios.autenticar('ana', 'errada123'))
        self.assertIsNone(self.usuarios.autenticar('naoexiste', 'senha123'))

    def test_token_renovacao_e_logout(self):
        self.criar()
        sessao = self.usuarios.autenticar('ana', 'senha123')
        usuario = self.usuarios.usuario_do_token(sessao['access_token'])
        self.assertEqual((usuario['username'], usuario['nome'], usuario['email']),
                         ('ana', 'Ana Souza', 'ana@gmail.com'))
        self.usuarios.encerrar(sessao['access_token'])
        self.assertIsNone(self.usuarios.usuario_do_token(sessao['access_token']))
        self.assertIsNotNone(self.usuarios.renovar(sessao['refresh_token']))
        self.assertIsNone(self.usuarios.renovar('invalido'))


class TestFluxoWeb(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.web = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                               'SUPABASE_CLIENT': self.cliente}).test_client()

    def token_csrf(self, caminho='/login'):
        resposta = self.web.get(caminho, headers={'Accept': 'text/html'})
        self.assertEqual(resposta.status_code, 200)
        campo = re.search(r'name="csrf_token" value="([^"]+)"',
                          resposta.get_data(as_text=True))
        self.assertIsNotNone(campo, caminho)
        return campo.group(1)

    def postar(self, caminho, data=None, **opcoes):
        return self.web.post(caminho, data={**(data or {}), 'csrf_token': self.token_csrf()},
                             **opcoes)

    def cadastrar(self, **campos):
        dados = dict(nome='Ana', username='ana', email='ana@gmail.com',
                     senha='senha123', confirmar_senha='senha123')
        dados.update(campos)
        return self.postar('/cadastro', data=dados)

    def entrar(self, senha='senha123'):
        return self.postar('/login', data={'username': 'ana', 'senha': senha, 'formato': 'html'})

    def test_cadastro(self):
        self.assertEqual(self.cadastrar().status_code, 201)
        self.assertEqual(self.cadastrar().status_code, 409)
        self.assertEqual(self.cadastrar(username='outra', email='b@gmail.com').status_code, 201)
        self.assertEqual(self.cadastrar(email='ana@unb.br', username='x1y').status_code, 400)
        resposta = self.cadastrar(username='z', email='z@gmail.com')
        self.assertIn('username', resposta.get_json()['erros'])
        self.assertNotIn('senha123', resposta.get_data(as_text=True))

    def test_cadastro_html_mostra_erro_de_gmail(self):
        resposta = self.postar('/cadastro', data=dict(
            nome='Ana', username='ana', email='ana@unb.br', senha='senha123',
            confirmar_senha='senha123', formato='html'))
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('@gmail.com', resposta.get_data(as_text=True))

    def test_login_redireciona_para_home(self):
        self.cadastrar()
        resposta = self.entrar()
        self.assertEqual(resposta.status_code, 303)
        self.assertTrue(resposta.headers['Location'].endswith('/'))
        home = self.web.get('/').get_data(as_text=True)
        self.assertIn('Olá, Ana', home)
        self.assertNotIn('href="/login"', home)

    def test_login_invalido_e_json(self):
        self.cadastrar()
        resposta = self.entrar('errada123')
        self.assertEqual(resposta.status_code, 401)
        self.assertIn('Usuário ou senha inválidos', resposta.get_data(as_text=True))
        self.assertEqual(self.postar('/login', data={'username': 'ana', 'senha': 'errada123'}).status_code, 401)
        self.assertEqual(self.postar('/login', data={'username': 'ana', 'senha': 'senha123'}).status_code, 200)

    def test_perfil_exige_login_e_logout_revoga(self):
        json = {'Accept': 'application/json'}
        self.assertEqual(self.web.get('/perfil').status_code, 302)
        self.assertEqual(self.web.get('/perfil', headers=json).status_code, 401)
        self.cadastrar()
        self.entrar()
        self.assertEqual(self.web.get('/perfil', headers=json).get_json()['username'], 'ana')
        self.assertEqual(self.postar('/logout', data={'formato': 'html'}).status_code, 303)
        self.assertEqual(self.web.get('/perfil', headers=json).status_code, 401)
        self.assertEqual(self.cliente.auth.tokens, {})

    def test_sessao_expirada_e_renovada_pelo_refresh_token(self):
        json = {'Accept': 'application/json'}
        self.cadastrar()
        self.entrar()
        self.cliente.auth.expirar_acesso()
        self.assertEqual(self.web.get('/perfil', headers=json).status_code, 200)
        self.assertEqual(self.web.get('/perfil', headers=json).status_code, 200)   # cookie novo

    def test_listagem_e_perfil_de_professor(self):
        html = self.web.get('/professores?nome=maria').get_data(as_text=True)
        self.assertIn('MARIA LIMA', html)
        self.assertNotIn('JOSÉ', html)
        self.assertEqual(self.web.get('/professores/1').status_code, 200)
        self.assertEqual(self.web.get('/professores/99').status_code, 404)
        self.assertEqual(self.web.get('/professores/1?disciplina_id=20').status_code, 404)
        self.assertEqual(self.web.get('/professores/1?disciplina_id=abc').status_code, 400)

    def test_avaliar_exige_login(self):
        self.assertEqual(self.web.get('/avaliar/1').status_code, 302)
        self.assertEqual(self.postar('/avaliar/1', headers={'Accept': 'application/json'}).status_code, 401)

    def test_fluxo_avaliacao_e_ordem_da_listagem(self):
        self.cadastrar()
        self.entrar()
        formulario = self.web.get('/avaliar/2?disciplina_id=20').get_data(as_text=True)
        self.assertIn('name="clareza"', formulario)
        dados = {**{c: '5' for c in CRITERIOS}, 'disciplina_id': '20'}
        self.assertEqual(self.postar('/avaliar/2', data={**dados, 'clareza': '9'}).status_code, 400)
        html = self.postar('/avaliar/2', data=dados, follow_redirects=True).get_data(as_text=True)
        self.assertIn('1 avaliações', html)
        gravada, = self.cliente.tabelas['avaliacoes']
        self.assertEqual(gravada['usuario_id'], next(iter(self.cliente.auth.usuarios)))
        self.assertEqual(self.postar('/avaliar/2', data=dados).status_code, 409)
        self.assertEqual(len(self.cliente.tabelas['avaliacoes']), 1)
        lista = self.web.get('/professores').get_data(as_text=True)
        self.assertLess(lista.index('MARIA LIMA'), lista.index('JOSÉ ÁVILA'))   # mais avaliada primeiro
        self.assertIn('1 avaliação<', lista)

    def test_csrf_rejeita_posts_sem_token_ou_com_token_invalido(self):
        self.cadastrar()
        self.entrar()
        for caminho in ('/cadastro', '/login', '/avaliar/1', '/logout'):
            for dados in ({}, {'csrf_token': 'token-invalido'}):
                with self.subTest(caminho=caminho, dados=dados):
                    resposta = self.web.post(caminho, data=dados)
                    self.assertEqual(resposta.status_code, 400)
                    self.assertIn('CSRF', resposta.get_data(as_text=True))
        self.assertEqual(len(self.cliente.auth.usuarios), 1)
        self.assertEqual(self.cliente.tabelas['avaliacoes'], [])
        self.assertEqual(self.web.get('/perfil', headers={'Accept': 'application/json'}).status_code, 200)

    def test_csrf_rejeita_token_de_outro_cliente(self):
        token = self.token_csrf()
        outro = self.web.application.test_client()
        outro.get('/login')
        resposta = outro.post('/cadastro', data={'csrf_token': token})
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('CSRF', resposta.get_data(as_text=True))
        self.assertEqual(self.cliente.auth.usuarios, {})

    def test_csrf_rejeita_token_expirado(self):
        token = self.token_csrf()
        with patch('time.time', return_value=time.time() + 7200):
            resposta = self.web.post('/cadastro', data={'csrf_token': token})
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('CSRF', resposta.get_data(as_text=True))
        self.assertEqual(self.cliente.auth.usuarios, {})

    def test_csrf_aceita_token_no_cabecalho(self):
        token = self.token_csrf()
        resposta = self.web.post('/cadastro', data=dict(
            nome='Ana', username='ana', email='ana@gmail.com', senha='senha123',
            confirmar_senha='senha123'), headers={'X-CSRFToken': token})
        self.assertEqual(resposta.status_code, 201)

    def test_formularios_post_incluem_token_valido(self):
        self.token_csrf('/cadastro')
        self.token_csrf('/login')
        self.cadastrar()
        self.entrar()
        token = self.token_csrf('/avaliar/1?disciplina_id=10')
        resposta = self.web.post('/avaliar/1', data={
            **NOTAS, 'disciplina_id': '10', 'csrf_token': token})
        self.assertEqual(resposta.status_code, 303)
        for caminho in ('/', '/perfil'):
            token = self.token_csrf(caminho)
            self.assertTrue(token)
        self.assertEqual(self.web.post('/logout', data={'csrf_token': token}).status_code, 200)


if __name__ == '__main__':
    unittest.main()
