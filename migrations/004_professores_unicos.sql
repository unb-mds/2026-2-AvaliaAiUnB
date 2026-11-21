-- Issue #235: professores duplicados (mesmo docente em várias unidades)
-- Depende de: 001_initial_schema.sql e 002_comentarios.sql
--
-- Causa: a constraint UNIQUE (nome, departamento) criava uma linha por unidade
-- em que o docente dá aula (ex.: o mesmo nome no Campus Ceilândia e no IB).
-- Esta migração:
--   1. agrupa os professores pelo nome normalizado (caixa e espaços);
--   2. escolhe o registro canônico de cada grupo, cujo departamento é mantido:
--      prefere uma unidade acadêmica a um decanato (ex.: DPG, que só agrupa a
--      pós-graduação), depois mais avaliações, mais comentários, mais turmas e,
--      por fim, o menor id;
--   3. move turmas, avaliações e comentários dos duplicados para o canônico,
--      apagando antes o que violaria as chaves únicas (fica a turma do
--      canônico e a avaliação mais recente do mesmo usuário/disciplina);
--   4. apaga os duplicados e troca a constraint por UNIQUE (nome).
--
-- Disciplinas não precisam de mesclagem: o código já é único e disciplinas
-- com o mesmo nome e códigos diferentes são ofertas distintas de cada unidade.
--
-- Rodar no SQL Editor do Supabase. Tudo roda numa transação: se qualquer
-- verificação falhar, nada é alterado. Rodar de novo não tem efeito.

BEGIN;

-- 0. Segurança: aborta se outra tabela (além das conhecidas) referenciar professores.
DO $$
DECLARE
    desconhecidas TEXT;
BEGIN
    SELECT string_agg(DISTINCT conrelid::regclass::text, ', ')
      INTO desconhecidas
      FROM pg_constraint
     WHERE contype = 'f'
       AND confrelid = 'public.professores'::regclass
       AND conrelid::regclass::text NOT IN ('turmas', 'avaliacoes', 'comentarios');
    IF desconhecidas IS NOT NULL THEN
        RAISE EXCEPTION 'Tabelas não previstas referenciam professores: %', desconhecidas;
    END IF;
END $$;

-- 1. Mapa duplicado -> canônico
CREATE TEMP TABLE mapa_professores ON COMMIT DROP AS
WITH estatisticas AS (
    SELECT p.id,
           upper(regexp_replace(btrim(p.nome), '\s+', ' ', 'g')) AS chave,
           (p.departamento ILIKE 'DECANATO%') AS eh_decanato,
           (SELECT count(*) FROM avaliacoes a  WHERE a.professor_id = p.id) AS n_avaliacoes,
           (SELECT count(*) FROM comentarios c WHERE c.professor_id = p.id) AS n_comentarios,
           (SELECT count(*) FROM turmas t      WHERE t.professor_id = p.id) AS n_turmas
      FROM professores p
), ranqueados AS (
    SELECT id,
           first_value(id) OVER (
               PARTITION BY chave
               ORDER BY eh_decanato, n_avaliacoes DESC, n_comentarios DESC, n_turmas DESC, id
           ) AS canonico
      FROM estatisticas
)
SELECT id AS duplicado, canonico
  FROM ranqueados
 WHERE id <> canonico;

-- 2. Turmas: apaga as que colidiriam no UNIQUE e move o resto
WITH alvo AS (
    SELECT t.id,
           row_number() OVER (
               PARTITION BY COALESCE(m.canonico, t.professor_id), t.disciplina_id, t.ano, t.periodo
               ORDER BY (m.duplicado IS NULL) DESC, t.id
           ) AS ordem
      FROM turmas t
      LEFT JOIN mapa_professores m ON m.duplicado = t.professor_id
)
DELETE FROM turmas WHERE id IN (SELECT id FROM alvo WHERE ordem > 1);

UPDATE turmas t
   SET professor_id = m.canonico
  FROM mapa_professores m
 WHERE t.professor_id = m.duplicado;

-- 3. Avaliações: um usuário só pode ter uma por professor/disciplina; fica a mais recente
WITH alvo AS (
    SELECT a.id,
           row_number() OVER (
               PARTITION BY a.usuario_id, COALESCE(m.canonico, a.professor_id), a.disciplina_id
               ORDER BY a.criado_em DESC NULLS LAST, a.id DESC
           ) AS ordem
      FROM avaliacoes a
      LEFT JOIN mapa_professores m ON m.duplicado = a.professor_id
)
DELETE FROM avaliacoes WHERE id IN (SELECT id FROM alvo WHERE ordem > 1);

UPDATE avaliacoes a
   SET professor_id = m.canonico
  FROM mapa_professores m
 WHERE a.professor_id = m.duplicado;

-- 4. Comentários: sem chave única, só move
UPDATE comentarios c
   SET professor_id = m.canonico
  FROM mapa_professores m
 WHERE c.professor_id = m.duplicado;

-- 5. Apaga os duplicados (já sem nenhum vínculo)
DELETE FROM professores p
 USING mapa_professores m
 WHERE p.id = m.duplicado;

-- 6. Causa raiz: um professor por nome, independentemente da unidade
ALTER TABLE professores DROP CONSTRAINT IF EXISTS uq_professores_nome_departamento;
ALTER TABLE professores DROP CONSTRAINT IF EXISTS uq_professores_nome;
ALTER TABLE professores ADD CONSTRAINT uq_professores_nome UNIQUE (nome);

-- 7. Conferência final (aborta a transação se sobrou duplicata)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM professores
         GROUP BY upper(regexp_replace(btrim(nome), '\s+', ' ', 'g'))
        HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION 'Ainda há professores duplicados após a mesclagem.';
    END IF;
END $$;

COMMIT;
