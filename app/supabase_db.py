"""Acesso ao Supabase com as credenciais do .env da raiz (criação preguiçosa do cliente)."""
import os
from pathlib import Path

from dotenv import load_dotenv

_cliente = None


def _carregar_env():
    atual = Path(__file__).resolve().parent
    for _ in range(3):
        candidato = atual / '.env'
        if candidato.exists():
            load_dotenv(candidato)
            return
        atual = atual.parent
    load_dotenv()


def _url():
    url = (os.getenv('SUPABASE_URL') or '').strip().rstrip('/')
    for sufixo in ('/rest/v1', '/rest', '/v1'):
        if url.endswith(sufixo):
            url = url[: -len(sufixo)].rstrip('/')
    return url


def credenciais_configuradas() -> bool:
    _carregar_env()
    return bool(_url() and (os.getenv('SUPABASE_SERVICE_KEY') or '').strip())


def novo_cliente():
    """Cliente independente. Usado para validar senha de um usuário sem tocar no cliente principal."""
    if not credenciais_configuradas():
        raise RuntimeError('SUPABASE_URL e SUPABASE_SERVICE_KEY precisam estar no .env')
    from supabase import create_client
    return create_client(_url(), os.getenv('SUPABASE_SERVICE_KEY').strip())


def get_supabase():
    """Cliente único do processo. A service key fica só no servidor, nunca em templates."""
    global _cliente
    if _cliente is None:
        _cliente = novo_cliente()
    return _cliente
