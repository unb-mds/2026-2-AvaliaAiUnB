import os
import tempfile
import unittest
from unittest import mock

from app import database
from app.models import Disciplina, Professor, Usuario
from app.repositorio import (AvaliacaoRepository, DisciplinaRepository,
                             ProfessorRepository, UsuarioRepository)


class BancoTemporarioTestCase(unittest.TestCase):
    def setUp(self):
        # Usa o schema real (inicializar_banco) em um arquivo temporário.
        descritor, self.caminho = tempfile.mkstemp(suffix='.db')
        os.close(descritor)
        patcher = mock.patch.object(database, 'CAMINHO_BANCO', self.caminho)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(os.remove, self.caminho)
        database.inicializar_banco()
        self.professores = ProfessorRepository()
        self.disciplinas = DisciplinaRepository()


class TestProfessores(BancoTemporarioTestCase):
    def test_criar_professor_e_buscar_por_id(self):
        professor = Professor(nome='Ana Silva', departamento='CIC')

        sucesso, _ = self.professores.criar(professor)

        self.assertTrue(sucesso)
        encontrado = self.professores.buscar_por_id(professor.id)
        self.assertEqual(encontrado['nome'], 'Ana Silva')
        self.assertEqual(encontrado['departamento'], 'CIC')

    def test_buscar_por_nome_ignora_caixa_e_aceita_trecho(self):
        for nome in ['Ana SILVA', 'Bruno Costa', 'Carlos silveira']:
            self.professores.criar(Professor(nome=nome))

        nomes = [p['nome'] for p in self.professores.buscar_por_nome('silv')]

        self.assertEqual(nomes, ['Ana SILVA', 'Carlos silveira'])

    def test_homonimos_sao_permitidos(self):
        primeiro = Professor(nome='Ana Silva', departamento='CIC')
        segundo = Professor(nome='Ana Silva', departamento='MAT')

        self.assertTrue(self.professores.criar(primeiro)[0])
        self.assertTrue(self.professores.criar(segundo)[0])
        self.assertNotEqual(primeiro.id, segundo.id)


class TestDisciplinas(BancoTemporarioTestCase):
    def test_codigo_duplicado_e_rejeitado(self):
        primeira = Disciplina(nome='Calculo 1', codigo='MAT0025')
        segunda = Disciplina(nome='Outra Disciplina', codigo='MAT0025')

        self.assertTrue(self.disciplinas.criar(primeira)[0])
        sucesso, mensagem = self.disciplinas.criar(segunda)

        self.assertFalse(sucesso)
        self.assertIn('código', mensagem)
        self.assertIsNone(segunda.id)

    def test_buscar_por_id_e_por_codigo(self):
        disciplina = Disciplina(nome='Calculo 1', codigo='MAT0025')
        self.disciplinas.criar(disciplina)

        por_id = self.disciplinas.buscar_por_id(disciplina.id)
        por_codigo = self.disciplinas.buscar_por_codigo('MAT0025')

        self.assertEqual(por_id['codigo'], 'MAT0025')
        self.assertEqual(por_codigo['id'], disciplina.id)
        self.assertEqual(por_codigo['nome'], 'Calculo 1')

    def test_buscar_inexistente_retorna_none(self):
        self.assertIsNone(self.disciplinas.buscar_por_id(999))
        self.assertIsNone(self.disciplinas.buscar_por_codigo('XXX0000'))

    def test_listar_professores_da_disciplina(self):
        disciplina = Disciplina(nome='Calculo 1', codigo='MAT0025')
        outra = Disciplina(nome='Fisica 1', codigo='FIS0001')
        self.disciplinas.criar(disciplina)
        self.disciplinas.criar(outra)
        for nome in ['Bruno Costa', 'Ana Silva', 'Carlos Lima']:
            professor = Professor(nome=nome)
            self.professores.criar(professor)
            if nome != 'Carlos Lima':
                self.professores.vincular(professor.id, disciplina.id)
            else:
                self.professores.vincular(professor.id, outra.id)

        nomes = [p['nome'] for p in self.disciplinas.listar_professores(disciplina.id)]

        self.assertEqual(nomes, ['Ana Silva', 'Bruno Costa'])


class TestVinculo(BancoTemporarioTestCase):
    def test_vincular_faz_a_disciplina_aparecer_para_o_professor(self):
        professor = Professor(nome='Ana Silva', departamento='CIC')
        disciplina = Disciplina(nome='Calculo 1', codigo='MAT0025')
        self.professores.criar(professor)
        self.disciplinas.criar(disciplina)

        sucesso, _ = self.professores.vincular(professor.id, disciplina.id)

        self.assertTrue(sucesso)
        codigos = [d['codigo'] for d in self.professores.listar_disciplinas(professor.id)]
        self.assertEqual(codigos, ['MAT0025'])

    def test_vincular_duas_vezes_nao_duplica(self):
        professor = Professor(nome='Ana Silva', departamento='CIC')
        disciplina = Disciplina(nome='Calculo 1', codigo='MAT0025')
        self.professores.criar(professor)
        self.disciplinas.criar(disciplina)

        self.professores.vincular(professor.id, disciplina.id)
        sucesso, _ = self.professores.vincular(professor.id, disciplina.id)

        self.assertTrue(sucesso)
        self.assertEqual(len(self.professores.listar_disciplinas(professor.id)), 1)

    def test_vincular_com_ids_inexistentes_falha(self):
        sucesso, mensagem = self.professores.vincular(999, 999)

        self.assertFalse(sucesso)
        self.assertIn('não encontrad', mensagem)

    def test_vinculo_habilita_avaliacao_e_medias(self):
        professor = Professor(nome='Ana Silva', departamento='CIC')
        disciplina = Disciplina(nome='Calculo 1', codigo='MAT0025')
        usuario = Usuario(nome='Aluno', email='aluno@unb.br', senha='hash')
        self.professores.criar(professor)
        self.disciplinas.criar(disciplina)
        UsuarioRepository().criar_usuario(usuario)
        notas = {'avaliacao_geral': 4, 'didatica': 5, 'organizacao': 3,
                 'dificuldade': 2, 'disponibilidade': 4}
        avaliacoes = AvaliacaoRepository()

        with self.assertRaises(ValueError):
            avaliacoes.salvar(usuario.id, professor.id, disciplina.id, notas)

        self.professores.vincular(professor.id, disciplina.id)
        self.assertTrue(avaliacoes.salvar(usuario.id, professor.id, disciplina.id, notas))

        resultado = avaliacoes.calcular_medias(professor.id, disciplina.id)
        self.assertEqual(resultado['quantidade'], 1)
        self.assertEqual(resultado['medias']['didatica'], 5)
        self.assertEqual(resultado['medias']['avaliacao_geral'], 4)


if __name__ == '__main__':
    unittest.main()
