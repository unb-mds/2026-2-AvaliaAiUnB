import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client


def encontrar_env():
    atual = Path(__file__).resolve().parent
    for _ in range(5):
        candidato = atual / ".env"
        if candidato.exists():
            return candidato
        atual = atual.parent
    return None


env_path = encontrar_env()

if env_path:
    print(f"[supabase_client] Carregando .env de: {env_path}")
    load_dotenv(env_path)
else:
    print("[supabase_client] AVISO: nenhum .env encontrado.")
    load_dotenv()


# 🔥 Normalização BRUTA
def normalizar_url(url: str) -> str:
    if not url:
        return url
    url = url.strip().rstrip("/")
    # Remove /rest/v1 se estiver no final
    for sufixo in ["/rest/v1", "/rest", "/v1"]:
        if url.endswith(sufixo):
            url = url[: -len(sufixo)]
            url = url.rstrip("/")
    return url


SUPABASE_URL = normalizar_url(os.getenv("SUPABASE_URL"))
SUPABASE_SERVICE_KEY = (os.getenv("SUPABASE_SERVICE_KEY") or "").strip()


print(f"[supabase_client] URL normalizada: {SUPABASE_URL}")
print(f"[supabase_client] Key: {SUPABASE_SERVICE_KEY[:20]}...")


if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError(
        "SUPABASE_URL e SUPABASE_SERVICE_KEY precisam estar definidos no .env\n"
        f"Procurei o .env em: {env_path or 'nenhum lugar'}"
    )


supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)