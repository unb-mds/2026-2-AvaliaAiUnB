# Release Notes – v2.0.0 | AvaliaAi UnB

Nesta segunda versão do AvaliaAi, o nosso foco principal foi a evolução da infraestrutura, a segurança da aplicação e a melhoria da documentação. O projeto deixou de ser estritamente local e passou a contar com uma arquitetura moderna e orquestrada em nuvem.

## Novidades, Melhorias e Correções
- **Migração para a Nuvem:** Substituímos o banco de dados local (SQLite) pelo Supabase (PostgreSQL), garantindo maior escalabilidade.
- **Dockerização da Aplicação:** O projeto agora é executado dentro de contentores Docker (`Dockerfile` e `docker-compose.yml`), garantindo que o ambiente de desenvolvimento seja idêntico para todos os membros da equipa.
- **Segurança Reforçada (RLS):** Habilitámos o Row Level Security (RLS) nas tabelas do banco de dados (professores, disciplinas, turmas, perfis, avaliações) e criámos Políticas de Acesso restritas (Policies) para evitar leituras e escritas maliciosas.
- **Otimização de Dependências:** O ambiente da API foi limpo. As bibliotecas pesadas do web scraper (Selenium) foram isoladas num ficheiro próprio (`requirements-scraper.txt`).
- **Evolução da Documentação:** O nosso site no GitHub Pages (MkDocs) foi expandido e agora conta com o Diagrama de Arquitetura (Contexto, Componentes e Tech Stack), Story Map, User Stories atualizadas e link direto para o protótipo no Figma.
- **Limpeza de Repositório:** O repositório foi auditado e totalmente limpo de resíduos do banco legado.

## Limitações conhecidas
- Funcionalidades avançadas, como o ranking de professores e a moderação robusta de avaliações, continuam em desenvolvimento e chegarão nas próximas atualizações.
- O scraper do SIGAA ainda precisa ser executado à parte para popular o banco de dados com as turmas.

## Como rodar
Devido à nova arquitetura, a forma de executar o projeto mudou. Agora utilizamos o Docker para facilitar o processo. Certifique-se de ter o **Docker** e o **Docker Compose** instalados.

1. Crie o ficheiro de credenciais:
Copie o ficheiro `.env.example` para um novo ficheiro chamado `.env` e preencha as credenciais do Supabase (`SUPABASE_URL` e `SUPABASE_SERVICE_KEY`).

2. Inicie a aplicação com o Docker:
No terminal, na raiz do projeto, execute:
`docker compose up --build`

3. Acesse no navegador:
Aceda ao endereço local (geralmente `http://localhost:8000/`).

