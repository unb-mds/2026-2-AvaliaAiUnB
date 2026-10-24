"""Resumo final de uma execução do scraper (sem selenium nem Supabase)."""

MOTIVOS_LINHA = {
    "menos_de_8_celulas": "linha com menos de 8 células",
    "stale": "elemento obsoleto (stale) durante a leitura",
    "erro": "erro ao processar a linha",
    "sem_disciplina": "turma sem disciplina associada",
}


class Resumo:
    """Acumula unidades processadas, puladas e linhas ignoradas."""

    def __init__(self):
        self.unidades_ok = []
        self.unidades_sem_turmas = []
        self.unidades_puladas = []  # (unidade, motivo)
        self.linhas_puladas = {}
        self.a_definir_ignorados = 0

    def registrar_ok(self, unidade: str):
        self.unidades_ok.append(unidade)

    def registrar_sem_turmas(self, unidade: str):
        """Unidade que respondeu sem turmas: só aviso, não é falha."""
        self.unidades_sem_turmas.append(unidade)

    def registrar_unidade_pulada(self, unidade: str, motivo: str):
        """Falha técnica: a unidade não pôde ser lida."""
        self.unidades_puladas.append((unidade, motivo))

    def registrar_linha_pulada(self, motivo: str):
        if motivo not in MOTIVOS_LINHA:
            raise ValueError(f"Motivo de linha desconhecido: {motivo!r}")
        self.linhas_puladas[motivo] = self.linhas_puladas.get(motivo, 0) + 1

    def codigo_saida(self) -> int:
        """0 se nenhuma unidade falhou (unidade sem turmas é só aviso); 1 caso contrário."""
        return 1 if self.unidades_puladas else 0

    def imprimir(self):
        print("\n" + "=" * 55)
        print("[RESUMO]")
        print("=" * 55)
        print(f"Unidades lidas com turmas: {len(self.unidades_ok)}")

        print(f"Unidades sem turmas (aviso): {len(self.unidades_sem_turmas)}")
        for unidade in self.unidades_sem_turmas:
            print(f"  - {unidade}")

        print(f"Unidades puladas por erro: {len(self.unidades_puladas)}")
        for unidade, motivo in self.unidades_puladas:
            print(f"  - {unidade}: {motivo}")

        total_linhas = sum(self.linhas_puladas.values())
        print(f"Linhas puladas: {total_linhas}")
        for motivo, quantidade in sorted(self.linhas_puladas.items()):
            print(f"  - {MOTIVOS_LINHA[motivo]}: {quantidade}")

        print(f"'A DEFINIR DOCENTE' ignorados: {self.a_definir_ignorados}")
