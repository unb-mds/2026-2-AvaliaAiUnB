"""Gravação no Supabase dos dados do scraper (sem selenium)."""
from turmas_sigaa import montar_payload_turmas

CONFLITO_PROFESSORES = "nome,departamento"
CONFLITO_DISCIPLINAS = "codigo"
CONFLITO_TURMAS = "professor_id,disciplina_id,ano,periodo"


def _supabase():
    """Import tardio: o --dry-run nunca importa supabase_client (nem lê o .env)."""
    from supabase_client import supabase

    return supabase


def salvar_professores(professores: list, cliente=None) -> dict:
    if not professores:
        print("[!] Nenhum professor para salvar.")
        return {}
    try:
        cliente = cliente or _supabase()
        response = (
            cliente.table("professores")
            .upsert(professores, on_conflict=CONFLITO_PROFESSORES)
            .execute()
        )
        print(f"[*] {len(response.data)} professores upsertados.")
        return {(p["nome"], p.get("departamento")): p["id"] for p in response.data}
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
