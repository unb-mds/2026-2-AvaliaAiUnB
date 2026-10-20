"""Regressões de configuração segura e de sigilo das chaves."""
import io
import os
from pathlib import Path
import runpy
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

from app import create_app
from tests.fake_supabase import ClienteFalso

RAIZ = Path(__file__).resolve().parent.parent


class TestConfiguracaoSegura(unittest.TestCase):
    def setUp(self):
        ambiente = patch.dict(os.environ, {}, clear=True)
        dotenv = patch('app.load_dotenv')
        ambiente.start()
        dotenv.start()
        self.addCleanup(ambiente.stop)
        self.addCleanup(dotenv.stop)

    def criar_app(self):
        return create_app({'TESTING': True, 'SUPABASE_CLIENT': ClienteFalso()})

    def test_secret_key_obrigatoria(self):
        for valor in (None, '', '   '):
            with self.subTest(valor=valor):
                if valor is None:
                    os.environ.pop('SECRET_KEY', None)
                else:
                    os.environ['SECRET_KEY'] = valor
                with self.assertRaisesRegex(RuntimeError, 'SECRET_KEY'):
                    self.criar_app()

    def test_secret_key_lida_do_ambiente(self):
        os.environ['SECRET_KEY'] = 'chave-exclusiva-deste-teste'
        self.assertEqual(self.criar_app().secret_key, os.environ['SECRET_KEY'])

    def test_debug_desligado_por_padrao_e_valores_falsos(self):
        os.environ['SECRET_KEY'] = 'chave-exclusiva-deste-teste'
        self.assertFalse(self.criar_app().debug)
        for valor in ('', '0', 'false', 'off', 'no', 'invalido'):
            with self.subTest(valor=valor):
                os.environ['FLASK_DEBUG'] = valor
                self.assertFalse(self.criar_app().debug)

    def test_debug_habilitado_explicitamente(self):
        os.environ['SECRET_KEY'] = 'chave-exclusiva-deste-teste'
        for valor in ('1', 'true', 'yes', 'on', ' TRUE '):
            with self.subTest(valor=valor):
                os.environ['FLASK_DEBUG'] = valor
                self.assertTrue(self.criar_app().debug)

    def test_run_sem_debug_nao_habilita_console_ou_reloader(self):
        os.environ['SECRET_KEY'] = 'chave-exclusiva-deste-teste'
        for valor in (None, '0', 'false', 'off', 'invalido'):
            with self.subTest(valor=valor):
                if valor is not None:
                    os.environ['FLASK_DEBUG'] = valor
                app = self.criar_app()
                with patch('app.create_app', return_value=app), \
                        patch('werkzeug.serving.run_simple') as servidor, \
                        redirect_stdout(io.StringIO()):
                    runpy.run_path(str(RAIZ / 'run.py'), run_name='__main__')
                servidor.assert_called_once()
                self.assertFalse(servidor.call_args.kwargs['use_debugger'])
                self.assertFalse(servidor.call_args.kwargs['use_reloader'])

    def test_dotenv_carregado_antes_da_configuracao(self):
        def carregar(_caminho):
            os.environ['SECRET_KEY'] = 'chave-exclusiva-do-dotenv-de-teste'
            os.environ['FLASK_DEBUG'] = '1'

        with patch('app.load_dotenv', side_effect=carregar) as dotenv:
            app = self.criar_app()
        dotenv.assert_called_once_with(RAIZ / '.env')
        self.assertEqual(app.secret_key, 'chave-exclusiva-do-dotenv-de-teste')
        self.assertTrue(app.debug)

    def test_scraper_nao_imprime_chave(self):
        chave = 'chave-ficticia-para-teste-de-log-sem-credenciais-reais'
        saida = io.StringIO()
        with patch.dict(os.environ, {'SUPABASE_URL': 'https://exemplo.supabase.co',
                                     'SUPABASE_SERVICE_KEY': chave}), \
                patch('dotenv.load_dotenv'), patch('supabase.create_client') as cliente, \
                redirect_stdout(saida), redirect_stderr(saida):
            runpy.run_path(str(RAIZ / 'scraper' / 'supabase_client.py'))
        cliente.assert_called_once_with('https://exemplo.supabase.co', chave)
        self.assertNotIn(chave[:20], saida.getvalue())
        self.assertNotIn(chave, saida.getvalue())


if __name__ == '__main__':
    unittest.main()
