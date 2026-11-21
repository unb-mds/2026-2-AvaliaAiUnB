# Backend

O AvaliaUnb usa Python e Flask para renderizar páginas Jinja2 e processar
logins, sessões, consultas, avaliações e comentários. A persistência usa PostgreSQL no
Supabase; as contas são gerenciadas pelo Supabase Auth, com entrada apenas pela
conta Google.

## Inicialização e estrutura

`run.py` chama `create_app`, definida em `app/__init__.py`. A fábrica carrega o
`.env` da raiz, configura a aplicação, exige `SECRET_KEY`, configura a proteção CSRF, monta os repositórios, registra a renovação de
sessão e os três Blueprints. A função `configurar_seguranca` também define
headers, cookies e limites de requisições; a revisão da inicialização do
CSRF faz parte da [#127](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/127). O Gunicorn usa a mesma aplicação pelo alvo `run:app`.

```text
Requisição HTTP
    → app/routes/ (Blueprints)
    → app/controllers/ e app/validacoes.py
    → app/repositorio.py
    → app/supabase_db.py
    → Supabase (PostgreSQL e Auth)
```

| Arquivo ou diretório | Responsabilidade |
|---|---|
| `app/__init__.py` | Fábrica `create_app(config=None)` e registro das dependências |
| `app/routes/main_routes.py` | Página inicial (`main_bp`) |
| `app/routes/auth_routes.py` | Login com Google, logout e perfil do usuário (`auth_bp`) |
| `app/routes/professor_routes.py` | Busca, perfil do professor, comparação, ranking, avaliações e comentários (`professor_bp`) |
| `app/controllers/auth_controller.py` | Início e conclusão do login com Google |
| `app/controllers/session_controller.py` | Identificação do usuário, cookies, renovação, logout e `login_required` |
| `app/controllers/professor_controller.py` | Catálogo, seleção de professores e disciplinas, indicadores e operações de avaliação e de comentário |
| `app/validacoes.py` | Critérios e validação das notas e do texto dos comentários |
| `app/seguranca.py` | Configuração de segurança, headers e limites de requisições na main, incluindo o de comentários |
| `app/utils.py` | Normalização de texto para buscas |
| `app/repositorio.py` | Repositórios de usuários, professores, avaliações e comentários |
| `app/supabase_db.py` | Leitura das credenciais e criação dos clientes Supabase |
| `app/models.py` | Estruturas de dados do domínio; não é um ORM |
| `app/templates/` e `app/static/` | Páginas Jinja2 e recursos estáticos |
| `scraper/` | Coleta e persistência do catálogo do SIGAA, executadas separadamente |

Os caminhos da tabela são relativos à raiz do repositório.

## Rotas

| Método | Caminho | Acesso | Comportamento |
|---|---|---|---|
| GET | `/` | Público | Página inicial |
| GET | `/login` | Público | Tela com o botão "Entrar com Google" |
| GET | `/cadastro` | Público | Redireciona para `/login`; a conta é criada no primeiro login |
| GET | `/login/google` | Público | Gera o verificador PKCE e redireciona ao Supabase Auth |
| GET | `/login/google/retorno` | Público | Troca o código por sessão, cria o perfil no primeiro acesso e grava os cookies |
| POST | `/logout` | Autenticado | Revoga a sessão e remove os cookies |
| GET | `/perfil` | Autenticado | Dados, favoritos e avaliações do próprio usuário |
| POST | `/professores/<id>/favorito` | Autenticado + CSRF | Favorita (`acao=adicionar`) ou desfavorita (`acao=remover`) o professor |
| GET | `/professores` | Público | Catálogo filtrado por `nome`, `disciplina`, `departamento` e pela busca unificada `q` |
| GET | `/busca/sugestoes` | Público | Autocompletar (JSON): professores, disciplinas e departamentos para `q`; `limite` (padrão 8, máximo 20) e `contexto` (`consulta` ou `comparacao`); limite de 120 por minuto |
| GET | `/professores/<int:professor_id>` | Público | Perfil, médias e comentários; `disciplina_id` seleciona a disciplina das médias, `semestre` (ex.: `2026-2`) restringe as médias a uma turma, `evolucao_criterio` escolhe o critério do gráfico e `comentarios_disciplina` filtra os comentários |
| GET | `/comparar` | Público | Compara professores de uma disciplina (`disciplina_id`, `professor`) ou `professor_1` e `professor_2`; `busca` lista resultados da busca unificada |
| GET | `/ranking` | Público | Classificação por média, com mínimo de cinco avaliações válidas |
| GET, POST | `/avaliar/<int:professor_id>` | Autenticado | Formulário e registro de notas para uma disciplina vinculada; `semestre` (ex.: `2026-2`) é a turma cursada, uma avaliação por semestre (sem o campo, vale a turma mais recente) |
| GET, POST | `/avaliacoes/<int:avaliacao_id>/editar` | Autor autenticado | Formulário e atualização das próprias notas |
| POST | `/avaliacoes/<int:avaliacao_id>/excluir` | Autor autenticado | Exclusão da própria avaliação |
| POST | `/professores/<int:professor_id>/comentarios` | Autenticado | Publica um comentário em uma disciplina vinculada ao professor; limite de 10 por hora por usuário |
| GET, POST | `/comentarios/<int:comentario_id>/editar` | Autor autenticado | Formulário e atualização do texto e da disciplina do próprio comentário |
| GET, POST | `/comentarios/<int:comentario_id>/excluir` | Autor autenticado | GET mostra a confirmação; POST exclui o próprio comentário |

O perfil e o formulário de avaliação recebem também `next` para manter a URL
de retorno da busca. A validação desse parâmetro está em `app/seguranca.py`;
o bloqueio de barra invertida foi integrado no
[PR #133](https://github.com/unb-mds/2026-2-AvaliaUnB/pull/133).

Os formulários e as páginas de comentário preservam `next` e
`comentarios_disciplina` (e, ao publicar, a disciplina das médias, enviada no
campo `disciplina_medias`) para voltar ao mesmo ponto do perfil. Os dois
parâmetros são validados antes do redirecionamento 303 para o perfil com
`#comentarios`: `next` pela mesma regra de URL segura e
`comentarios_disciplina` pela lista de disciplinas do professor.

As telas são renderizadas no servidor. Algumas rotas também retornam JSON
conforme o cabeçalho `Accept`; o logout reconhece ainda o campo
`formato=html`. Não existe uma API REST separada com os mesmos contratos para
todas as páginas. Todos os POSTs passam pela proteção CSRF, inclusive quando
a resposta solicitada é JSON.

## Login com Google e sessão

A única forma de entrar é a conta Google, pelo provedor do Supabase Auth com
fluxo PKCE. `/login/google` gera um verificador, guarda-o na sessão assinada
do Flask e redireciona ao Supabase, que leva ao Google. O retorno em
`/login/google/retorno` só é aceito com o verificador do mesmo navegador, o
que impede login CSRF. A troca do código é feita em um cliente Supabase
independente, sem alterar a sessão do cliente compartilhado do servidor.

No primeiro acesso, `UsuarioRepository` cria o registro em `perfis` com o nome
vindo do Google e um nome de usuário único derivado do e-mail (minúsculas,
letras, números, ponto ou sublinhado; um sufixo numérico resolve conflitos),
e copia `nome` e `username` para o `user_metadata`. Contas antigas, criadas
pelo cadastro com senha, são vinculadas pelo Supabase quando o e-mail Google
é o mesmo: o id, o perfil e as avaliações continuam os mesmos. Não existem
mais cadastro, login ou recuperação por senha.

Os tokens são guardados nos cookies `avaliaai_session` e `avaliaai_refresh`,
com `HttpOnly`, `SameSite=Lax` e duração de doze horas. Na `main`, `Secure`
depende da configuração `COOKIE_SECURE`, habilitada fora do debug.
`obter_usuario_atual` valida o token no Supabase, tenta renovar a sessão quando
necessário e guarda o usuário em `flask.g` durante a requisição. O hook
`after_request` envia os cookies renovados. O logout solicita a revogação ao
Supabase e remove os cookies. A falha de revogação com token de acesso expirado
foi registrada na auditoria e é tratada na
[issue #126](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/126).

`login_required` redireciona navegadores sem sessão para `/login`; clientes que
aceitam apenas JSON recebem HTTP 401. Tentativas de carregar, editar ou excluir
avaliações de outro usuário recebem HTTP 404, pois a consulta inclui o autor.
O mesmo vale para comentários: editar ou excluir o de outra pessoa, ou um que
não exista, responde HTTP 404 (nunca 403).

## Repositórios e consultas

Os repositórios ficam em `current_app.extensions['repositorios']` e são obtidos
por `repositorios()` dentro do contexto Flask.

- `UsuarioRepository`: contas no Supabase Auth, perfis e operações de sessão.
- `ProfessorRepository`: professores, disciplinas pela view
  `vw_professor_disciplina`, catálogo, departamentos e ranking.
- `AvaliacaoRepository`: registro, consulta, médias, edição e exclusão de notas.
- `ComentarioRepository`: listagem, busca, criação, edição e exclusão de
  comentários (veja a seção [Comentários](#comentarios)).
- `DenunciaRepository`: denúncias privadas de comentários.
- `FavoritoRepository`: lista pessoal de professores favoritos (adicionar,
  remover, consultar e listar por usuário).

`supabase_db.py` fornece um cliente compartilhado por processo e a função
`novo_cliente()` para operações de autenticação que precisam de um cliente
independente. A aplicação atual usa `SUPABASE_URL` e `SUPABASE_SERVICE_KEY`
no servidor. A
[auditoria concluída na #111](AUDITORIA_SEGURANCA.md)
identificou a necessidade de reduzir o uso da service key; a migração para
chave pública com RLS é acompanhada nas issues #124, #129 e #130.

Consultas extensas usam paginação em lotes de mil registros. O catálogo é
armazenado em memória por processo por até cinco minutos; registrar, editar ou
excluir uma avaliação invalida o cache desse processo. As médias e o ranking
consultam as avaliações a cada acesso, sem usar esse cache.

A busca normaliza acentos, maiúsculas e espaços extras. Nome e disciplina usam
correspondência parcial; departamento exige igualdade após normalização. A
disciplina pode ser buscada por nome ou código. A lista é ordenada pelo total
de avaliações, depois por nome e identificador.

Para os cartões da Consulta, `AvaliacaoRepository.dificuldade_por_professor_disciplina`
devolve, numa única consulta agrupada para os professores da página, a
dificuldade média (uma casa decimal) e a quantidade de avaliações por professor
e disciplina, com a mesma regra de `_resumir_notas` usada no perfil. No
`professor_controller`, `paginar_catalogo` calcula a paginação da lista (100
professores por página), `dificuldades_da_pagina` monta os valores e os textos
exibidos e `organizar_disciplinas` ordena as disciplinas de cada cartão (mais
avaliações primeiro, depois as sem avaliações, desempate por nome) e separa as
que ficam em "Ver mais N disciplinas" (com mais de 5, 4 visíveis e as demais
extras). Nenhuma disciplina é descartada.

A busca unificada (`q`) casa com o nome do professor, o departamento ou o nome
ou código de alguma disciplina. `ProfessorRepository.sugerir` usa o mesmo
catálogo em cache para o autocompletar: exige ao menos dois caracteres
normalizados e ordena quem começa com o termo, depois quem tem uma palavra que
começa com ele e por fim quem só o contém; entre professores, o mais avaliado
vem antes. Cada sugestão traz `tipo`, `tipo_rotulo`, `texto`, `detalhe` e a
`url` de destino no contexto pedido.

## Avaliações e médias

Cada avaliação contém didática, clareza, organização, disponibilidade e
dificuldade, com notas inteiras de um a cinco. A aplicação verifica o vínculo
entre professor e disciplina e permite uma avaliação por usuário para esse par.
Ano e período são obtidos do vínculo de turma mais recente disponível para o par.

No perfil do professor, as médias correspondem à disciplina selecionada. Na
comparação, são agregadas todas as disciplinas e períodos para cada professor.
Uma linha só participa das médias quando os cinco critérios têm notas válidas;
sem avaliações válidas, as médias são `None` e a quantidade é zero.

O ranking exige cinco avaliações válidas e calcula a média de didática,
clareza, organização e disponibilidade. Dificuldade não entra na média geral.
Os desempates usam quantidade de avaliações, nome normalizado e identificador.

O esquema e as políticas RLS versionadas estão em
`docs/migrations/001_initial_schema.sql`; a tabela de comentários está em
`docs/migrations/002_comentarios.sql`. Sua aplicação ao ambiente real
deve ser conferida no Supabase.
O
[modelo de dados e a proposta de comentários](Modelo%20de%20Dados.md)
foram publicados na [issue #109](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/109).
Este guia descreve as operações do backend, incluindo os comentários abaixo; as
regras futuras de reações, denúncia e moderação serão consolidadas e revisadas
na [issue #116](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/116).

## Comentários

O perfil do professor lista, e usuários autenticados publicam, editam e excluem,
comentários sobre a experiência com um professor em uma disciplina que ele
ministra. As regras de negócio estão em [Comentários](COMENTARIOS.md). Reações,
denúncia, moderação, ocultação e filtro automático ainda não têm backend.

**Repositório.** `ComentarioRepository` (em `app/repositorio.py`) acessa a
tabela `comentarios`. Como o backend usa a service key, que ignora RLS, a
autoria e o vínculo entre professor e disciplina são conferidos no servidor:

- `listar_por_professor(professor_id, disciplina_id=None, usuario_atual_id=None)`
  devolve `(comentarios, ha_mais)`. Filtra `ocultado_em IS NULL` e a disciplina,
  ordena por `criado_em` e `id` do mais recente para o mais antigo e busca
  `LIMITE_COMENTARIOS + 1` (50 + 1) linhas só para saber se há mais. Os nomes de
  usuário vêm de `perfis` (`id` e `username`); o e-mail nunca é selecionado.
  Cada comentário tem apenas `id`, `texto`, `username`, `disciplina_nome`,
  `disciplina_codigo`, `criado_em`, `editado` e `e_meu`, este calculado no
  servidor. O `usuario_id` não sai do repositório.
- `buscar_do_usuario(comentario_id, usuario_id)` devolve o comentário se for
  do usuário, ou `None`.
- `criar(usuario_id, professor_id, disciplina_id, texto)` e
  `atualizar(comentario_id, usuario_id, disciplina_id, texto)` validam o texto e
  conferem, pela view `vw_professor_disciplina`, que a disciplina pertence ao
  professor; caso contrário levantam `ValueError`. O `usuario_id` vem sempre do
  argumento (a sessão), nunca do formulário.
- `atualizar` e `excluir` filtram por `id` **e** `usuario_id`; sem linha
  afetada devolvem `False` e a rota responde 404. A atualização muda só `texto`
  e `disciplina_id`: professor, autor e datas de criação não mudam.

**Validação.** `validar_comentario` (em `app/validacoes.py`) normaliza `\r\n`
para `\n`, remove os espaços das extremidades e exige de 2 a 1.000 caracteres.
O texto é simples: HTML e Markdown não são interpretados e o template escapa a
saída. O banco também verifica o tamanho.

**Rotas.** Na publicação, as checagens seguem a ordem: login, professor
existente (404), `disciplina_id` convertido com `int()` e presente nas
disciplinas do professor, e texto válido. A rota não usa `carregar_perfil`,
porque ele leria o `disciplina_id` do formulário como disciplina das médias. Em
erro, responde 400 renderizando o perfil com o texto e a disciplina escolhidos
preservados; em sucesso, redireciona (303) ao perfil. Editar e excluir carregam o
comentário pelo `buscar_do_usuario`, então o de outra pessoa ou inexistente
responde 404. A edição ignora `professor_id`, `usuario_id` e outros campos
enviados. A exclusão tem uma página de confirmação (GET) e, no POST, responde
JSON se o `Accept` pedir, como a exclusão de avaliações. O filtro
`comentarios_disciplina` do perfil não reutiliza `disciplina_id`: vazio ou
inválido volta a "todas as disciplinas", sem 404.

**Limite de envio.** `limitar_comentario` (em `app/seguranca.py`) permite 10
comentários por hora por usuário logado (por IP só para visitante), com escopo
próprio: esgotar o limite de comentários não afeta o das avaliações, e o
contrário também. Vale apenas para a publicação; editar e excluir não têm limite.
Como no limite de avaliações, toda tentativa de POST conta, inclusive as
recusadas por validação.

**Falhas e efeitos.** Se a consulta dos comentários falhar, o erro é registrado
com `current_app.logger.exception` e a seção mostra "Não foi possível carregar os
comentários agora.", sem derrubar o resto do perfil. Comentários não alteram
notas, médias, comparação nem ranking, e não usam o cache do catálogo.

## Scraper

O scraper não é executado pelas rotas Flask. `scraper_sigaa.py` coordena a
coleta; `cli_sigaa.py` interpreta argumentos; os módulos de texto, unidades e
turmas tratam os dados; `resumo_sigaa.py` organiza os resultados; e
`persistencia_sigaa.py` grava usando o cliente de `scraper/supabase_client.py`.

Os upserts usam nome e departamento para professores, código para disciplinas
e professor, disciplina, ano e período para turmas. O departamento corresponde
à unidade selecionada na coleta. O modo `--dry-run` exibe os dados sem ler o
`.env` nem gravar no Supabase.

Dependências, parâmetros e diagnóstico estão no [guia do scraper](COMO_USAR_SCRAPER.md).

## Validação e contribuição

Execute na raiz, com as dependências do app instaladas:

```bash
python -m unittest discover -s tests -t .
```

Os testes usam `tests/fake_supabase.py`. A fábrica aceita `SUPABASE_CLIENT`
pela configuração para injetar o cliente falso, junto de uma `SECRET_KEY`
exclusiva de teste. A suíte não precisa de credenciais reais, Chrome ou acesso
ao Supabase.

Ao alterar uma funcionalidade, mantenha a rota responsável pela resposta HTTP,
as regras no controller ou nos validadores e a persistência no repositório.
Atualize os testes do comportamento afetado e a documentação correspondente.

Clientes que enviam formulários diretamente precisam carregar a página por GET,
preservar o cookie de sessão Flask e enviar o token no campo `csrf_token` ou no
cabeçalho `X-CSRFToken`. POSTs sem token, com token inválido ou expirado recebem
HTTP 400 antes da operação. As regras de notas, busca e indicadores estão no
[guia de funcionalidades](FUNCIONALIDADES.md).

Relacionado: [arquitetura](ARQUITETURA.md), [modelo de dados](Modelo%20de%20Dados.md),
[cibersegurança](CIBERSEGURANCA.md) e [critérios de contribuição](PROCESSO_CONTRIBUICAO.md).
