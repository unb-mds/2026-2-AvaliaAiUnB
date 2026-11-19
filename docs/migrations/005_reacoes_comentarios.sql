-- Reações de comentários pelo backend Flask. Não altera os comentários existentes.
BEGIN;
CREATE TABLE public.reacoes_comentarios (
    comentario_id BIGINT NOT NULL REFERENCES public.comentarios(id) ON DELETE CASCADE,
    usuario_id UUID NOT NULL REFERENCES public.perfis(id) ON DELETE CASCADE,
    reacao TEXT NOT NULL CHECK (reacao IN ('curtir', 'descurtir')),
    PRIMARY KEY (comentario_id, usuario_id)
);
CREATE INDEX reacoes_comentarios_usuario_idx ON public.reacoes_comentarios(usuario_id);
ALTER TABLE public.reacoes_comentarios ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.reacoes_comentarios FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.reacoes_comentarios TO service_role;

-- Agregação no banco para não truncar contagens no limite de linhas da API.
CREATE FUNCTION public.contar_reacoes_comentarios(p_ids BIGINT[], p_usuario_id UUID)
RETURNS TABLE (comentario_id BIGINT, curtidas BIGINT, descurtidas BIGINT, minha_reacao TEXT)
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = '' AS $$
    SELECT c.id,
           count(*) FILTER (WHERE r.reacao = 'curtir'),
           count(*) FILTER (WHERE r.reacao = 'descurtir'),
           max(r.reacao) FILTER (WHERE r.usuario_id = p_usuario_id)
    FROM public.comentarios c
    LEFT JOIN public.reacoes_comentarios r ON r.comentario_id = c.id
    WHERE c.id = ANY(p_ids) AND c.ocultado_em IS NULL
    GROUP BY c.id;
$$;
REVOKE ALL ON FUNCTION public.contar_reacoes_comentarios(BIGINT[], UUID) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.contar_reacoes_comentarios(BIGINT[], UUID) TO service_role;

CREATE FUNCTION public.alternar_reacao_comentario(
    p_professor_id BIGINT, p_comentario_id BIGINT, p_usuario_id UUID, p_reacao TEXT
)
RETURNS TEXT LANGUAGE plpgsql SECURITY INVOKER SET search_path = '' AS $$
DECLARE
    autor UUID;
BEGIN
    IF p_reacao IS NULL OR p_reacao NOT IN ('curtir', 'descurtir') THEN
        RAISE EXCEPTION 'Reação inválida.' USING ERRCODE = '23514';
    END IF;
    -- A trava serializa trocas, remoções e exclusão do comentário na mesma transação.
    SELECT usuario_id INTO autor FROM public.comentarios
    WHERE id = p_comentario_id AND professor_id = p_professor_id AND ocultado_em IS NULL
    FOR UPDATE;

    IF NOT FOUND THEN
        RETURN 'indisponivel';
    ELSIF autor = p_usuario_id THEN
        RETURN 'autor';
    END IF;

    DELETE FROM public.reacoes_comentarios
    WHERE comentario_id = p_comentario_id AND usuario_id = p_usuario_id AND reacao = p_reacao;
    IF NOT FOUND THEN
        INSERT INTO public.reacoes_comentarios (comentario_id, usuario_id, reacao)
        VALUES (p_comentario_id, p_usuario_id, p_reacao)
        ON CONFLICT (comentario_id, usuario_id) DO UPDATE SET reacao = EXCLUDED.reacao;
    END IF;
    RETURN 'ok';
END;
$$;

REVOKE ALL ON FUNCTION public.alternar_reacao_comentario(BIGINT, BIGINT, UUID, TEXT)
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.alternar_reacao_comentario(BIGINT, BIGINT, UUID, TEXT)
    TO service_role;

COMMIT;
