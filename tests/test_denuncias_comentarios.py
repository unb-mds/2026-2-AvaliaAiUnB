"""Denúncia de comentários (issue #215), com o cliente falso."""
import re
import unittest
from urllib.parse import parse_qs, urlsplit

from flask_wtf.csrf import generate_csrf

from app import create_app
from app.repositorio import DenunciaRepository
from app.validacoes import MOTIVOS_DENUNCIA, validar_denuncia
from tests.fake_supabase import ClienteFalso, entrar_pela_web

EMAIL_AUTORA = 'ana@gmail.com'
EMAIL_DENUNCIANTE = 'denunciante.secreta@gmail.com'
NOME_DENUNCIANTE = 'Denunciante Secreta'


class BaseDenuncia(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                               'SUPABASE_CLIENT': self.cliente})
        self.app.add_url_rule('/teste/csrf', 'teste_csrf', generate_csrf)
        # A autora e quem denuncia usam navegadores separados.
        self.web_autora = self.app.test_client()
        self.web = self.app.test_client()
        self.id_autora = self._entrar(self.web_autora, EMAIL_AUTORA, 'Ana')
        self.id_denunciante = self._entrar(self.web, EMAIL_DENUNCIANTE, NOME_DENUNCIANTE)
        self.username_denunciante = next(p['username'] for p in self.cliente.tabelas['perfis']
                                         if p['id'] == self.id_denunciante)
        self.cid = self.semear('comentário da Ana')

    def _entrar(self, web, email, nome):
        entrar_pela_web(web, self.cliente, email, nome)
        return next(u['id'] for u in self.cliente.auth.usuarios.values() if u['email'] == email)

    def semear(self, texto, usuario=None, ocultado_em=None):
        tabela = self.cliente.tabelas['comentarios']
        n = len(tabela) + 1
        tabela.append({'id': n, 'usuario_id': usuario or self.id_autora, 'professor_id': 1,
                       'disciplina_id': 10, 'texto': texto,
                       'criado_em': f'2026-03-01T10:00:{n:02d}+00:00',
                       'atualizado_em': f'2026-03-01T10:00:{n:02d}+00:00',
                       'ocultado_em': ocultado_em})
        return n

    def denuncias(self):
        return [dict(l) for l in self.cliente.tabelas['denuncias_comentarios']]

    def ver(self, caminho, web=None):
        return (web or self.web).get(caminho, headers={'Accept': 'text/html'})

    def denunciar(self, comentario_id=None, dados=None, web=None, csrf=True, accept='text/html'):
        web = web or self.web
        dados = dict({'motivo': 'ofensa'} if dados is None else dados)
        if csrf:
            dados['csrf_token'] = web.get('/teste/csrf').get_data(as_text=True)
        return web.post(f'/comentarios/{comentario_id or self.cid}/denunciar', data=dados,
                        headers={'Accept': accept})


class TestVisitante(BaseDenuncia):
    def test_visitante_e_mandado_ao_login_e_nada_e_gravado(self):
        visitante = self.app.test_client()
        resposta = self.ver(f'/comentarios/{self.cid}/denunciar', web=visitante)
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(urlsplit(resposta.headers['Location']).path, '/login')
        token = visitante.get('/teste/csrf').get_data(as_text=True)
        resposta = visitante.post(f'/comentarios/{self.cid}/denunciar',
                                  data={'csrf_token': token, 'motivo': 'spam'},
                                  headers={'Accept': 'text/html'})
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(urlsplit(resposta.headers['Location']).path, '/login')
        self.assertEqual(self.denuncias(), [])

    def test_visitante_de_api_recebe_401(self):
        resposta = self.app.test_client().post(f'/comentarios/{self.cid}/denunciar',
                                               headers={'Accept': 'application/json'})
        self.assertIn(resposta.status_code, (400, 401))   # sem CSRF ou sem sessão: nunca grava
        self.assertEqual(self.denuncias(), [])

    def test_visitante_nao_ve_o_link_de_denunciar(self):
        html = self.ver('/professores/1', web=self.app.test_client()).get_data(as_text=True)
        self.assertIn('comentário da Ana', html)
        self.assertNotIn('/denunciar', html)


class TestLinkNoPerfil(BaseDenuncia):
    def test_logado_ve_denunciar_no_comentario_alheio(self):
        html = self.ver('/professores/1').get_data(as_text=True)
        self.assertIn(f'/comentarios/{self.cid}/denunciar', html)
        self.assertIn('>Denunciar</a>', html)

    def test_autora_nao_ve_denunciar_no_proprio_comentario(self):
        html = self.ver('/professores/1', web=self.web_autora).get_data(as_text=True)
        self.assertNotIn('/denunciar', html)
        self.assertIn(f'/comentarios/{self.cid}/editar', html)


class TestFormulario(BaseDenuncia):
    def test_get_mostra_motivos_csrf_e_aviso_de_privacidade(self):
        resposta = self.ver(f'/comentarios/{self.cid}/denunciar?next=/professores%3Fnome%3Djo'
                            '&comentarios_disciplina=10')
        self.assertEqual(resposta.status_code, 200)
        html = resposta.get_data(as_text=True)
        self.assertIn('JOSÉ ÁVILA', html)
        self.assertIn('comentário da Ana', html)
        self.assertRegex(html, r'name="csrf_token" value="[^"]+"')
        for chave, rotulo in MOTIVOS_DENUNCIA.items():
            self.assertIn(f'value="{chave}"', html)
            self.assertIn(rotulo, html)
        self.assertIn('não veem quem denunciou', html)
        self.assertIn('maxlength="500"', html)
        self.assertIn('name="next" value="/professores?nome=jo"', html)
        self.assertIn('name="comentarios_disciplina" value="10"', html)
        cancelar = re.search(r'<a class="cancelar botao botao-secundario" href="([^"]+)">Cancelar</a>', html)
        voltar = urlsplit(cancelar.group(1).replace('&amp;', '&'))
        self.assertEqual(voltar.path, '/professores/1')
        self.assertEqual(voltar.fragment, 'comentarios')
        self.assertEqual(parse_qs(voltar.query)['next'], ['/professores?nome=jo'])

    def test_next_externo_e_descartado(self):
        html = self.ver(f'/comentarios/{self.cid}/denunciar?next=https://malicioso.example').get_data(as_text=True)
        self.assertNotIn('malicioso', html)


class TestEnviar(BaseDenuncia):
    def test_post_valido_grava_e_confirma_o_recebimento(self):
        resposta = self.denunciar(dados={'motivo': 'dados_pessoais',
                                         'explicacao': '  expõe a matrícula \r\n',
                                         'usuario_id': self.id_autora, 'next': '/professores'})
        self.assertEqual(resposta.status_code, 303)
        destino = urlsplit(resposta.headers['Location'])
        self.assertEqual(destino.path, f'/comentarios/{self.cid}/denunciar')
        self.assertEqual(parse_qs(destino.query)['next'], ['/professores'])

        [denuncia] = self.denuncias()
        self.assertEqual(denuncia['comentario_id'], self.cid)
        # O denunciante vem da sessão; o usuario_id do formulário é ignorado.
        self.assertEqual(denuncia['usuario_id'], self.id_denunciante)
        self.assertEqual(denuncia['motivo'], 'dados_pessoais')
        self.assertEqual(denuncia['explicacao'], 'expõe a matrícula')
        self.assertIsNone(denuncia['resolvida_em'])

        html = self.ver(resposta.headers['Location']).get_data(as_text=True)
        self.assertIn('Denúncia recebida', html)
        self.assertIn('Quem escreveu não fica sabendo quem denunciou', html)
        self.assertNotIn('<form method="post"', html)

    def test_explicacao_e_opcional(self):
        self.assertEqual(self.denunciar(dados={'motivo': 'spam', 'explicacao': '   '}).status_code, 303)
        self.assertIsNone(self.denuncias()[0]['explicacao'])

    def test_comentario_continua_visivel_depois_da_denuncia(self):
        self.denunciar()
        html = self.ver('/professores/1', web=self.app.test_client()).get_data(as_text=True)
        self.assertIn('comentário da Ana', html)

    def test_cliente_de_api_recebe_201(self):
        resposta = self.denunciar(accept='application/json')
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.get_json(), {'mensagem': 'Denúncia recebida.'})


class TestDuplicidade(BaseDenuncia):
    def test_segunda_denuncia_do_mesmo_usuario_e_recusada(self):
        self.assertEqual(self.denunciar().status_code, 303)
        resposta = self.denunciar(dados={'motivo': 'spam'})
        self.assertEqual(resposta.status_code, 409)
        self.assertIn('Denúncia recebida', resposta.get_data(as_text=True))
        self.assertEqual(len(self.denuncias()), 1)
        self.assertEqual(self.denuncias()[0]['motivo'], 'ofensa')

    def test_get_depois_de_denunciar_mostra_so_a_confirmacao(self):
        self.denunciar()
        html = self.ver(f'/comentarios/{self.cid}/denunciar').get_data(as_text=True)
        self.assertIn('Denúncia recebida', html)
        self.assertNotIn('name="motivo"', html)

    def test_duplicada_por_api_recebe_409(self):
        self.denunciar()
        resposta = self.denunciar(accept='application/json')
        self.assertEqual(resposta.status_code, 409)
        self.assertIn('denuncia', resposta.get_json()['erros'])

    def test_outra_pessoa_pode_denunciar_o_mesmo_comentario(self):
        self.denunciar()
        terceira = self.app.test_client()
        self._entrar(terceira, 'carla@gmail.com', 'Carla')
        self.assertEqual(self.denunciar(web=terceira).status_code, 303)
        self.assertEqual(len(self.denuncias()), 2)

    def test_depois_de_resolvida_pode_denunciar_de_novo(self):
        self.denunciar()
        self.cliente.tabelas['denuncias_comentarios'][0]['resolvida_em'] = '2026-04-01T00:00:00+00:00'
        self.assertEqual(self.denunciar(dados={'motivo': 'ameaca'}).status_code, 303)
        self.assertEqual([d['motivo'] for d in self.denuncias()], ['ofensa', 'ameaca'])

    def test_corrida_no_banco_conta_como_duplicada(self):
        repositorio = DenunciaRepository(self.cliente)
        repositorio.tem_denuncia_ativa = lambda *_: False   # simula duas requisições simultâneas
        self.assertTrue(repositorio.criar(self.cid, self.id_denunciante, 'spam'))
        self.assertFalse(repositorio.criar(self.cid, self.id_denunciante, 'spam'))
        self.assertEqual(len(self.denuncias()), 1)


class TestValidacao(BaseDenuncia):
    def test_motivo_ausente_ou_invalido_recebe_400(self):
        for motivo in ('', 'nao_gostei', None):
            with self.subTest(motivo=motivo):
                dados = {'explicacao': 'texto preservado'}
                if motivo is not None:
                    dados['motivo'] = motivo
                resposta = self.denunciar(dados=dados)
                self.assertEqual(resposta.status_code, 400)
                html = resposta.get_data(as_text=True)
                self.assertIn('Escolha o motivo da denúncia.', html)
                self.assertIn('>texto preservado</textarea>', html)
        self.assertEqual(self.denuncias(), [])

    def test_explicacao_longa_recebe_400_e_preserva_o_motivo(self):
        resposta = self.denunciar(dados={'motivo': 'spam', 'explicacao': 'x' * 501})
        self.assertEqual(resposta.status_code, 400)
        html = resposta.get_data(as_text=True)
        self.assertIn('no máximo 500 caracteres', html)
        self.assertRegex(html, r'value="spam" required\s+checked')
        self.assertEqual(self.denuncias(), [])

    def test_explicacao_com_500_caracteres_passa(self):
        self.assertEqual(self.denunciar(dados={'motivo': 'spam', 'explicacao': 'x' * 500}).status_code, 303)

    def test_sem_csrf_recebe_400_e_nada_e_gravado(self):
        resposta = self.denunciar(csrf=False)
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(self.denuncias(), [])

    def test_csrf_de_outra_sessao_e_recusado(self):
        token_alheio = self.web_autora.get('/teste/csrf').get_data(as_text=True)
        resposta = self.web.post(f'/comentarios/{self.cid}/denunciar',
                                 data={'csrf_token': token_alheio, 'motivo': 'spam'},
                                 headers={'Accept': 'text/html'})
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(self.denuncias(), [])

    def test_repositorio_recusa_motivo_invalido(self):
        with self.assertRaises(ValueError):
            DenunciaRepository(self.cliente).criar(self.cid, self.id_denunciante, 'qualquer')

    def test_validar_denuncia(self):
        self.assertEqual(validar_denuncia('ofensa', None), ('ofensa', None, {}))
        self.assertEqual(validar_denuncia(' spam ', ' a\r\nb '), ('spam', 'a\nb', {}))
        self.assertIn('motivo', validar_denuncia('', '')[2])


class TestComentarioNaoDenunciavel(BaseDenuncia):
    def test_autora_nao_denuncia_o_proprio_comentario(self):
        self.assertEqual(self.ver(f'/comentarios/{self.cid}/denunciar', web=self.web_autora).status_code, 404)
        self.assertEqual(self.denunciar(web=self.web_autora).status_code, 404)
        self.assertEqual(self.denuncias(), [])

    def test_comentario_inexistente_ou_oculto_da_404(self):
        oculto = self.semear('texto oculto', ocultado_em='2026-04-01T00:00:00+00:00')
        for cid in (999, oculto):
            with self.subTest(comentario=cid):
                self.assertEqual(self.ver(f'/comentarios/{cid}/denunciar').status_code, 404)
                self.assertEqual(self.denunciar(comentario_id=cid).status_code, 404)
        self.assertEqual(self.denuncias(), [])


class TestPrivacidade(BaseDenuncia):
    def test_autora_e_visitantes_nao_veem_quem_denunciou(self):
        self.denunciar(dados={'motivo': 'ofensa', 'explicacao': 'explicação reservada'})
        paginas = {
            'perfil (autora)': self.ver('/professores/1', web=self.web_autora),
            'perfil (visitante)': self.ver('/professores/1', web=self.app.test_client()),
            'editar (autora)': self.ver(f'/comentarios/{self.cid}/editar', web=self.web_autora),
            'excluir (autora)': self.ver(f'/comentarios/{self.cid}/excluir', web=self.web_autora),
        }
        for nome, resposta in paginas.items():
            with self.subTest(pagina=nome):
                self.assertEqual(resposta.status_code, 200)
                html = resposta.get_data(as_text=True)
                self.assertNotIn(self.username_denunciante, html)
                self.assertNotIn(NOME_DENUNCIANTE, html)
                self.assertNotIn('explicação reservada', html)
                self.assertNotIn('Denúncia recebida', html)

    def test_confirmacao_nao_mostra_o_autor_do_comentario(self):
        self.denunciar()
        html = self.ver(f'/comentarios/{self.cid}/denunciar').get_data(as_text=True)
        self.assertIn('comentário da Ana', html)
        self.assertNotIn(EMAIL_AUTORA, html)
        self.assertNotIn(self.id_autora, html)


if __name__ == '__main__':
    unittest.main()
