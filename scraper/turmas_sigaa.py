"""Montagem pura do payload de turmas (sem selenium nem Supabase)."""


def montar_payload_turmas(turmas: list, mapa_prof: dict, mapa_disc: dict) -> list:
    """Deduplica turmas pela chave única (professor, disciplina, ano, periodo).

    `mapa_prof` é {nome: id} (um professor por nome, issue #235) e
    `mapa_disc` é {codigo: id}. Turmas cujo professor ou disciplina não estão
    nos mapas são ignoradas.
    """
    vistos = set()
    payload = []

    for t in turmas:
        prof_id = mapa_prof.get(t["professor_nome"])
        disc_id = mapa_disc.get(t["disciplina_codigo"])

        if not prof_id or not disc_id:
            continue

        chave = (prof_id, disc_id, t["ano"], t["periodo"])

        if chave in vistos:
            continue

        vistos.add(chave)
        payload.append({
            "professor_id": prof_id,
            "disciplina_id": disc_id,
            "ano": t["ano"],
            "periodo": t["periodo"],
        })

    return payload
