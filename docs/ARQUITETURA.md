# Diagramas de Arquitetura

Os diagramas representam a arquitetura do AvaliaUnB implementada na `main`.

=== "Contexto"

    ### Diagrama de Contexto

    ![Diagrama de contexto do AvaliaUnB](diagrama-contexto.svg)

    Qualquer visitante pode consultar o catálogo. O registro de notas exige
    login com nome de usuário e senha, validados pelo Supabase Auth. O scraper
    importa professores, disciplinas e turmas do SIGAA.

=== "Componentes da aplicação"

    ### Diagrama de Componentes da Aplicação

    ![Diagrama de componentes da aplicação](diagrama-componentes.svg)

    As rotas Flask renderizam os templates Jinja2 e delegam as operações aos
    controllers. Os repositórios usam o cliente Supabase para dados e autenticação.

=== "Tech Stack"

    ### Tech Stack

    ![Tech Stack do AvaliaUnB](tech-stack.svg)

    O Flask renderiza as páginas Jinja2. O Supabase hospeda o PostgreSQL e
    gerencia contas e sessões com o Supabase Auth. O scraper coleta o catálogo
    do SIGAA em um processo separado.

## Aprofundamento

Os diagramas mostram as relações gerais. Consulte o [guia do backend](BACKEND.md)
para rotas e repositórios, o [modelo de dados](Modelo%20de%20Dados.md)
para tabelas e RLS, o [scraper](COMO_USAR_SCRAPER.md) para a coleta e
[o mapa da documentação](GUIA_DOCUMENTACAO.md) para os demais temas.
