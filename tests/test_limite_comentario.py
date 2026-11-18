"""Limite de envio de comentários: 10 por hora por usuário, com contador próprio.

Usa um app Flask mínimo com rotas registradas só aqui, para exercitar o decorator
sem depender das rotas reais nem do Supabase.
"""
import re
import unittest
from unittest.mock import patch

from flask import Flask, jsonify, render_template_string

from app.seguranca import configurar_seguranca, limitar_avaliacao, limitar_comentario, limiter

ALVO_OBTER_USUARIO = 'app.controllers.session_controller.obter_usuario_atual'


class TestLimiteComentario(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.testing = True
        app.config['SECRET_KEY'] = 'chave-exclusiva-dos-testes'
        configurar_seguranca(app)
        limiter.reset()

        @app.get('/')
        def formulario():
            return render_template_string(
                '<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">')

        @app.post('/comentar')
        @limitar_comentario
        def comentar():
            return jsonify(ok=True)

        @app.post('/avaliar')
        @limitar_avaliacao
        def avaliar():
            return jsonify(ok=True)

        self.web = app.test_client()
        self.usuario = {'id': 'usuario-1'}
        patcher = patch(ALVO_OBTER_USUARIO, lambda: self.usuario)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(limiter.reset)

    def enviar(self, rota, ip='10.0.0.1', **cabecalhos):
        html = self.web.get('/').get_data(as_text=True)
        token = re.search(r'value="([^"]+)"', html).group(1)
        return self.web.post(rota, data={'csrf_token': token}, headers=cabecalhos,
                             environ_overrides={'REMOTE_ADDR': ip})

    def esgotar(self, rota, quantidade, **kwargs):
        for _ in range(quantidade):
            self.assertEqual(self.enviar(rota, **kwargs).status_code, 200)

    def test_as_dez_primeiras_passam_e_a_11a_e_barrada(self):
        self.esgotar('/comentar', 10)
        self.assertEqual(self.enviar('/comentar').status_code, 429)

    def test_resposta_ao_exceder_e_a_mesma_do_limite_de_avaliacoes(self):
        self.esgotar('/comentar', 10)
        self.esgotar('/avaliar', 20)
        comentario, avaliacao = self.enviar('/comentar'), self.enviar('/avaliar')
        self.assertEqual((comentario.status_code, avaliacao.status_code), (429, 429))
        self.assertEqual(comentario.get_data(as_text=True), avaliacao.get_data(as_text=True))
        self.assertIn('Muitas tentativas', comentario.get_data(as_text=True))

    def test_429_responde_json_para_api(self):
        self.esgotar('/comentar', 10)
        resposta = self.enviar('/comentar', Accept='application/json')
        self.assertEqual(resposta.status_code, 429)
        self.assertIn('Muitas tentativas', resposta.get_json()['erro'])

    def test_limite_e_por_usuario_e_nao_por_ip(self):
        # IPs diferentes, mesmo usuário: o contador é um só.
        for i in range(10):
            self.assertEqual(self.enviar('/comentar', ip=f'10.1.0.{i}').status_code, 200)
        self.assertEqual(self.enviar('/comentar', ip='10.1.0.200').status_code, 429)

    def test_outro_usuario_nao_e_afetado_mesmo_no_mesmo_ip(self):
        self.esgotar('/comentar', 10)
        self.assertEqual(self.enviar('/comentar').status_code, 429)
        self.usuario = {'id': 'usuario-2'}
        self.assertEqual(self.enviar('/comentar').status_code, 200)

    def test_contador_de_comentarios_e_independente_do_de_avaliacoes(self):
        self.esgotar('/comentar', 10)
        self.assertEqual(self.enviar('/comentar').status_code, 429)
        self.assertEqual(self.enviar('/avaliar').status_code, 200)   # avaliar segue livre

    def test_esgotar_avaliacoes_nao_barra_comentarios(self):
        self.esgotar('/avaliar', 20)
        self.assertEqual(self.enviar('/avaliar').status_code, 429)
        self.assertEqual(self.enviar('/comentar').status_code, 200)  # comentar segue livre

    def test_get_nao_conta_no_limite(self):
        for _ in range(30):
            self.assertEqual(self.web.get('/comentar').status_code, 405)
        self.esgotar('/comentar', 10)

    def test_visitante_e_limitado_por_ip(self):
        self.usuario = None
        for _ in range(10):
            self.assertEqual(self.enviar('/comentar', ip='10.2.0.1').status_code, 200)
        self.assertEqual(self.enviar('/comentar', ip='10.2.0.1').status_code, 429)
        self.assertEqual(self.enviar('/comentar', ip='10.2.0.2').status_code, 200)

    def test_escopos_distintos(self):
        self.assertNotEqual(limitar_comentario, limitar_avaliacao)


if __name__ == '__main__':
    unittest.main()
