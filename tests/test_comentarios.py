"""ComentarioRepository (issue #167), com o cliente Supabase falso em memória."""
import unittest

from app import create_app
from app.repositorio import LIMITE_COMENTARIOS, ComentarioRepository, repositorios
from tests.fake_supabase import ClienteFalso

ANA, BIA = 'uuid-ana', 'uuid-bia'
CAMPOS_PUBLICOS = {'id', 'texto', 'username', 'disciplina_nome', 'disciplina_codigo',
                   'criado_em', 'editado', 'e_meu'}


class BaseComentarios(unittest.TestCase):
    def setUp(self):
        self.cliente = ClienteFalso()
        # Prof. 1 ministra a disciplina 10 e 11; prof. 2 ministra só a 20.
        self.cliente.tabelas['vw_professor_disciplina'].append(
            {'professor_id': 1, 'disciplina_id': 11, 'codigo_disciplina': 'FGA0011',
             'disciplina': 'CÁLCULO 2', 'ano': 2026, 'periodo': 1})
        self.cliente.tabelas['perfis'] += [
            {'id': ANA, 'username': 'ana', 'nome_completo': 'Ana Silva', 'email': 'ana@gmail.com'},
            {'id': BIA, 'username': 'bia', 'nome_completo': 'Bia Souza', 'email': 'bia@gmail.com'},
        ]
        self.repo = ComentarioRepository(self.cliente)

    def semear(self, quantidade=1, usuario=ANA, professor=1, disciplina=10, **extra):
        """Insere comentários direto na tabela, com datas crescentes (YYYY-MM-DDTHH:MM:SS)."""
        tabela = self.cliente.tabelas['comentarios']
        for _ in range(quantidade):
            n = len(tabela) + 1
            tabela.append({
                'id': n, 'usuario_id': usuario, 'professor_id': professor,
                'disciplina_id': disciplina, 'texto': f'comentário {n}',
                'criado_em': f'2026-03-01T10:{n // 60:02d}:{n % 60:02d}+00:00',
                'atualizado_em': f'2026-03-01T10:{n // 60:02d}:{n % 60:02d}+00:00',
                'ocultado_em': None, **extra,
            })

    def linhas(self):
        return self.cliente.tabelas['comentarios']


class TestListagem(BaseComentarios):
    def test_lista_vazia(self):
        self.assertEqual(self.repo.listar_por_professor(1), ([], False))

    def test_nao_lista_ocultados(self):
        self.semear(2)
        self.semear(1, ocultado_em='2026-03-02T00:00:00+00:00')
        comentarios, _ = self.repo.listar_por_professor(1)
        self.assertEqual([c['id'] for c in comentarios], [2, 1])

    def test_so_do_professor_pedido(self):
        self.semear(1, professor=1)
        self.semear(1, professor=2, disciplina=20)
        comentarios, _ = self.repo.listar_por_professor(2)
        self.assertEqual([c['id'] for c in comentarios], [2])

    def test_ordem_mais_recente_primeiro_com_desempate_por_id(self):
        self.semear(3)
        # Empate de data entre os ids 4 e 5: o id maior vem primeiro.
        self.semear(2, criado_em='2026-04-01T00:00:00+00:00')
        comentarios, _ = self.repo.listar_por_professor(1)
        self.assertEqual([c['id'] for c in comentarios], [5, 4, 3, 2, 1])

    def test_filtro_por_disciplina(self):
        self.semear(2, disciplina=10)
        self.semear(1, disciplina=11)
        todos, _ = self.repo.listar_por_professor(1)
        so_11, _ = self.repo.listar_por_professor(1, disciplina_id=11)
        so_10, _ = self.repo.listar_por_professor(1, disciplina_id=10)
        self.assertEqual(len(todos), 3)
        self.assertEqual([c['id'] for c in so_11], [3])
        self.assertEqual([c['id'] for c in so_10], [2, 1])
        self.assertEqual(so_11[0]['disciplina_nome'], 'CÁLCULO 2')
        self.assertEqual(so_11[0]['disciplina_codigo'], 'FGA0011')

    def test_limite_exato_nao_avisa_que_ha_mais(self):
        self.semear(LIMITE_COMENTARIOS)
        comentarios, ha_mais = self.repo.listar_por_professor(1)
        self.assertEqual((len(comentarios), ha_mais), (LIMITE_COMENTARIOS, False))

    def test_acima_do_limite_devolve_os_mais_recentes_e_avisa(self):
        self.semear(LIMITE_COMENTARIOS + 1)
        comentarios, ha_mais = self.repo.listar_por_professor(1)
        self.assertEqual(len(comentarios), 50)
        self.assertTrue(ha_mais)
        self.assertEqual(comentarios[0]['id'], 51)
        self.assertNotIn(1, [c['id'] for c in comentarios])   # o mais antigo ficou de fora

    def test_limite_vale_depois_do_filtro_de_disciplina(self):
        self.semear(60, disciplina=10)
        self.semear(3, disciplina=11)
        so_11, ha_mais = self.repo.listar_por_professor(1, disciplina_id=11)
        self.assertEqual((len(so_11), ha_mais), (3, False))
        so_10, ha_mais = self.repo.listar_por_professor(1, disciplina_id=10)
        self.assertEqual((len(so_10), ha_mais), (50, True))

    def test_constante_do_limite(self):
        self.assertEqual(LIMITE_COMENTARIOS, 50)


class TestPrivacidade(BaseComentarios):
    def test_so_campos_publicos_sem_email_nem_usuario_id(self):
        self.semear(1, usuario=ANA)
        comentario, = self.repo.listar_por_professor(1)[0]
        self.assertEqual(set(comentario), CAMPOS_PUBLICOS)
        self.assertEqual(comentario['username'], 'ana')
        texto_inteiro = repr(comentario)
        for segredo in ('ana@gmail.com', ANA, 'Ana Silva'):
            self.assertNotIn(segredo, texto_inteiro)

    def test_e_meu_e_calculado_no_servidor(self):
        self.semear(1, usuario=ANA)
        self.semear(1, usuario=BIA)
        como_ana, _ = self.repo.listar_por_professor(1, usuario_atual_id=ANA)
        self.assertEqual({c['username']: c['e_meu'] for c in como_ana}, {'ana': True, 'bia': False})
        visitante, _ = self.repo.listar_por_professor(1)
        self.assertFalse(any(c['e_meu'] for c in visitante))

    def test_editado_so_depois_de_uma_edicao(self):
        self.semear(1)
        self.assertFalse(self.repo.listar_por_professor(1)[0][0]['editado'])
        self.assertTrue(self.repo.atualizar(1, ANA, 10, 'texto novo'))
        self.assertTrue(self.repo.listar_por_professor(1)[0][0]['editado'])


class TestEditado(unittest.TestCase):
    """A conta do "editado" aceita os formatos de data que o PostgREST devolve."""

    def editado(self, criado, atualizado):
        return ComentarioRepository._foi_editado({'criado_em': criado, 'atualizado_em': atualizado})

    def test_sem_fracao_e_com_deslocamento(self):
        self.assertFalse(self.editado('2026-11-17T20:39:00+00:00', '2026-11-17T20:39:00+00:00'))
        self.assertTrue(self.editado('2026-11-17T20:39:00+00:00', '2026-11-17T20:39:01+00:00'))

    def test_uma_a_seis_casas_decimais(self):
        for casas in range(1, 7):
            with self.subTest(casas=casas):
                criado = '2026-11-17T20:39:00.' + '1' * casas + '+00:00'
                depois = '2026-11-17T20:39:00.' + '2' * casas + '+00:00'
                self.assertFalse(self.editado(criado, criado))
                self.assertTrue(self.editado(criado, depois))

    def test_cinco_casas_decimais(self):
        self.assertTrue(self.editado('2026-11-17T20:39:00.12345+00:00',
                                     '2026-11-17T20:39:00.12346+00:00'))
        self.assertFalse(self.editado('2026-11-17T20:39:00.12345+00:00',
                                      '2026-11-17T20:39:00.12345+00:00'))

    def test_seis_casas_decimais(self):
        self.assertTrue(self.editado('2026-11-17T20:39:00.123456+00:00',
                                     '2026-11-17T20:39:00.123457+00:00'))

    def test_fracao_sem_zeros_a_direita_equivale_a_fracao_completa(self):
        self.assertFalse(self.editado('2026-11-17T20:39:00.5+00:00',
                                      '2026-11-17T20:39:00.500000+00:00'))

    def test_sufixo_z(self):
        self.assertTrue(self.editado('2026-11-17T20:39:00Z', '2026-11-17T20:39:05Z'))
        self.assertFalse(self.editado('2026-11-17T20:39:00.25Z', '2026-11-17T20:39:00.250000+00:00'))
        self.assertTrue(self.editado('2026-11-17T20:39:00Z', '2026-11-17T20:39:00.000001+00:00'))

    def test_data_invalida_nunca_levanta_e_vale_false(self):
        valida = '2026-11-17T20:39:00+00:00'
        for invalida in ('ontem', '2026-13-45T99:99:99+00:00', '', None, 123):
            with self.subTest(invalida=invalida):
                self.assertFalse(self.editado(valida, invalida))
                self.assertFalse(self.editado(invalida, valida))
        self.assertFalse(ComentarioRepository._foi_editado({}))

    def test_fuso_misto_nao_levanta(self):
        self.assertFalse(self.editado('2026-11-17T20:39:00', '2026-11-17T20:39:05+00:00'))


class TestCriar(BaseComentarios):
    def test_cria_com_usuario_do_argumento_e_texto_aparado(self):
        novo_id = self.repo.criar(ANA, 1, 10, '  Boa didática \r\n')
        gravado, = self.linhas()
        self.assertEqual(gravado['id'], novo_id)
        self.assertEqual((gravado['usuario_id'], gravado['professor_id'], gravado['disciplina_id']),
                         (ANA, 1, 10))
        self.assertEqual(gravado['texto'], 'Boa didática')

    def test_mesma_conta_pode_comentar_varias_vezes_no_mesmo_par(self):
        self.repo.criar(ANA, 1, 10, 'primeiro')
        self.repo.criar(ANA, 1, 10, 'segundo')
        self.assertEqual(len(self.linhas()), 2)

    def test_disciplina_de_outro_professor_e_recusada(self):
        with self.assertRaisesRegex(ValueError, 'não vinculada'):
            self.repo.criar(ANA, 1, 20, 'texto válido')   # a 20 é do professor 2
        self.assertEqual(self.linhas(), [])

    def test_disciplina_inexistente_e_professor_sem_turma_sao_recusados(self):
        for professor, disciplina in ((1, 999), (3, 10)):
            with self.subTest(professor=professor, disciplina=disciplina):
                with self.assertRaises(ValueError):
                    self.repo.criar(ANA, professor, disciplina, 'texto válido')
        self.assertEqual(self.linhas(), [])

    def test_texto_invalido_e_recusado(self):
        for texto in ('', ' a ', 'x' * 1001):
            with self.subTest(tamanho=len(texto)):
                with self.assertRaises(ValueError):
                    self.repo.criar(ANA, 1, 10, texto)
        self.assertEqual(self.linhas(), [])


class TestAtualizar(BaseComentarios):
    def test_autor_atualiza_texto_e_disciplina_e_nada_mais(self):
        self.semear(1, usuario=ANA, disciplina=10)
        antes = dict(self.linhas()[0])
        self.assertTrue(self.repo.atualizar(1, ANA, 11, ' novo texto '))
        depois = self.linhas()[0]
        self.assertEqual((depois['texto'], depois['disciplina_id']), ('novo texto', 11))
        for campo in ('usuario_id', 'professor_id', 'criado_em', 'ocultado_em'):
            self.assertEqual(depois[campo], antes[campo])
        self.assertGreater(depois['atualizado_em'], antes['atualizado_em'])

    def test_outro_usuario_nao_afeta_nada(self):
        self.semear(1, usuario=ANA)
        antes = [dict(l) for l in self.linhas()]
        self.assertFalse(self.repo.atualizar(1, BIA, 10, 'texto de outra pessoa'))
        self.assertEqual(self.linhas(), antes)

    def test_comentario_inexistente_devolve_false(self):
        self.assertFalse(self.repo.atualizar(99, ANA, 10, 'texto válido'))

    def test_disciplina_de_outro_professor_e_recusada_e_nada_muda(self):
        self.semear(1, usuario=ANA, professor=1, disciplina=10)
        antes = [dict(l) for l in self.linhas()]
        with self.assertRaisesRegex(ValueError, 'não vinculada'):
            self.repo.atualizar(1, ANA, 20, 'texto válido')
        self.assertEqual(self.linhas(), antes)

    def test_texto_invalido_e_recusado(self):
        self.semear(1, usuario=ANA)
        with self.assertRaises(ValueError):
            self.repo.atualizar(1, ANA, 10, ' ')
        self.assertEqual(self.linhas()[0]['texto'], 'comentário 1')


class TestExcluirEBuscar(BaseComentarios):
    def test_autor_exclui_so_o_proprio_comentario(self):
        self.semear(2, usuario=ANA)
        self.assertTrue(self.repo.excluir(1, ANA))
        self.assertEqual([l['id'] for l in self.linhas()], [2])

    def test_outro_usuario_nao_exclui(self):
        self.semear(1, usuario=ANA)
        self.assertFalse(self.repo.excluir(1, BIA))
        self.assertEqual(len(self.linhas()), 1)

    def test_excluir_inexistente_devolve_false(self):
        self.assertFalse(self.repo.excluir(99, ANA))

    def test_buscar_do_usuario(self):
        self.semear(1, usuario=ANA, disciplina=11)
        achado = self.repo.buscar_do_usuario(1, ANA)
        self.assertEqual((achado['id'], achado['professor_id'], achado['disciplina_id']), (1, 1, 11))
        self.assertEqual(achado['disciplina_nome'], 'CÁLCULO 2')
        self.assertNotIn('usuario_id', achado)
        self.assertIsNone(self.repo.buscar_do_usuario(1, BIA))
        self.assertIsNone(self.repo.buscar_do_usuario(99, ANA))


class TestRegistro(unittest.TestCase):
    def test_repositorio_registrado_no_app(self):
        app = create_app({'TESTING': True, 'SECRET_KEY': 'chave-exclusiva-dos-testes',
                          'SUPABASE_CLIENT': ClienteFalso()})
        with app.app_context():
            self.assertIsInstance(repositorios().comentarios, ComentarioRepository)


if __name__ == '__main__':
    unittest.main()
