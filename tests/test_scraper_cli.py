import contextlib
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))

from cli_sigaa import montar_parser


class TestMontarParser(unittest.TestCase):
    def test_padroes(self):
        args = montar_parser().parse_args([])
        self.assertEqual(args.ano, "2026")
        self.assertEqual(args.periodo, "2")
        self.assertIsNone(args.unidade)  # None = todas as unidades
        self.assertEqual(args.pausa, 1.0)
        self.assertFalse(args.dry_run)
        self.assertFalse(args.headless)

    def test_parametros(self):
        args = montar_parser().parse_args(
            ["--ano", "2025", "--periodo", "1", "--unidade", "673",
             "--unidade", "12", "--dry-run"]
        )
        self.assertEqual((args.ano, args.periodo), ("2025", "1"))
        self.assertEqual(args.unidade, ["673", "12"])
        self.assertTrue(args.dry_run)

    def test_ano_e_periodo_invalidos_encerram(self):
        for argv in (["--ano", "26"], ["--periodo", "9"]):
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    montar_parser().parse_args(argv)


if __name__ == "__main__":
    unittest.main()
