// Validação descartável: node tests/validar_reacoes_sql.mjs <caminho-do-pglite/dist/index.js>
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
const { PGlite } = await import(pathToFileURL(process.argv[2]).href);
const banco = new PGlite();
const autor = '00000000-0000-0000-0000-000000000001';
const leitor = '00000000-0000-0000-0000-000000000002';
try {
    await banco.exec(`
        CREATE ROLE anon; CREATE ROLE authenticated; CREATE ROLE service_role BYPASSRLS;
        CREATE TABLE public.perfis (id UUID PRIMARY KEY);
        CREATE TABLE public.comentarios (id BIGINT PRIMARY KEY, professor_id BIGINT NOT NULL,
                                        usuario_id UUID REFERENCES public.perfis(id), ocultado_em TIMESTAMPTZ);
        GRANT SELECT,UPDATE ON public.comentarios TO service_role;
        INSERT INTO public.perfis VALUES ('${autor}'), ('${leitor}');
        INSERT INTO public.comentarios VALUES (1,245,'${autor}',NULL), (2,245,'${autor}',now());
    `);
    const permissoes = () => banco.query("SELECT grantee,privilege_type FROM information_schema.role_table_grants WHERE table_name='comentarios' ORDER BY grantee,privilege_type");
    const antes = await permissoes();
    await banco.exec(await readFile(new URL('../docs/migrations/005_reacoes_comentarios.sql', import.meta.url), 'utf8'));
    assert.deepEqual((await permissoes()).rows, antes.rows, 'Não muda as permissões de comentários existentes.');
    const alternar = async (uid, reacao, cid=1, pid=245) =>
        (await banco.query('select public.alternar_reacao_comentario($1,$2,$3,$4) as resultado', [pid,cid,uid,reacao])).rows[0].resultado;
    const contar = async () => (await banco.query('select * from public.contar_reacoes_comentarios($1,$2)', [[1,2],leitor])).rows;
    await banco.exec('SET ROLE service_role');
    assert.equal(await alternar(autor,'curtir'), 'autor');
    assert.equal(await alternar(leitor,'curtir',2), 'indisponivel');
    assert.equal(await alternar(leitor,'curtir',1,999), 'indisponivel');
    assert.equal(await alternar(leitor,'curtir'), 'ok');
    assert.deepEqual(await contar(), [{comentario_id:1,curtidas:1,descurtidas:0,minha_reacao:'curtir'}]);
    assert.equal(await alternar(leitor,'descurtir'), 'ok');
    assert.deepEqual(await contar(), [{comentario_id:1,curtidas:0,descurtidas:1,minha_reacao:'descurtir'}]);
    await alternar(leitor,'descurtir');
    assert.deepEqual(await contar(), [{comentario_id:1,curtidas:0,descurtidas:0,minha_reacao:null}]);
    await assert.rejects(alternar(leitor,'invalida'), /Reação inválida/);
    await banco.exec('RESET ROLE');
    // Contagens corretas mesmo acima do limite padrão de mil linhas da Data API.
    await banco.exec(`INSERT INTO public.perfis SELECT md5(i::text)::uuid FROM generate_series(1,1100) i;
                      INSERT INTO public.reacoes_comentarios SELECT 1,md5(i::text)::uuid,'curtir' FROM generate_series(1,1100) i;`);
    assert.equal((await contar())[0].curtidas, 1100);
    await assert.rejects(banco.exec(`INSERT INTO public.reacoes_comentarios VALUES (1,md5('1')::uuid,'descurtir')`), /duplicate key/);
    for (const papel of ['anon','authenticated']) {
        await banco.exec('SET ROLE '+papel);
        await assert.rejects(banco.query('select * from public.reacoes_comentarios'), /permission denied/);
        await assert.rejects(contar(), /permission denied/);
        await assert.rejects(alternar(leitor,'curtir'), /permission denied/);
        await banco.exec('RESET ROLE');
    }
    const rls = await banco.query("select relrowsecurity from pg_class where oid='public.reacoes_comentarios'::regclass");
    assert.equal(rls.rows[0].relrowsecurity,true);
    await banco.exec('DELETE FROM public.comentarios WHERE id=1');
    assert.equal((await banco.query('select count(*)::integer as quantidade from public.reacoes_comentarios')).rows[0].quantidade,0);
    console.log('SQL aprovado: alternância, autoria, ocultação, contagem >1000, unicidade, RLS, permissões e cascata.');
} finally { await banco.close(); }
