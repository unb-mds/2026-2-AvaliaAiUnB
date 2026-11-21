-- Issue #223: favoritar professores (RF11).
-- Depende de: 001_initial_schema.sql (perfis, professores)
-- Fora do escopo: notificações quando um favorito recebe avaliação.
--
-- A lista é pessoal: cada usuário lê, adiciona e remove só os próprios favoritos.
-- Um professor aparece no máximo uma vez na lista de cada usuário (chave primária composta).

BEGIN;

CREATE TABLE IF NOT EXISTS favoritos (
    usuario_id   UUID   NOT NULL REFERENCES perfis(id)      ON DELETE CASCADE,
    professor_id BIGINT NOT NULL REFERENCES professores(id) ON DELETE CASCADE,
    criado_em    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (usuario_id, professor_id)
);

-- Lista do perfil: favoritos do usuário, mais recentes primeiro
CREATE INDEX IF NOT EXISTS idx_favoritos_usuario_criado
    ON favoritos (usuario_id, criado_em DESC);

-- RLS: nada para anon; authenticated só enxerga e mexe nas próprias linhas.
-- O backend usa service_role e sempre filtra por usuario_id da sessão.
ALTER TABLE favoritos ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON favoritos FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, DELETE ON favoritos TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON favoritos TO service_role;

DROP POLICY IF EXISTS favoritos_select ON favoritos;
CREATE POLICY favoritos_select ON favoritos
    FOR SELECT TO authenticated
    USING (usuario_id = auth.uid());

DROP POLICY IF EXISTS favoritos_insert ON favoritos;
CREATE POLICY favoritos_insert ON favoritos
    FOR INSERT TO authenticated
    WITH CHECK (usuario_id = auth.uid());

DROP POLICY IF EXISTS favoritos_delete ON favoritos;
CREATE POLICY favoritos_delete ON favoritos
    FOR DELETE TO authenticated
    USING (usuario_id = auth.uid());

COMMIT;
