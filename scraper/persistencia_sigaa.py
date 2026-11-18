"""Gravação no Supabase dos dados do scraper (sem selenium)."""
from turmas_sigaa import montar_payload_turmas

CONFLITO_PROFESSORES = "nome"
CONFLITO_DISCIPLINAS = "codigo"
CONFLITO_TURMAS = "professor_id,disciplina_id,ano,periodo"
LOTE_CONSULTA = 100  # nomes por consulta .in_() (mantém a URL do PostgREST curta)


def _supabase():
    """Import tardio: o --dry-run nunca importa supabase_client (nem lê o .env)."""
    from supabase_client import supabase

    return supabase


def unificar_professores(professores: list) -> list:
    """Um registro por nome (issue #235): a primeira unidade vista é a que fica."""
    por_nome = {}
    for p in professores:
        por_nome.setdefault(p["nome"], p)
    return list(por_nome.values())


def salvar_professores(professores: list, cliente=None) -> dict:
    """Insere os professores novos e devolve {nome: id} de todos.

    Um professor é único pelo nome. Quem já existe não é alterado
    (ignore_duplicates), então o departamento gravado não muda a cada unidade
    raspada; os ids dos existentes são buscados depois do upsert.
    """
    if not professores:
        print("[!] Nenhum professor para salvar.")
        return {}
    unicos = unificar_professores(professores)
    try:
        cliente = cliente or _supabase()
        response = (
            cliente.table("professores")
            .upsert(unicos, on_conflict=CONFLITO_PROFESSORES, ignore_duplicates=True)
            .execute()
        )
        print(f"[*] {len(response.data)} professores novos (de {len(unicos)} únicos).")
        nomes = [p["nome"] for p in unicos]
        mapa = {}
        for i in range(0, len(nomes), LOTE_CONSULTA):
            linhas = (
                cliente.table("professores")
                .select("id,nome")
                .in_("nome", nomes[i:i + LOTE_CONSULTA])
                .execute()
            ).data
            mapa.update({p["nome"]: p["id"] for p in linhas})
        return mapa
    except Exception as e:
        print(f"[!] Erro ao salvar professores: {e}")
        return {}


def salvar_disciplinas(disciplinas: list, cliente=None) -> dict:
    if not disciplinas:
        return {}
    try:
        cliente = cliente or _supabase()
        response = (
            cliente.table("disciplinas")
            .upsert(disciplinas, on_conflict=CONFLITO_DISCIPLINAS)
            .execute()
        )
        print(f"[*] {len(response.data)} disciplinas upsertadas.")
        return {d["codigo"]: d["id"] for d in response.data}
    except Exception as e:
        print(f"[!] Erro ao salvar disciplinas: {e}")
        return {}


def salvar_turmas(turmas: list, mapa_prof: dict, mapa_disc: dict, cliente=None):
    if not turmas:
        return

    # 🔥 Deduplica turmas pela chave única (professor, disciplina, ano, periodo)
    payload = montar_payload_turmas(turmas, mapa_prof, mapa_disc)

    if not payload:
        print("[!] Nenhuma turma única para salvar.")
        return

    print(f"[*] Turmas únicas após deduplicação: {len(payload)} (de {len(turmas)} originais)")

    try:
        cliente = cliente or _supabase()
        response = (
            cliente.table("turmas")
            .upsert(payload, on_conflict=CONFLITO_TURMAS)
            .execute()
        )
        print(f"[*] {len(response.data)} turmas upsertadas.")
    except Exception as e:
        print(f"[!] Erro ao salvar turmas: {e}")
