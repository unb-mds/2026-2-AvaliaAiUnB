"""Acesso ao Supabase com as credenciais do .env da raiz (criação preguiçosa do cliente)."""
import os
from pathlib import Path

from dotenv import load_dotenv

_cliente = None
_cliente_publico = None


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


def _chave_servico():
    return (os.getenv('SUPABASE_SERVICE_KEY') or '').strip()


def _chave_publica():
    return (
        os.getenv('SUPABASE_ANON_KEY')
        or os.getenv('SUPABASE_PUBLIC_KEY')
        or os.getenv('SUPABASE_KEY')
        or ''
    ).strip()


def credenciais_configuradas() -> bool:
    _carregar_env()
    return bool(_url() and _chave_servico())


def credenciais_publicas_configuradas() -> bool:
    _carregar_env()
    return bool(_url() and (_chave_publica() or _chave_servico()))


def novo_cliente():
    """Cliente independente com service key (operações administrativas de Auth)."""
    if not credenciais_configuradas():
        raise RuntimeError('SUPABASE_URL e SUPABASE_SERVICE_KEY precisam estar no .env')
    from supabase import create_client
    return create_client(_url(), _chave_servico())


def novo_cliente_publico():
    """Cliente independente com a chave pública (sujeito às políticas de RLS)."""
    if not credenciais_publicas_configuradas():
        raise RuntimeError('SUPABASE_URL e SUPABASE_ANON_KEY precisam estar no .env')
    from supabase import create_client
    chave = _chave_publica() or _chave_servico()
    return create_client(_url(), chave)


def get_supabase():
    """Cliente único do processo com service key. Restrito ao servidor."""
    global _cliente
    if _cliente is None:
        _cliente = novo_cliente()
    return _cliente


def get_supabase_publico():
    """Cliente único do processo com chave pública (respeita RLS para leitura pública)."""
    global _cliente_publico
    if _cliente_publico is None:
        _cliente_publico = novo_cliente_publico()
    return _cliente_publico