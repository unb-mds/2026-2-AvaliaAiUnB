---
title: Início
hide:
  - toc
---

<div class="hero" markdown>

# AvaliaAi UnB

Plataforma de consulta, comparação e avaliação de professores e disciplinas da Universidade de Brasília.

<div class="hero-actions" markdown>

[Acessar o site :material-open-in-new:](https://avaliaunb.com.br/){ .md-button .md-button--primary }

[Código no GitHub :fontawesome-brands-github:](https://github.com/unb-mds/2026-2-AvaliaAiUnB){ .md-button .md-button--primary }

[Documento de visão :material-file-document-outline:](DOCUMENTO_DE_VISAO.md){ .md-button .md-button--primary }

</div>

</div>

## O que o AvaliaAi faz

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

Na matrícula, o estudante decide em pouco tempo, e as informações estão espalhadas em grupos de WhatsApp e Telegram ou nem existem de forma organizada. O SIGAA mostra horários e vagas, mas não o jeito de ensinar de cada professor. O AvaliaAi reúne isso em avaliações objetivas e fáceis de consultar.

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

<div class="grid cards" markdown>

- :material-file-document-outline: **[Documento de visão](DOCUMENTO_DE_VISAO.md)**

    ---

    Problema, personas, requisitos, story map e user stories.

- :material-list-box-outline: **[Funcionalidades](FUNCIONALIDADES.md)**

    ---

    Regras da busca, avaliações, ranking e comparação.

- :material-cloud-outline: **[Hospedagem](HOSPEDAGEM.md)**

    ---

    Endereços, variáveis de ambiente e validação do deploy.

- :material-sitemap-outline: **[Arquitetura](ARQUITETURA.md)**

    ---

    Diagramas de contexto, de componentes e a tech stack.

- :material-shield-check-outline: **[Auditoria de segurança](AUDITORIA_SEGURANCA.md)**

    ---

    O que foi verificado e o que foi encontrado.

- :simple-figma: **[Protótipo no Figma](https://www.figma.com/board/PgqkPopVXOiSqm9gD5RRNv/AvaliaAi---Template-MDS?node-id=0-1&p=f&t=Rxu6jVCgeVZHCyg2-0)**

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
