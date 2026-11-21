-- Issue #252: avaliar a turma (semestre) cursada.
-- Depende de: 001_initial_schema.sql (avaliacoes, turmas)
-- A 006 é a dos favoritos (#223); as duas são independentes.
--
-- Antes: uma avaliação por usuário, professor e disciplina; o semestre era o da turma
-- mais recente. Agora: uma avaliação por semestre cursado. A pessoa escolhe a turma
-- no formulário e o backend confere que o professor deu a disciplina naquele semestre.
-- As avaliações já gravadas continuam válidas: nenhuma tem par repetido, então todas
-- satisfazem a nova restrição.

BEGIN;

ALTER TABLE avaliacoes
    DROP CONSTRAINT IF EXISTS uq_avaliacoes_usuario_prof_disc;

ALTER TABLE avaliacoes
    DROP CONSTRAINT IF EXISTS uq_avaliacoes_usuario_prof_disc_semestre;

ALTER TABLE avaliacoes
    ADD CONSTRAINT uq_avaliacoes_usuario_prof_disc_semestre
    UNIQUE (usuario_id, professor_id, disciplina_id, ano, periodo);

-- Médias por semestre no perfil (filtro) e no gráfico de evolução
CREATE INDEX IF NOT EXISTS idx_avaliacoes_professor_semestre
    ON avaliacoes (professor_id, ano, periodo);

COMMIT;
