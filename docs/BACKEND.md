# Backend

O AvaliaUnb usa Python e Flask para renderizar páginas Jinja2 e processar
logins, sessões, consultas e avaliações. A persistência usa PostgreSQL no
Supabase; as contas são gerenciadas pelo Supabase Auth, com entrada apenas pela
conta Google.

## Inicialização e estrutura

`run.py` chama `create_app`, definida em `app/__init__.py`. A fábrica carrega o
`.env` da raiz, configura a aplicação, exige `SECRET_KEY`, configura a proteção CSRF, monta os repositórios, registra a renovação de
sessão e os três Blueprints. A função `configurar_seguranca` também define
headers, cookies e limites de requisições; a revisão da inicialização do
CSRF faz parte da [#127](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/127). O Gunicorn usa a mesma aplicação pelo alvo `run:app`.

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
| `app/routes/professor_routes.py` | Busca, perfil do professor, comparação, ranking e avaliações (`professor_bp`) |
| `app/controllers/auth_controller.py` | Início e conclusão do login com Google |
| `app/controllers/session_controller.py` | Identificação do usuário, cookies, renovação, logout e `login_required` |
| `app/controllers/professor_controller.py` | Catálogo, seleção de professores e disciplinas, indicadores e operações de avaliação |
| `app/validacoes.py` | Critérios e validação das notas |
| `app/seguranca.py` | Configuração de segurança, headers e limites de requisições na main |
| `app/utils.py` | Normalização de texto para buscas |
| `app/repositorio.py` | Repositórios de usuários, professores e avaliações |
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
| GET | `/perfil` | Autenticado | Dados e avaliações do próprio usuário |
| GET | `/professores` | Público | Catálogo filtrado por `nome`, `disciplina` e `departamento` |
| GET | `/professores/<int:professor_id>` | Público | Perfil e médias; `disciplina_id` seleciona a disciplina |
| GET | `/comparar` | Público | Compara `professor_1` e `professor_2` |
| GET | `/ranking` | Público | Classificação por média, com mínimo de cinco avaliações válidas |
| GET, POST | `/avaliar/<int:professor_id>` | Autenticado | Formulário e registro de notas para uma disciplina vinculada |
| GET, POST | `/avaliacoes/<int:avaliacao_id>/editar` | Autor autenticado | Formulário e atualização das próprias notas |
| POST | `/avaliacoes/<int:avaliacao_id>/excluir` | Autor autenticado | Exclusão da própria avaliação |

O perfil e o formulário de avaliação recebem também `next` para manter a URL
de retorno da busca. A validação desse parâmetro está em `app/seguranca.py`;
o bloqueio de barra invertida foi integrado no
[PR #133](https://github.com/unb-mds/2026-2-AvaliaAiUnB/pull/133).

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
[issue #126](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/126).

`login_required` redireciona navegadores sem sessão para `/login`; clientes que
aceitam apenas JSON recebem HTTP 401. Tentativas de carregar, editar ou excluir
avaliações de outro usuário recebem HTTP 404, pois a consulta inclui o autor.

## Repositórios e consultas

Os repositórios ficam em `current_app.extensions['repositorios']` e são obtidos
por `repositorios()` dentro do contexto Flask.

- `UsuarioRepository`: contas no Supabase Auth, perfis e operações de sessão.
- `ProfessorRepository`: professores, disciplinas pela view
  `vw_professor_disciplina`, catálogo, departamentos e ranking.
- `AvaliacaoRepository`: registro, consulta, médias, edição e exclusão de notas.

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
`docs/migrations/001_initial_schema.sql`. Sua aplicação ao ambiente real
deve ser conferida no Supabase.
O
[modelo de dados e a proposta de comentários](Modelo%20de%20Dados.md)
foram publicados na [issue #109](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/109).
Este guia descreve as operações do backend; as regras futuras de comentários
serão consolidadas e revisadas na
[issue #116](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/116).

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
