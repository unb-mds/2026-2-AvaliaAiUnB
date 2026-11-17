BEGIN;

CREATE TABLE public.emails_verificados (
    usuario_id UUID PRIMARY KEY REFERENCES public.perfis(id) ON DELETE CASCADE,
    endereco_sha256 TEXT NOT NULL CHECK (endereco_sha256 ~ '^[0-9a-f]{64}$')
);

ALTER TABLE public.emails_verificados ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.emails_verificados FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON public.emails_verificados TO service_role;

COMMIT;
