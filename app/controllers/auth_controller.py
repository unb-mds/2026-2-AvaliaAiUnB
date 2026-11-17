"""Login com Google: delega ao Supabase Auth (fluxo PKCE) e devolve a sessão para as rotas."""
from app.repositorio import repositorios


def iniciar_login_google(redirect_to):
    """(url do Supabase para onde o navegador vai, verificador PKCE a guardar na sessão)."""
    return repositorios().usuarios.url_login_google(redirect_to)


def concluir_login_google(codigo, verificador):
    """Sessão ({'access_token', 'refresh_token'}) se o retorno do Google for válido, senão None."""
    if not codigo or not verificador:
        return None
    return repositorios().usuarios.entrar_com_google(codigo, verificador)
