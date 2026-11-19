# Nova interface

Esta branch aplica a interface editorial aprovada à aplicação Flask existente: fundo preto, destaque verde, tema claro opcional, fontes locais e chapéu branco com estrela dourada. A proposta está relacionada à issue #245. A versão principal e seu histórico são preservados para revisão e reversão.

## O que está incluído

- Início com destaques calculados a partir do catálogo real, consulta com autocompletar e paginação, perfil docente, ranking com filtro de departamento e comparação de vários professores.
- Login Google, cadastro no primeiro acesso, perfil do estudante, criação, edição e exclusão das próprias avaliações, fluxo separado de verificação de e-mail, Sobre, privacidade e feedback.
- Comentários públicos com filtro por disciplina e edição/exclusão pelo autor.
- Reações de gostar e não gostar: repetir remove a reação; escolher a outra troca a opção; o autor não reage ao próprio comentário. Os ícones usam contorno, sem emoji amarelo.
- Temas persistidos no navegador, menu móvel e botão de tema centralizado, com acesso à conta também no cabeçalho do celular.

As disciplinas e ações adicionais dos cartões estão em **Disciplinas e avaliações** e **Mais opções**. A comparação mantém a tabela completa em **Ver notas por critério e destaques**. Os destaques da home são ordenados por quantidade de avaliações; o ranking continua exigindo pelo menos cinco avaliações válidas.

## Como executar esta branch

Requisitos: Python 3.11 ou superior e um projeto Supabase configurado conforme [Hospedagem](HOSPEDAGEM.md). No PowerShell, a partir da pasta do repositório:

```powershell
git switch nova-interface
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Preencha o arquivo `.env` local com `SECRET_KEY`, `SUPABASE_URL` e `SUPABASE_SERVICE_KEY` do ambiente apropriado. Não envie esse arquivo ao GitHub. O backend usa as credenciais do servidor; nenhuma chave de serviço deve ir para JavaScript ou HTML.

```powershell
& .\.venv\Scripts\python.exe run.py
```

Acesse o endereço informado pelo Flask. O catálogo e as operações usam o Supabase configurado. O login Google exige as URLs de retorno corretas no provedor; um domínio de preview precisa estar autorizado para concluir o OAuth. SMTP só é necessário para o fluxo separado e opcional de verificação do perfil.

Esta branch não depende do arquivo HTML de referência, de scripts da máquina da autora, de contas de demonstração ou de uma cópia de usuários. Os dados ilustrativos do protótipo não foram incorporados ao aplicativo. A prévia anterior com gravações em memória não faz parte da entrega versionada.

## Ativar as reações

A migração [005_reacoes_comentarios.sql](migrations/005_reacoes_comentarios.sql) depende da estrutura existente de perfis e comentários. Ela cria uma tabela e duas funções SQL; não reexecute as migrações anteriores sobre um banco já configurado.

Valide e aplique a migração primeiro em um Supabase de desenvolvimento. Ela não é aplicada automaticamente ao iniciar a aplicação ou ao abrir esta branch. A versão anterior de comentários continua funcionando sem a migração; os controles de reação ficam indisponíveis até ela estar presente.

As funções usam `SECURITY INVOKER`, RLS e acesso restrito ao backend. A alternância trava a linha do comentário e a contagem é agregada no banco. As contagens não revelam a identidade de quem reagiu. A migração não modifica os dados ou as permissões existentes dos comentários.

## Validação

```powershell
& .\.venv\Scripts\python.exe -m pip install pytest "mkdocs>=1.6,<2" "mkdocs-material>=9.5,<10"
& .\.venv\Scripts\python.exe -m unittest discover -s tests -t .
& .\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
& .\.venv\Scripts\python.exe -m mkdocs build --strict
```

Os testes da aplicação usam clientes simulados e não escrevem no banco online. Para validar o SQL em um PostgreSQL embarcado descartável, é possível instalar PGlite fora das dependências de produção:

```powershell
npm install --prefix .venv/sql-test --no-save --package-lock=false @electric-sql/pglite@0.5.16
node tests/validar_reacoes_sql.mjs .venv/sql-test/node_modules/@electric-sql/pglite/dist/index.js
```

O teste SQL verifica a migração repetida, permissões, alternância e contagem com dados fictícios. Não substitui homologação no Supabase nem teste de concorrência entre conexões reais.

Validação da entrega em 19/11/2026: 396 testes pelo unittest; 419 testes e 170 subtestes pelo pytest; validação SQL descartável aprovada; documentação compilada com `mkdocs build --strict`. As contagens são execuções da mesma suíte por ferramentas diferentes e não devem ser somadas.

O catálogo, perfil, comentários, comparação, temas e navegação foram inspecionados na prévia local. Login Google real, envio SMTP e persistência online exigem validação no ambiente configurado antes da publicação definitiva. Testes aprovados não garantem ausência de todos os problemas.

## Pendências que ficam com as demais issues

- #213: escolher a ordenação dos comentários e ampliar o acesso além dos 50 mais recentes.
- #214: filtro automático de ofensas, spam e dados pessoais.
- #215, #216 e #217: denúncias, moderação e retenção dos registros.
- #211: decisões do grupo sobre as regras de comentários, incluindo verificação e eventual exposição do e-mail. A implementação atual exibe somente o nome de usuário.
- #221, #223 e #224: filtros por nota/volume, favoritos e evolução por semestre.
- #226 e #236: homologar o espaçamento da comparação mobile e ajustar nomes em caixa alta.
- #242: decidir a política de histórico e de apresentação dos semestres.

As tarefas de documentação e releases finais continuam no planejamento do grupo. Esta branch não declara essas funcionalidades concluídas nem encerra automaticamente a #245.

## Revisão, publicação e reversão

A branch foi preparada a partir da `main`, preservando workflows, documentação, backups e configurações existentes. O envio da branch não incorpora suas mudanças à `main`. Um link navegável para o grupo depende de um deploy de preview da hospedagem; o link da branch por si só mostra o código.

Antes da publicação definitiva, revise os checks, configure um ambiente apropriado, homologue os fluxos autenticados e aplique a migração se as reações forem ativadas. Não use os testes automatizados para criar conteúdo no banco público.

Se a proposta não for aprovada, basta manter a `main`. Depois de um merge, a mudança visual pode ser revertida por um novo commit/PR. Reverter o código não desfaz migrações nem recupera dados excluídos; evite remover tabelas ou dados para reverter apenas o visual.
