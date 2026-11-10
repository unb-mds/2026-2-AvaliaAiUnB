---
title: Início
hide:
  - toc
---

<div class="hero" markdown>

# AvaliaUnb

Plataforma de consulta, comparação e avaliação de professores e disciplinas da Universidade de Brasília.

<div class="hero-actions" markdown>

[Acessar o site :material-open-in-new:](https://avaliaunb.com.br/){ .md-button .md-button--primary }

[Código no GitHub :fontawesome-brands-github:](https://github.com/unb-mds/2026-2-AvaliaAiUnB){ .md-button .md-button--primary }

[Documento de visão :material-file-document-outline:](DOCUMENTO_DE_VISAO.md){ .md-button .md-button--primary }

</div>

</div>

## O que o AvaliaUnb faz

<div class="grid cards" markdown>

- :material-magnify: **Busca**

    ---

    Encontre professores e disciplinas por nome, departamento ou disciplina.

- :material-star-outline: **Avaliações por critérios**

    ---

    Didática, clareza, organização, disponibilidade e dificuldade, sempre com a mesma régua.

- :material-chart-bar: **Médias consolidadas**

    ---

    As notas de cada professor, por disciplina, em um só lugar.

- :material-trophy-outline: **Ranking**

    ---

    Veja quem está melhor avaliado pelos estudantes.

- :material-scale-balance: **Comparação**

    ---

    Coloque dois professores lado a lado antes de montar a grade.

- :material-account-circle-outline: **Perfil do estudante**

    ---

    Cada pessoa vê, edita e apaga as próprias avaliações.

</div>

## Por que ele existe

!!! info "O problema"
    **Insegurança e falta de transparência na escolha de docentes e disciplinas na matrícula da UnB.**

Na matrícula, o estudante decide em pouco tempo, e as informações estão espalhadas em grupos de WhatsApp e Telegram ou nem existem de forma organizada. O SIGAA mostra horários e vagas, mas não o jeito de ensinar de cada professor. O AvaliaUnb reúne isso em avaliações objetivas e fáceis de consultar.

## Como é feito

<div class="grid cards" markdown>

- :simple-flask: **Flask**

    ---

    Aplicação web em Python.

- :simple-supabase: **Supabase**

    ---

    Banco PostgreSQL, autenticação e regras de acesso (RLS).

- :simple-docker: **Docker**

    ---

    Ambiente igual para toda a equipe.

- :simple-githubactions: **GitHub Actions**

    ---

    Testes e verificações de segurança em todo pull request.

</div>

## Explore a documentação

Para navegar por assunto e evitar versões divergentes, consulte o
[mapa da documentação](GUIA_DOCUMENTACAO.md).

<div class="grid cards" markdown>

- :material-file-document-outline: **[Documento de visão](DOCUMENTO_DE_VISAO.md)**

    ---

    Problema, personas, requisitos, story map e user stories.

- :material-list-box-outline: **[Funcionalidades](FUNCIONALIDADES.md)**

    ---

    Regras da busca, avaliações, ranking e comparação.

- :material-database: **[Modelo de dados](Modelo%20de%20Dados.md)**

    ---

    Esquema, relações, políticas e diferenças entre versão SQL e banco implantado.

- :material-database-import: **[Scraper SIGAA](COMO_USAR_SCRAPER.md)**

    ---

    Instalação, coleta, dry-run e atualização do catálogo.

- :material-cloud-outline: **[Hospedagem](HOSPEDAGEM.md)**

    ---

    Endereços, variáveis de ambiente e validação do deploy.

- :material-sitemap-outline: **[Arquitetura](ARQUITETURA.md)**

    ---

    Diagramas de contexto, de componentes e a tech stack.

- :material-code-tags: **[Backend](BACKEND.md)**

    ---

    Rotas, sessão, persistência e testes da aplicação.

- :material-monitor: **[Frontend](FRONTEND.md)**

    ---

    Templates, estilos, estados e contribuição.

- :material-comment-outline: **[Comentários avaliativos](COMENTARIOS.md)**

    ---

    Especificação para revisão do grupo.

- :material-source-branch: **[Pipeline](pipeline.md)**

    ---

    Testes, auditoria automatizada e publicação da documentação.

- :material-check-all: **[DoR e DoD](PROCESSO_CONTRIBUICAO.md)**

    ---

    Critérios de início e conclusão para issues e pull requests.

- :material-shield-check-outline: **[Auditoria de segurança](AUDITORIA_SEGURANCA.md)**

    ---

    Diagnóstico histórico, correções e limites da auditoria.

- :material-shield-lock-outline: **[Cibersegurança](CIBERSEGURANCA.md)**

    ---

    Mecanismos atuais e plano de correções.

- :simple-figma: **[Board do Figma](https://www.figma.com/board/PgqkPopVXOiSqm9gD5RRNv/AvaliaAi---Template-MDS?node-id=0-1)**

    ---

    Board com o design e os materiais da interface.

</div>

??? note "Para desenvolvedores: rodar o projeto no seu computador"
    O site já está no ar em [avaliaunb.com.br](https://avaliaunb.com.br/). Esta parte é só para quem quer mexer no código.

    1. Copie o arquivo `.env.example` para `.env` e preencha as variáveis descritas no README do repositório.
    2. Na raiz do projeto, rode:

        ```bash
        docker compose up --build
        ```

    3. Abra `http://localhost:8000/` no navegador.
