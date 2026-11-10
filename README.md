# 🎓 AvaliaUnb

> Consulta, comparação e avaliação de professores e disciplinas da Universidade de Brasília.

O AvaliaUnb reúne avaliações por critérios pedagógicos para ajudar estudantes a
escolher disciplinas e docentes durante a matrícula. É um projeto da disciplina
**Métodos de Desenvolvimento de Software (MDS/UnB), semestre 2026/2**.

**Comece por aqui:** [site](https://avaliaunb.com.br/) ·
[documentação oficial](https://unb-mds.github.io/2026-2-AvaliaAiUnB/) ·
[documento de visão](docs/DOCUMENTO_DE_VISAO.md) ·
[issues do projeto](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues)

## Sumário

- [Sobre o projeto](#sobre-o-projeto)
- [Funcionalidades e releases](#funcionalidades-e-releases)
- [Quem pode usar](#quem-pode-usar)
- [Tecnologias e arquitetura](#tecnologias-e-arquitetura)
- [Como executar](#como-executar)
- [Segurança e correções em andamento](#segurança-e-correções-em-andamento)
- [Documentação](#documentação)
- [Como contribuir](#como-contribuir)
- [Equipe](#equipe)

## Sobre o projeto

Informações sobre professores costumam ficar dispersas em grupos de mensagens,
o que dificulta comparar experiências na hora da matrícula. O AvaliaUnb organiza
a consulta por professor, disciplina e departamento, com notas de **didática,
clareza, organização, disponibilidade e dificuldade**.

O [documento de visão](docs/DOCUMENTO_DE_VISAO.md) apresenta o problema,
as personas, os requisitos e as metas de usabilidade, desempenho e segurança.

## Funcionalidades e releases

O planejamento e o estado da implementação são apresentados separadamente na
tabela. As entregas disponíveis consideram a versão da `main`; branches
anteriores podem conter apenas parte delas.

| Etapa | Funcionalidades | Estado |
|---|---|---|
| R1 — fluxo essencial | Cadastro, login, busca de professores e disciplinas, perfil do professor, avaliação por cinco critérios e consulta de médias | Implementado |
| R2 — consulta e gestão de avaliações | Ranking, comparação entre dois professores, filtro por departamento, busca que ignora acentos e espaços extras e perfil do usuário com edição e exclusão das próprias avaliações | Implementado |
| Evolução dos filtros | Faixa de nota e volume de avaliações | Pendente |
| Comentários e moderação | Comentários, denúncias e remoção por moderação | Em especificação na [#116](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/116); sem fluxo implementado |
| Outras funcionalidades planejadas | Favoritos e gráficos de desempenho | Pendente |

A consulta principal fica em `/professores`; ranking e comparação ficam em
`/ranking` e `/comparar`. A lista é ordenada pela quantidade de avaliações.
O ranking usa a média de quatro critérios, excluindo dificuldade, e exige
pelo menos cinco avaliações válidas.

Veja as [regras de busca, notas, comparação e ranking](docs/FUNCIONALIDADES.md).

## Quem pode usar

| Perfil | Acesso | O que pode fazer |
|---|---|---|
| Visitante | Sem login | Consultar professores, disciplinas, médias, ranking e comparação |
| Usuário cadastrado | Nome de usuário e senha | Consultar e registrar avaliações; listar, editar e excluir as próprias avaliações em `/perfil` |

O público principal são os estudantes da UnB. Docentes também podem consultar
os indicadores públicos. O cadastro atual aceita e-mail `@gmail.com`; a
confirmação do endereço está prevista na
[issue #125](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/125).

## Tecnologias e arquitetura

| Camada | Tecnologias |
|---|---|
| Interface | HTML5, CSS3, JavaScript e templates Jinja2 |
| Backend | Python, Flask e Blueprints |
| Persistência | PostgreSQL hospedado no Supabase |
| Contas e sessões | Supabase Auth |
| Coleta do SIGAA | Python e Selenium, com dependências próprias |
| Execução em contêiner | Docker Compose e Gunicorn |
| Documentação | MkDocs Material e GitHub Pages |
| Testes e qualidade | unittest, pip-audit e Bandit |
| Deploy | Configuração para Vercel adicionada no [PR #131](https://github.com/unb-mds/2026-2-AvaliaAiUnB/pull/131) |

### Backend

`run.py` cria a aplicação por `create_app`, em `app/__init__.py`.
As requisições passam por rotas, controllers e validações até os repositórios,
que acessam o Supabase. O scraper é executado separadamente e alimenta o catálogo.

O [guia do backend](docs/BACKEND.md) detalha a estrutura, as rotas, as sessões,
os repositórios e a integração com o [scraper](docs/COMO_USAR_SCRAPER.md).

### Dados

O banco contém `professores`, `disciplinas`, `turmas`, `perfis` e
`avaliacoes`, além da view `vw_professor_disciplina`. A chave de professor
é nome e departamento; o departamento corresponde à unidade que oferece a
disciplina no SIGAA. Consulte o
[modelo de dados e a proposta de comentários](docs/Modelo%20de%20Dados.md).

### Frontend

As páginas são renderizadas no servidor a partir de `app/templates/`, com
recursos em `app/static/`. O design system e a aplicação do visual final estão
acompanhados nas issues
[#112](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/112) e
[#114](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/114).

O [guia do frontend](docs/FRONTEND.md) inventaria as telas, os estilos e os
estados existentes e explica como contribuir. As definições finais de cores,
tipografia e componentes serão incorporadas quando a #112 for consolidada.

## Como executar

### Ambiente local

Use Python 3.11 ou superior e execute:

```bash
git clone https://github.com/unb-mds/2026-2-AvaliaAiUnB.git
cd 2026-2-AvaliaAiUnB
python -m venv .venv
```

Ative o ambiente virtual com `.\.venv\Scripts\Activate.ps1` no PowerShell ou
`source .venv/bin/activate` no Linux/macOS. Depois instale as dependências:

```bash
pip install -r requirements.txt
```

Copie `.env.example` para `.env` na raiz e preencha:

| Variável | Uso |
|---|---|
| `SECRET_KEY` | Chave privada e estável para sessão Flask e CSRF. Obrigatória; em produção, pelo menos 32 caracteres e sem valores fracos. |
| `SUPABASE_URL` | URL do projeto Supabase. |
| `SUPABASE_SERVICE_KEY` | Chave de serviço, restrita ao servidor. |
| `FLASK_DEBUG` | Opcional; desligado por padrão. Use `1` somente no desenvolvimento local. |

Gere uma chave com `python -c "import secrets; print(secrets.token_hex(32))"`.
O `.env` é ignorado pelo Git; variáveis já definidas no ambiente têm prioridade.

Com o banco configurado, inicie o servidor:

```bash
python run.py
```

Acesse `http://127.0.0.1:5000`. O [guia do scraper](docs/COMO_USAR_SCRAPER.md)
cobre o preparo do banco e a coleta. O esquema inicial passou a incluir RLS
e políticas de acesso na [#123](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/123).

### Docker

Com Docker, Docker Compose e o `.env` configurados, execute:

```bash
docker compose up --build
```

A aplicação será servida pelo Gunicorn em `http://localhost:8000`.
O scraper é executado separadamente.

### Hospedagem

O endereço público informado pela equipe é [avaliaunb.com.br](https://avaliaunb.com.br/).
A configuração para Vercel está no [pyproject.toml](pyproject.toml), com entrada
`run:app`. O guia de hospedagem registra o que está disponível sobre cada ambiente.

As [instruções de hospedagem](docs/HOSPEDAGEM.md) detalham variáveis,
Preview, produção e a validação dos fluxos no ambiente publicado.

## Segurança e correções em andamento

A versão da `main` inclui autenticação com Supabase Auth, proteção CSRF,
cookies de autenticação com `HttpOnly`, `SameSite=Lax` e `Secure` fora do debug,
headers de segurança e limites de requisições. A autorização de edição e
exclusão confere o autor da avaliação no backend.

A [auditoria de 02/11/2026](docs/AUDITORIA_SEGURANCA.md)
foi concluída na #111. O relatório registra um achado de prioridade alta,
três de prioridade média e oito de prioridade baixa, sem achados críticos.
O [PR #139](https://github.com/unb-mds/2026-2-AvaliaAiUnB/pull/139)
versionou RLS e políticas no esquema inicial. A aplicação ainda usa a chave
de serviço. As mudanças seguintes estão nas issues
[#124](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/124),
[#125](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/125),
[#126](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/126),
[#127](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/127),
[#129](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/129) e
[#130](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/130).
A conclusão da auditoria não significa que essas correções já foram aplicadas.
O [resumo de cibersegurança](docs/CIBERSEGURANCA.md) relaciona os mecanismos do
código, a situação do RLS e os resultados da auditoria com cada correção.

Comentários e moderação têm uma [especificação proposta](docs/COMENTARIOS.md),
baseada na #109, para revisão do grupo na
[#116](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/116).
Ela propõe quem pode participar, limites, relação com avaliações, denúncia e
privacidade. A revisão das regras permanece pendente; o recurso não está implementado.

## Documentação

| Assunto | Onde consultar |
|---|---|
| Início e instruções de execução | [Documentação do projeto](docs/index.md) · [Mapa e índice por assunto](docs/GUIA_DOCUMENTACAO.md) |
| Produto e requisitos | [Documento de visão](docs/DOCUMENTO_DE_VISAO.md) |
| Funcionalidades | [Busca, notas, comparação e ranking](docs/FUNCIONALIDADES.md) |
| Backend | [Estrutura, rotas, sessões e repositórios](docs/BACKEND.md) |
| Frontend | [Templates, estilos, estados e contribuição](docs/FRONTEND.md) |
| Dados | [Modelo de dados](docs/Modelo%20de%20Dados.md) |
| Arquitetura | [Diagramas do sistema](docs/ARQUITETURA.md) |
| Coleta | [Guia do scraper](docs/COMO_USAR_SCRAPER.md) |
| Cibersegurança | [Mecanismos e correções](docs/CIBERSEGURANCA.md) · [Relatório da auditoria](docs/AUDITORIA_SEGURANCA.md) |
| Comentários | [Especificação para revisão do grupo](docs/COMENTARIOS.md) |
| Automação e checks | [Pipeline do GitHub Actions](docs/pipeline.md) · [DoR e DoD](docs/PROCESSO_CONTRIBUICAO.md) |
| Hospedagem | [Configuração de Preview, produção e lançamento](docs/HOSPEDAGEM.md) |
| Design | [Board do Figma](https://www.figma.com/board/PgqkPopVXOiSqm9gD5RRNv/AvaliaAi---Template-MDS?node-id=0-1) |
| Histórico | [Release 1](RELEASE-v1.0.0.md) · [Release 2](RELEASE-v2.0.0.md) |

Para abrir o site localmente, instale `mkdocs-material` no ambiente virtual e
execute `mkdocs serve` na raiz. Valide com `mkdocs build --strict`.
Na `main`, o workflow de documentação publica as mudanças em `docs/` ou
`mkdocs.yml` no GitHub Pages.

## Como contribuir

1. Escolha uma [issue](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues)
   e alinhe o escopo com os responsáveis.
2. Crie uma branch a partir da `main` atualizada para a mudança.
3. Use mensagens de commit que indiquem a alteração, como
   `docs: reorganiza o README` ou `fix: corrige filtro de professores`.
4. Para mudanças no código, execute `python -m unittest discover -s tests -t .`.
   A suíte usa um Supabase falso e dispensa credenciais reais e Chrome.
5. Para mudanças na documentação, confira os links e execute
   `mkdocs build --strict`.
6. Abra um pull request para a `main`, referenciando a issue, descrevendo a
   mudança e informando a validação realizada. Confira os checks antes do merge.

Consulte também os [critérios de contribuição](docs/PROCESSO_CONTRIBUICAO.md),
com o Definition of Ready e Definition of Done usados nos templates de issue e PR.

Consulte o [guia do backend](docs/BACKEND.md), os
[diagramas de arquitetura](docs/ARQUITETURA.md) e as
[regras de funcionalidades](docs/FUNCIONALIDADES.md) ao alterar o sistema.

## Equipe

Projeto desenvolvido no contexto da disciplina **Métodos de Desenvolvimento
de Software da Universidade de Brasília**, no semestre **2026/2**.

Os integrantes e suas contribuições podem ser consultados no
[histórico de contribuições](https://github.com/unb-mds/2026-2-AvaliaAiUnB/graphs/contributors).
