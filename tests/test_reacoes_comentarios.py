"""Reações pela interface: sessão, CSRF, isolamento de autoria e indisponibilidade."""
from unittest.mock import patch

from app.repositorio import repositorios
from tests.test_comentarios_publicar import BasePublicar


class TestReacoes(BasePublicar):
    def setUp(self):
        super().setUp()
        self.autor = self.entrar()
        self.postar({'disciplina_id': '10', 'texto': 'Explica com clareza.'})
        self.cid = self.comentarios()[0]['id']
        self.url = f'/professores/1/comentarios/{self.cid}/reacao'

    def reagir(self, reacao='curtir', **extra):
        dados = {'reacao': reacao, **extra,
                 'csrf_token': self.web.get('/teste/csrf').get_data(as_text=True)}
        return self.web.post(self.url, data=dados)

    def test_alternar_trocar_remover_e_manter_filtros(self):
        leitor = self.entrar('bia@gmail.com', 'Bia')
        resposta = self.reagir(usuario_id=self.autor, comentarios_disciplina='11',
                               disciplina_medias='10', next='/ranking')
        self.assertEqual(resposta.status_code, 303)
        self.assertIn('comentarios_disciplina=11', resposta.location)
        self.assertIn('disciplina_id=10', resposta.location)
        self.assertIn('next=/ranking', resposta.location)
        self.assertTrue(resposta.location.endswith('#comentarios'))
        reacoes = self.cliente.tabelas['reacoes_comentarios']
        self.assertEqual(reacoes, [{'comentario_id': self.cid, 'usuario_id': leitor, 'reacao': 'curtir'}])
        html = self.perfil()
        self.assertIn('aria-label="Gostei: 1"', html)
        self.assertIn('aria-pressed="true"', html)
        self.assertNotIn(leitor, html)
        self.assertEqual(self.reagir('descurtir').status_code, 303)
        self.assertEqual(len(reacoes), 1)
        self.assertEqual(reacoes[0]['reacao'], 'descurtir')
        self.assertEqual(self.reagir('descurtir').status_code, 303)
        self.assertEqual(reacoes, [])

    def test_autor_nao_reage(self):
        self.assertEqual(self.reagir().status_code, 403)
        self.assertEqual(self.cliente.tabelas['reacoes_comentarios'], [])

    def test_csrf_obrigatorio_e_acao_invalida(self):
        self.entrar('bia@gmail.com')
        self.assertEqual(self.web.post(self.url, data={'reacao': 'curtir'}).status_code, 400)
        self.assertEqual(self.reagir('outra').status_code, 400)
        self.assertEqual(self.cliente.tabelas['reacoes_comentarios'], [])

    def test_outro_professor_e_comentario_oculto_nao_recebem_reacoes(self):
        self.entrar('bia@gmail.com')
        self.url = f'/professores/2/comentarios/{self.cid}/reacao'
        self.assertEqual(self.reagir().status_code, 404)
        self.url = f'/professores/1/comentarios/{self.cid}/reacao'
        self.comentarios()[0]['ocultado_em'] = '2026-11-18T00:00:00Z'
        self.assertEqual(self.reagir().status_code, 404)

    def test_visitante_le_e_precisa_entrar_para_reagir(self):
        web = self.app.test_client()
        html = web.get('/professores/1').get_data(as_text=True)
        self.assertIn('Entrar para reagir', html)
        self.assertIn('0 curtidas', html)
        self.assertNotIn('👍', html)
        self.assertNotIn('👎', html)
        grupo = html.split('aria-label="Reações ao comentário de ana"', 1)[1].split('</div>', 1)[0]
        self.assertEqual(grupo.count('<svg'), 2)
        self.assertEqual(grupo.count('fill="none"'), 2)
        self.assertNotIn('name="reacao"', html)
        token = web.get('/teste/csrf').get_data(as_text=True)
        resposta = web.post(self.url, data={'reacao': 'curtir', 'csrf_token': token})
        self.assertEqual(resposta.status_code, 302)
        self.assertIn('/login', resposta.location)

    def test_falha_na_migracao_preserva_comentarios_e_medias(self):
        with self.app.app_context():
            repo = repositorios().comentarios
        with patch.object(repo, 'reacoes', side_effect=RuntimeError('indisponível')):
            html = self.perfil()
        self.assertIn('Explica com clareza.', html)
        self.assertIn('Médias Consolidadas', html)
        self.assertNotIn('comentario-reacoes', html)

    def test_contagem_nao_expoe_usuarios(self):
        self.entrar('bia@gmail.com')
        self.reagir()
        with self.app.app_context():
            contagens = repositorios().comentarios.reacoes([self.cid])
        self.assertEqual(contagens[self.cid], {'curtidas': 1, 'descurtidas': 0, 'minha_reacao': None})
