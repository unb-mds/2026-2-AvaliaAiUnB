# Release Notes - v1.0.1 | AvaliaUnB

Nesta atualização da Release 1 do AvaliaAi, entregamos novas funcionalidades de consulta, comparação e gestão de avaliações para os usuários, além de evoluirmos a persistência de dados para a nuvem, a automação de testes e deploy, a segurança da aplicação e a documentação do projeto.

## Novidades e Funcionalidades
- **Ranking de Professores:** Nova visualização com os docentes mais bem avaliados da plataforma a partir das notas registradas.
- **Comparação de Professores:** Tela dedicada para comparar lado a lado os critérios e as médias de diferentes docentes.
- **Perfil do Usuário e Gestão de Avaliações:** Área autenticada onde o usuário visualiza suas avaliações enviadas, podendo editá-las ou excluí-las.
- **Busca e Navegação Aprimoradas:** Adição de filtro por departamento nas consultas e melhorias na navegação de retorno entre as telas de listagem e detalhes.
- **Scraper Expandido:** O coletor de dados do SIGAA foi atualizado para percorrer e extrair turmas de todas as unidades acadêmicas da UnB.

## Infraestrutura, Segurança e Documentação
- **Banco de Dados na Nuvem:** Substituição do banco local (SQLite) pelo Supabase (PostgreSQL), mantendo o restante da aplicação leve e escalável.
- **CI/CD e Deploy:** Configuração do pipeline de integração contínua no **GitHub Actions** (testes automatizados) e deploy contínuo da aplicação na **Vercel**.
- **Suporte a Docker:** Adição de `Dockerfile` e `docker-compose.yml` como opção padronizada para execução em ambiente local.
- **Auditoria e Reforço de Segurança:** Implementação das melhorias levantadas na auditoria de segurança, incluindo proteção de sessão, validação de entrada, política de cabeçalhos (CSP) e exigência de `SECRET_KEY`.
- **Otimização de Dependências e Limpeza:** Isolamento das dependências pesadas do scraper (Selenium) em `requirements-scraper.txt` e remoção de resíduos do banco legado no repositório.
- **Evolução da Documentação:** Atualização do site no GitHub Pages (MkDocs) com o **Diagrama de Arquitetura** (Contexto, Componentes e Tech Stack), **Modelo de Dados**, Story Map, User Stories e link para o protótipo no Figma.

## Limitações conhecidas
- Funcionalidades de moderação mais robusta de avaliações seguem previstas para as próximas versões.
- O scraper do SIGAA ainda precisa ser executado separadamente para atualizar a base de turmas no banco de dados.

## Como acessar e rodar

### Acesso online
A aplicação está disponível no ar em: **https://avaliaunb.com.br**

### Execução local (opcional)
Caso queira rodar o projeto localmente (via **Docker** ou ambiente Python):

1. **Configure as variáveis de ambiente:**
   Copie o arquivo `.env.example` para `.env` e preencha as chaves obrigatórias:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
   - `SECRET_KEY`

2. **Inicie a aplicação com Docker:**
   Na raiz do projeto, execute:
   ```bash
   docker compose up --build