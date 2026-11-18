"""Editar e excluir o próprio comentário (issue #167), com o cliente falso."""
import re
import unittest
from urllib.parse import parse_qs, urlsplit

from flask_wtf.csrf import generate_csrf

from app import create_app
from app.repositorio import repositorios
from app.validacoes import CRITERIOS
from tests.fake_supabase import ClienteFalso, entrar_pela_web

EMAIL = 'ana@gmail.com'
EMAIL_BIA = 'bia@gmail.com'
BIA = 'uuid-bia'
OUTRO_USUARIO = 'uuid-de-outra-pessoa'


class BaseEdicao(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        # Professor 1 ministra as disciplinas 10 e 11; o professor 2, só a 20.
        self.cliente.tabelas['vw_professor_disciplina'].append(
            {'professor_id': 1, 'disciplina_id': 11, 'codigo_disciplina': 'FGA0011',
             'disciplina': 'CÁLCULO 2', 'ano': 2026, 'periodo': 1})
        self.cliente.tabelas['perfis'].append(
            {'id': BIA, 'username': 'bia', 'nome_completo': 'Bia Souza', 'email': EMAIL_BIA})
        self.app = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                               'SUPABASE_CLIENT': self.cliente})
        self.app.add_url_rule('/teste/csrf', 'teste_csrf', generate_csrf)
        self.web = self.app.test_client()

    def entrar(self):
        entrar_pela_web(self.web, self.cliente, EMAIL, 'Ana')
        self.id_logado = next(u['id'] for u in self.cliente.auth.usuarios.values()
                              if u['email'] == EMAIL)
        return self.id_logado

    def semear(self, texto='comentário original', usuario=None, professor=1, disciplina=10):
        tabela = self.cliente.tabelas['comentarios']
        n = len(tabela) + 1
        tabela.append({'id': n, 'usuario_id': usuario or self.id_logado, 'professor_id': professor,
                       'disciplina_id': disciplina, 'texto': texto,
                       'criado_em': f'2026-03-01T10:00:{n:02d}+00:00',
                       'atualizado_em': f'2026-03-01T10:00:{n:02d}+00:00', 'ocultado_em': None})
        return n

    def comentarios(self):
        return [dict(l) for l in self.cliente.tabelas['comentarios']]

    def ver(self, caminho, web=None):
        return (web or self.web).get(caminho, headers={'Accept': 'text/html'})

    def enviar(self, caminho, dados=None, csrf=True, **cabecalhos):
        dados = dict(dados or {})
        if csrf:
            dados['csrf_token'] = self.web.get('/teste/csrf').get_data(as_text=True)
        return self.web.post(caminho, data=dados, headers={'Accept': 'text/html', **cabecalhos})

    def editar(self, comentario_id, dados, **kwargs):
        return self.enviar(f'/comentarios/{comentario_id}/editar', dados, **kwargs)

    def excluir(self, comentario_id, dados=None, **kwargs):
        return self.enviar(f'/comentarios/{comentario_id}/excluir', dados, **kwargs)


class TestVisitante(BaseEdicao):
    def test_visitante_e_mandado_ao_login(self):
        self.entrar()
        self.semear()
        visitante = self.app.test_client()
        for caminho in ('/comentarios/1/editar', '/comentarios/1/excluir'):
            with self.subTest(caminho=caminho, metodo='GET'):
                resposta = self.ver(caminho, web=visitante)
                self.assertEqual(resposta.status_code, 302)
                self.assertEqual(urlsplit(resposta.headers['Location']).path, '/login')
        for rota in ('editar', 'excluir'):
            with self.subTest(rota=rota, metodo='POST'):
                token = visitante.get('/teste/csrf').get_data(as_text=True)
                resposta = visitante.post(f'/comentarios/1/{rota}', headers={'Accept': 'text/html'},
                                          data={'csrf_token': token, 'texto': 'invasão',
                                                'disciplina_id': '10'})
                self.assertEqual(resposta.status_code, 302)
                self.assertEqual(urlsplit(resposta.headers['Location']).path, '/login')
        self.assertEqual(self.comentarios()[0]['texto'], 'comentário original')

    def test_visitante_nao_ve_links_de_editar_nem_excluir(self):
        self.entrar()
        self.semear()
        html = self.ver('/professores/1', web=self.app.test_client()).get_data(as_text=True)
        self.assertIn('comentário original', html)
        self.assertNotIn('/comentarios/', html)


class TestEditar(BaseEdicao):
    def setUp(self):
        super().setUp()
        self.entrar()
        self.cid = self.semear('texto original', disciplina=10)

    def test_get_mostra_o_formulario_preenchido(self):
        resposta = self.ver(f'/comentarios/{self.cid}/editar?next=/professores%3Fnome%3Djo&comentarios_disciplina=11')
        self.assertEqual(resposta.status_code, 200)
        html = resposta.get_data(as_text=True)
        self.assertIn('JOSÉ ÁVILA', html)
        self.assertIn('CÁLCULO 1', html)
        self.assertRegex(html, r'name="csrf_token" value="[^"]+"')
        self.assertRegex(html, r'<textarea name="texto" id="texto_comentario" rows="5" maxlength="1000" required')
        self.assertIn('>texto original</textarea>', html)
        self.assertRegex(html, r'<option value="10"\s+selected>')
        self.assertNotRegex(html, r'<option value="11"\s+selected>')
        self.assertIn('2 a 1.000 caracteres', html)
        self.assertIn('Salvar alterações', html)
        self.assertIn('name="next" value="/professores?nome=jo"', html)
        self.assertIn('name="comentarios_disciplina" value="11"', html)
        cancelar = re.search(r'<a class="cancelar botao botao-secundario" href="([^"]+)">Cancelar</a>', html)
        voltar = urlsplit(cancelar.group(1).replace('&amp;', '&'))
        self.assertEqual(voltar.path, '/professores/1')
        self.assertEqual(voltar.fragment, 'comentarios')
        self.assertEqual(parse_qs(voltar.query)['comentarios_disciplina'], ['11'])

    def test_post_com_sucesso_salva_e_preserva_a_data_original(self):
        antes = self.comentarios()[0]
        resposta = self.editar(self.cid, {'disciplina_id': '10', 'texto': '  texto corrigido \r\n'})
        self.assertEqual(resposta.status_code, 303)
        depois = self.comentarios()[0]
        self.assertEqual(depois['texto'], 'texto corrigido')
        self.assertEqual(depois['criado_em'], antes['criado_em'])
        self.assertNotEqual(depois['atualizado_em'], antes['atualizado_em'])
        html = self.ver('/professores/1').get_data(as_text=True)
        self.assertIn('texto corrigido', html)
        self.assertEqual(html.count('(editado)'), 1)

    def test_post_pode_trocar_para_outra_disciplina_do_mesmo_professor(self):
        resposta = self.editar(self.cid, {'disciplina_id': '11', 'texto': 'texto válido'})
        self.assertEqual(resposta.status_code, 303)
        self.assertEqual(self.comentarios()[0]['disciplina_id'], 11)

    def test_redirect_preserva_next_e_filtro_validados(self):
        resposta = self.editar(self.cid, {'disciplina_id': '10', 'texto': 'texto válido',
                                          'next': '/professores?nome=jo',
                                          'comentarios_disciplina': '11'})
        destino = urlsplit(resposta.headers['Location'])
        consulta = parse_qs(destino.query)
        self.assertEqual((destino.path, destino.fragment), ('/professores/1', 'comentarios'))
        self.assertEqual(consulta['next'], ['/professores?nome=jo'])
        self.assertEqual(consulta['comentarios_disciplina'], ['11'])

    def test_redirect_descarta_next_externo_e_filtro_de_outro_professor(self):
        resposta = self.editar(self.cid, {'disciplina_id': '10', 'texto': 'texto válido',
                                          'next': 'https://evil.com/x',
                                          'comentarios_disciplina': '20'})
        consulta = parse_qs(urlsplit(resposta.headers['Location']).query)
        self.assertEqual(consulta['next'], ['/professores'])
        self.assertNotIn('comentarios_disciplina', consulta)
        self.assertNotIn('evil.com', resposta.headers['Location'])

    def test_texto_invalido_da_400_preserva_e_nada_muda(self):
        antes = self.comentarios()
        for texto in ('x', '   ', 'z' * 1001):
            with self.subTest(tamanho=len(texto)):
                resposta = self.editar(self.cid, {'disciplina_id': '11', 'texto': texto})
                self.assertEqual(resposta.status_code, 400)
                html = resposta.get_data(as_text=True)
                self.assertIn(f'>{texto}</textarea>', html)
                self.assertRegex(html, r'<option value="11"\s+selected>')
                self.assertIn('role="alert"', html)
                self.assertIn('aria-invalid="true"', html)
        self.assertEqual(self.comentarios(), antes)

    def test_disciplina_de_outro_professor_da_erro_e_nada_muda(self):
        antes = self.comentarios()
        resposta = self.editar(self.cid, {'disciplina_id': '20', 'texto': 'texto novo e válido'})
        self.assertEqual(resposta.status_code, 400)
        html = resposta.get_data(as_text=True)
        self.assertIn('Escolha a disciplina.', html)
        self.assertIn('>texto novo e válido</textarea>', html)
        self.assertRegex(html, r'<select name="disciplina_id"[^>]*aria-invalid="true"')
        self.assertEqual(self.comentarios(), antes)

    def test_disciplina_invalida_ou_ausente_da_erro(self):
        antes = self.comentarios()
        for dados in ({'disciplina_id': 'abc', 'texto': 'texto válido'},
                      {'disciplina_id': '', 'texto': 'texto válido'},
                      {'texto': 'texto válido'}):
            with self.subTest(dados=dados):
                self.assertEqual(self.editar(self.cid, dados).status_code, 400)
        self.assertEqual(self.comentarios(), antes)

    def test_professor_e_autor_enviados_no_formulario_sao_ignorados(self):
        antes = self.comentarios()[0]
        resposta = self.editar(self.cid, {
            'disciplina_id': '11', 'texto': 'texto novo', 'professor_id': '2',
            'usuario_id': OUTRO_USUARIO, 'criado_em': '2000-01-01T00:00:00+00:00',
            'ocultado_em': '2026-01-01T00:00:00+00:00', 'id': '99'})
        self.assertEqual(resposta.status_code, 303)
        depois = self.comentarios()
        self.assertEqual(len(depois), 1)
        for campo in ('id', 'professor_id', 'usuario_id', 'criado_em', 'ocultado_em'):
            self.assertEqual(depois[0][campo], antes[campo], campo)
        self.assertEqual((depois[0]['texto'], depois[0]['disciplina_id']), ('texto novo', 11))

    def test_sem_csrf_da_erro_e_nada_muda(self):
        antes = self.comentarios()
        resposta = self.editar(self.cid, {'disciplina_id': '10', 'texto': 'sem token'}, csrf=False)
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(self.comentarios(), antes)

    def test_script_sai_escapado_na_pagina_de_edicao(self):
        perigoso = '</textarea><script>alert(1)</script>'
        self.cliente.tabelas['comentarios'][0]['texto'] = perigoso
        html = self.ver(f'/comentarios/{self.cid}/editar').get_data(as_text=True)
        self.assertIn('&lt;/textarea&gt;&lt;script&gt;alert(1)&lt;/script&gt;', html)
        self.assertNotIn('<script>alert(1)', html)
        erro = self.editar(self.cid, {'disciplina_id': '', 'texto': perigoso}).get_data(as_text=True)
        self.assertIn('&lt;/textarea&gt;&lt;script&gt;', erro)
        self.assertNotIn('<script>alert(1)', erro)


class TestExcluir(BaseEdicao):
    def setUp(self):
        super().setUp()
        self.entrar()
        self.cid = self.semear('texto para excluir', disciplina=11)
        self.outro = self.semear('texto que fica', disciplina=10)

    def test_get_mostra_a_confirmacao_e_nao_apaga(self):
        resposta = self.ver(f'/comentarios/{self.cid}/excluir?next=/professores&comentarios_disciplina=11')
        self.assertEqual(resposta.status_code, 200)
        html = resposta.get_data(as_text=True)
        self.assertIn('JOSÉ ÁVILA', html)
        self.assertIn('CÁLCULO 2 — FGA0011', html)
        self.assertIn('texto para excluir', html)
        self.assertIn('não pode ser desfeita', html)
        self.assertRegex(html, r'<a class="cancelar botao botao-primario" href="[^"]+" autofocus>Cancelar</a>')
        self.assertIn('Excluir comentário</button>', html)
        self.assertRegex(html, r'name="csrf_token" value="[^"]+"')
        self.assertEqual(len(self.comentarios()), 2)

    def test_confirmacao_mostra_so_um_trecho_de_comentario_longo(self):
        self.cliente.tabelas['comentarios'][0]['texto'] = 'a' * 150 + 'b' * 150
        html = self.ver(f'/comentarios/{self.cid}/excluir').get_data(as_text=True)
        self.assertIn('a' * 150, html)
        self.assertNotIn('b' * 150, html)

    def test_post_apaga_so_o_proprio_comentario_e_redireciona(self):
        resposta = self.excluir(self.cid, {'next': '/professores?nome=jo', 'comentarios_disciplina': '10'})
        self.assertEqual(resposta.status_code, 303)
        self.assertEqual([c['id'] for c in self.comentarios()], [self.outro])
        destino = urlsplit(resposta.headers['Location'])
        self.assertEqual((destino.path, destino.fragment), ('/professores/1', 'comentarios'))
        consulta = parse_qs(destino.query)
        self.assertEqual(consulta['next'], ['/professores?nome=jo'])
        self.assertEqual(consulta['comentarios_disciplina'], ['10'])
        self.assertNotIn('texto para excluir', self.ver('/professores/1').get_data(as_text=True))

    def test_post_responde_json_quando_o_accept_pede(self):
        resposta = self.excluir(self.cid, Accept='application/json')
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('excluído', resposta.get_json()['mensagem'])
        self.assertEqual([c['id'] for c in self.comentarios()], [self.outro])

    def test_sem_csrf_da_erro_e_nada_e_apagado(self):
        resposta = self.excluir(self.cid, csrf=False)
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(len(self.comentarios()), 2)

    def test_script_sai_escapado_na_confirmacao(self):
        self.cliente.tabelas['comentarios'][0]['texto'] = '<script>alert(1)</script>'
        html = self.ver(f'/comentarios/{self.cid}/excluir').get_data(as_text=True)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', html)
        self.assertNotIn('<script>alert(1)', html)


class TestDeOutraPessoa(BaseEdicao):
    def setUp(self):
        super().setUp()
        self.entrar()
        self.meu = self.semear('meu comentário')
        self.alheio = self.semear('comentário da bia', usuario=BIA)

    def test_editar_ou_excluir_de_outra_pessoa_da_404_e_nada_muda(self):
        antes = self.comentarios()
        casos = [
            ('GET editar', lambda: self.ver(f'/comentarios/{self.alheio}/editar')),
            ('GET excluir', lambda: self.ver(f'/comentarios/{self.alheio}/excluir')),
            ('POST editar', lambda: self.editar(self.alheio, {'disciplina_id': '10', 'texto': 'invasão'})),
            ('POST excluir', lambda: self.excluir(self.alheio)),
        ]
        for nome, chamada in casos:
            with self.subTest(nome):
                resposta = chamada()
                self.assertEqual(resposta.status_code, 404)
                self.assertNotIn('comentário da bia', resposta.get_data(as_text=True))
        self.assertEqual(self.comentarios(), antes)

    def test_id_inexistente_da_404(self):
        for nome, chamada in (
                ('GET editar', lambda: self.ver('/comentarios/999/editar')),
                ('GET excluir', lambda: self.ver('/comentarios/999/excluir')),
                ('POST editar', lambda: self.editar(999, {'disciplina_id': '10', 'texto': 'texto'})),
                ('POST excluir', lambda: self.excluir(999))):
            with self.subTest(nome):
                self.assertEqual(chamada().status_code, 404)

    def test_links_so_aparecem_nos_comentarios_do_proprio_usuario(self):
        html = self.ver('/professores/1?comentarios_disciplina=10').get_data(as_text=True)
        self.assertEqual(html.count('>Editar</a>'), 1)
        self.assertEqual(html.count('>Excluir</a>'), 1)
        self.assertIn(f'/comentarios/{self.meu}/editar?', html)
        self.assertIn(f'/comentarios/{self.meu}/excluir?', html)
        self.assertNotIn(f'/comentarios/{self.alheio}/editar', html)
        self.assertNotIn(f'/comentarios/{self.alheio}/excluir', html)
        # No comentário alheio só aparece a denúncia (issue #215).
        self.assertIn(f'/comentarios/{self.alheio}/denunciar?', html)
        self.assertIn('comentarios_disciplina=10', re.search(
            rf'href="(/comentarios/{self.meu}/editar[^"]*)"', html).group(1))
        self.assertIn('next=', re.search(
            rf'href="(/comentarios/{self.meu}/excluir[^"]*)"', html).group(1))

    def test_comentario_de_outra_pessoa_continua_visivel_sem_links(self):
        html = self.ver('/professores/1').get_data(as_text=True)
        self.assertIn('comentário da bia', html)
        self.assertIn('meu comentário', html)


class TestPrivacidadeEIndependencia(BaseEdicao):
    def setUp(self):
        super().setUp()
        self.entrar()
        self.cid = self.semear('texto do usuário')
        self.semear('texto da bia', usuario=BIA)

    def test_paginas_nunca_contem_email_nem_ids_de_usuario(self):
        paginas = [
            self.ver(f'/comentarios/{self.cid}/editar').get_data(as_text=True),
            self.ver(f'/comentarios/{self.cid}/excluir').get_data(as_text=True),
            self.editar(self.cid, {'disciplina_id': '', 'texto': 'x',
                                   'usuario_id': OUTRO_USUARIO}).get_data(as_text=True),
            self.ver('/professores/1').get_data(as_text=True),
        ]
        for html in paginas:
            # O username ("ana", "bia") é público; e-mail, nome completo e ids não.
            for segredo in (EMAIL, EMAIL_BIA, self.id_logado, BIA, OUTRO_USUARIO, 'Bia Souza'):
                self.assertNotIn(segredo, html)

    def test_sem_safe_nos_templates_novos(self):
        from pathlib import Path
        for nome in ('editar_comentario.html', 'excluir_comentario.html', 'perfil_professor.html'):
            modelo = Path('app/templates', nome).read_text(encoding='utf-8')
            self.assertNotIn('|safe', modelo.replace(' ', ''), nome)
        html = self.ver(f'/comentarios/{self.cid}/editar').get_data(as_text=True)
        self.assertNotIn('style=', html)

    def test_editar_e_excluir_nao_alteram_avaliacoes_medias_nem_ranking(self):
        for n in range(5):
            self.cliente.tabelas['avaliacoes'].append({
                'id': n + 1, 'usuario_id': f'uuid-{n}', 'professor_id': 1, 'disciplina_id': 10,
                'ano': 2026, 'periodo': 1, **{c: 3 + n % 3 for c in CRITERIOS}})

        def retrato():
            with self.app.app_context():
                repos = repositorios()
                return (repos.avaliacoes.calcular_medias(1), repos.avaliacoes.calcular_medias(1, 10),
                        repos.professores.ranking(), repos.professores.catalogo())

        tabela = [dict(l) for l in self.cliente.tabelas['avaliacoes']]
        antes, ranking = retrato(), self.ver('/ranking').get_data(as_text=True)

        self.assertEqual(self.editar(self.cid, {'disciplina_id': '11', 'texto': 'editado'}).status_code, 303)
        self.assertEqual(self.excluir(self.cid).status_code, 303)

        self.assertEqual(self.cliente.tabelas['avaliacoes'], tabela)
        self.assertEqual(retrato(), antes)
        self.assertEqual(self.ver('/ranking').get_data(as_text=True), ranking)


if __name__ == '__main__':
    unittest.main()
