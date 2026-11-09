# Cibersegurança

Esta página resume os mecanismos existentes e o plano de correção da
[auditoria de segurança](AUDITORIA_SEGURANCA.md), realizada em 02/11/2026 na
[issue #111](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/111).
O relatório detalhado é a referência para evidências, método e limites da revisão.

## Mecanismos implementados

| Área | Comportamento atual | Onde consultar no código |
|---|---|---|
| Contas e senhas | Criação e autenticação pelo Supabase Auth; o login usa nome de usuário e senha | `UsuarioRepository`, em `app/repositorio.py` |
| Segredos | Configuração por ambiente ou `.env`, fora do Git; service key usada no servidor | `app/supabase_db.py`, `.env.example` |
| Sessão | Cookies `HttpOnly`, `SameSite=Lax` e `Secure` fora do debug; renovação pelo Supabase | `app/controllers/session_controller.py`, `app/seguranca.py` |
| Formulários | Proteção CSRF; token inválido ou ausente resulta em HTTP 400 | `app/__init__.py`, `app/seguranca.py`, templates |
| Autorização | Login exigido nas rotas protegidas; edição e exclusão filtradas pelo autor | Controllers, rotas e repositório de avaliações |
| Headers | CSP, proteção contra enquadramento, tipo de conteúdo e política de referência; HSTS em HTTPS fora do debug | `app/seguranca.py` |
| Limites | Limitação de requisições de login, cadastro e avaliação | `app/seguranca.py` |
| Qualidade | Testes automatizados, pip-audit e Bandit no GitHub Actions | [Pipeline](pipeline.md) |

`SECRET_KEY` é obrigatória na fábrica da aplicação. A configuração de segurança
também verifica chaves fracas em produção. O debug fica desligado por padrão.
Os tokens de autenticação ficam nos cookies e a service key não deve ser
incluída em templates, respostas ou recursos estáticos.

## Resultado da auditoria

O relatório registrou um achado de prioridade alta, três de prioridade média
e oito de prioridade baixa, sem achados críticos. Na data da auditoria,
pip-audit não identificou vulnerabilidades conhecidas nos dois arquivos de
dependências, e Bandit não apontou severidade média ou alta.

Esses resultados correspondem à revisão de 02/11/2026. O relatório informa que
não foi realizado teste de invasão e que alterações posteriores, incluindo a
navegação de retorno, precisam de revisão própria.

## Banco e RLS

Na data da auditoria, as cinco tabelas do banco consultado tinham RLS ativo
sem políticas. O [modelo de dados](Modelo%20de%20Dados.md) detalha essa revisão. A aplicação
usa a service key, que ignora RLS; a autorização do caminho atual depende do
backend. A view `vw_professor_disciplina` expõe dados públicos de professores,
disciplinas e turmas, com as permissões descritas no modelo.

O [PR #139](https://github.com/unb-mds/2026-2-AvaliaAiUnB/pull/139) incluiu RLS e
políticas no esquema inicial. O SQL versionado contém leitura pública para
catálogo, perfis e avaliações e regras de escrita vinculadas ao usuário em
perfis e avaliações. A adoção da chave pública pela aplicação é tratada em
etapas separadas.

## Correções acompanhadas

Situação consultada em **09/11/2026**.

| Issue | Prioridade na auditoria | Entrega esperada |
|---|---|---|
| [#123](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/123) | Alta | RLS e políticas versionados no esquema inicial pelo PR #139 |
| [#124](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/124) | Média | Cliente de chave pública e leitura pública com RLS |
| [#129](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/129) | Desdobramento da #124 | Avaliações com sessão do usuário e autorização também no banco |
| [#130](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/130) | Desdobramento da #124 | Perfil do usuário com chave pública e RLS |
| [#125](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/125) | Média | Confirmação do e-mail antes de ativar a conta |
| [#126](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/126) | Média | Revogação da sessão no logout com token de acesso expirado |
| [#127](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/127) | Baixa | Ajustes de CSRF, limites, mensagens, consultas, validações, logs e testes |

Concluir a auditoria significa ter o relatório e o plano de correção. Cada
correção deve atualizar o comportamento documentado quando for entregue.
Não é necessário esperar essas implementações para publicar o diagnóstico.

## Comentários e moderação

A proposta de comentários, denúncia, permissões de moderação e privacidade está
em [Comentários](COMENTARIOS.md). As regras dependem de revisão do grupo.
O esquema atual não implementa denúncia nem um papel de moderador; esses fluxos
precisam de projeto e implementação próprios após a especificação.
