# 🎓 AvaliaAi UnB

> **Plataforma de consulta, comparação e avaliação de professores e disciplinas da Universidade de Brasília (UnB).**

O **AvaliaAi** nasce para tornar a escolha de disciplinas e docentes mais informada, centralizando avaliações pedagógicas e transformando relatos dispersos em informações organizadas, objetivas e fáceis de consultar.

---

## 📚 Documentação Oficial (GitHub Pages)

Toda a documentação técnica, arquitetura, story maps, guias de contribuição e manuais do projeto estão centralizados no nosso site oficial gerado com **MkDocs**:

👉 **[Acessar a Documentação do AvaliaAi (GitHub Pages)](https://unb-mds.github.io/2026-2-AvaliaAiUnB/)**

---

## ✨ Visão geral

Durante o período de matrícula, estudantes precisam tomar decisões importantes em pouco tempo. Atualmente, informações sobre professores e disciplinas podem estar espalhadas em grupos de WhatsApp/Telegram ou simplesmente não estar disponíveis de forma estruturada.

O AvaliaAi propõe uma plataforma web que reúne:

- 🔎 **Busca de professores e disciplinas**
- ⭐ **Avaliações por critérios objetivos**
- 📊 **Médias e estatísticas consolidadas**
- ⚖️ **Comparação entre professores**
- 🛡️ **Moderação de avaliações**
- 🔐 **Autenticação de usuários**
- 📚 **Informações organizadas para apoiar a escolha de turmas**

A proposta é oferecer uma experiência focada na realidade acadêmica da UnB, com critérios como **didática, clareza, organização, disponibilidade e dificuldade**.

---

## 🎨 Design e protótipo

O protótipo e os materiais de interface do projeto estão disponíveis no Figma:

👉 **[Acessar o board do Figma](https://www.figma.com/board/PgqkPopVXOiSqm9gD5RRNv/Template-MDS--c%C3%B3pia-limpa---c%C3%B3pia-?node-id=0-1&t=JgPcJPdPogrAMhcN-0)**

---

## 📖 Documento de visão

O documento de visão contém o detalhamento do problema, posicionamento do produto, personas, arquitetura, stack tecnológica, requisitos funcionais e não funcionais e restrições do projeto.

📄 **[Consultar o Documento de Visão](docs/DOCUMENTO_DE_VISAO.md)**

> O documento de visão é a principal referência para entender o contexto, objetivos e requisitos do AvaliaAi.

---

## 🎯 Problema

O problema central identificado pelo projeto é:

> **“Insegurança e falta de transparência na escolha de docentes e disciplinas na matrícula da UnB.”**

Entre as causas levantadas estão:

- dados operacionais no SIGAA sem informações sobre metodologia de ensino;
- opiniões dispersas em grupos de mensagens;
- ausência de resultados consolidados acessíveis aos alunos no momento da matrícula;
- avaliações subjetivas e pouco padronizadas;
- falta de transparência sobre métodos de avaliação;
- pressão causada pela janela curta de matrícula.

O AvaliaAi busca centralizar essas informações e transformá-las em uma experiência de consulta estruturada.

---

## 👥 Público-alvo

### 🧑‍🎓 Estudantes

Estudantes que precisam montar sua grade e desejam conhecer melhor professores e disciplinas antes de realizar a matrícula.

**Principais necessidades:**
- encontrar informações rapidamente;
- consultar avaliações objetivas;
- comparar professores;
- montar uma grade mais consciente;
- reduzir a incerteza na escolha de turmas.

### 👩‍🏫 Docentes

Professores que desejam receber feedback estruturado e construtivo sobre sua atuação pedagógica.

**Principais necessidades:**
- visualizar médias agregadas;
- identificar pontos de melhoria;
- receber feedback baseado em critérios claros;
- contar com moderação contra conteúdos ofensivos ou ataques pessoais.

---

## 🧩 Principais funcionalidades

| Funcionalidade | Release | Status |
|---|:---:|:---:|
| Cadastro de usuário | 🚀 R1 | ✅ Concluído |
| Login / autenticação | 🚀 R1 | ✅ Concluído |
| Busca de professores e disciplinas | 🚀 R1 | ✅ Concluído |
| Perfil do professor | 🚀 R1 | ✅ Concluído |
| Avaliação por critérios | 🚀 R1 | ✅ Concluído |
| Visualização de médias | 🚀 R1 | ✅ Concluído |
| Ranking de professores | 🔮 R2 | ✅ Concluído (v2.0.0) |
| Comparação entre professores | 🔮 R2 | ✅ Concluído (v2.0.0) |
| Moderação de avaliações | 🔮 R2 | Em desenvolvimento |
| Segurança de Banco de Dados (RLS) | 🔮 R2 | ✅ Concluído (v2.0.0) |

### Comparação de professores (RF08)

A página `/comparar` permite selecionar dois professores diferentes e consultar, lado a lado, as médias de didática, clareza, organização, disponibilidade e dificuldade, além da quantidade de avaliações válidas. O acesso está disponível na lista e no perfil de cada professor; os links individuais já preenchem a primeira seleção.

As médias consideram todas as disciplinas e períodos, com o mesmo peso por avaliação. Uma avaliação só entra no cálculo quando todos os cinco critérios têm notas inteiras de 1 a 5. Dificuldade indica exigência (1 = muito fácil; 5 = muito difícil), enquanto nos demais critérios 5 representa excelente. Professores sem avaliações aparecem com um aviso, sem nota artificial. As médias são consultadas a cada comparação e exibidas com duas casas decimais.

### Ranking de professores (RF07)

A página `/ranking` está disponível pelos links na página inicial e na lista de professores. Ela mostra posição, média geral, quantidade de avaliações e acesso ao perfil de cada professor.

- Participam professores com **pelo menos 5 avaliações válidas** (todos os cinco critérios com notas inteiras de 1 a 5).
- A média geral é a soma das notas de **didática, clareza, organização e disponibilidade**, dividida pelo número de avaliações válidas vezes quatro. Todas as disciplinas e períodos têm o mesmo peso por avaliação.
- Dificuldade fica fora da média por medir exigência, sem representar qualidade de ensino.
- A ordem usa a média sem arredondar, depois a quantidade de avaliações (maior primeiro), o nome (sem distinguir acentos e caixa) e o identificador. As posições são sequenciais; a média exibida usa duas casas decimais.
- O ranking consulta as avaliações a cada acesso, sem depender do cache do catálogo. Se ninguém atingir o mínimo, a página informa esse estado.

---

## 🏗️ Arquitetura

O AvaliaAi UnB utiliza uma arquitetura web modular conteinerizada, desenvolvida em Python com Flask, organizada em camadas responsáveis pela interface, processamento, regras da aplicação e persistência de dados em nuvem.

    ┌─────────────────────────────────────────────┐
    │                FRONTEND                     │
    │       HTML5 · CSS3 · JavaScript · Jinja2    │
    └─────────────────────┬───────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────┐
    │                 BACKEND                     │
    │               Python · Flask                │
    │                                             │
    │  auth_routes.py       professor_routes.py   │
    └─────────────────────┬───────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────┐
    │             LÓGICA DA APLICAÇÃO             │
    │                                             │
    │  session_controller.py · validacoes.py      │
    │  Autenticação · Sessões · Avaliações        │
    └─────────────────────┬───────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────┐
    │           MODELOS E REPOSITÓRIOS            │
    │                                             │
    │  models.py · repositorio.py · database.py   │
    └─────────────────────┬───────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────┐
    │              BANCO DE DADOS                 │
    │                                             │
    │           Supabase (PostgreSQL)             │
    │  Usuários · Professores · Disciplinas       │
    │  Avaliações · Sessões (com RLS Auth)        │
    └─────────────────────────────────────────────┘

---

## 🛠️ Stack tecnológica

| Camada | Tecnologias |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript |
| **Templates** | Jinja2 |
| **Backend** | Python, Flask e Blueprints |
| **Banco de dados** | Supabase (PostgreSQL com RLS) |
| **Infraestrutura** | Docker e Docker Compose |
| **Documentação** | MkDocs (GitHub Pages) |
| **Design / Prototipagem** | Figma |
| **Versionamento** | Git + GitHub |

---

## ⚙️ Configuração e execução

O projeto foi atualizado para utilizar **Docker**, garantindo um ambiente idêntico para todos os membros da equipe. Contudo, a execução local nativa continua suportada.

### 1. Variáveis de Ambiente
Copie o ficheiro `.env.example` para um novo ficheiro chamado `.env` na raiz e preencha as variáveis abaixo. O `.env` é ignorado pelo Git; em produção, configure as variáveis diretamente no ambiente da hospedagem.

| Variável | Obrigatória | Uso |
|---|---|---|
| `SECRET_KEY` | Sim | Assina a sessão Flask e os tokens CSRF. Use uma chave aleatória, privada e estável. A aplicação não inicia se estiver ausente ou vazia. |
| `SUPABASE_URL` | Sim | URL do projeto Supabase, usada pela aplicação e pelo scraper. |
| `SUPABASE_SERVICE_KEY` | Sim | Chave de serviço do Supabase, restrita ao servidor. |
| `FLASK_DEBUG` | Não | Habilite com `1` para ambiente de desenvolvimento local. |

*Dica:* Gere uma `SECRET_KEY` segura executando `python -c "import secrets; print(secrets.token_hex(32))"` no terminal.

### 2. Executando com Docker (Recomendado)
Certifique-se de ter o **Docker** e o **Docker Compose** instalados na sua máquina.
1. No terminal, na raiz do projeto, execute:
    docker compose up --build
2. Aceda ao endereço `http://localhost:8000` no seu navegador.

### 3. Executando Localmente (Sem Docker)
1. Crie o ambiente virtual: `python -m venv venv`
2. Ative o ambiente: `venv\Scripts\activate` (Windows) ou `source venv/bin/activate` (Linux/Mac)
3. Instale as dependências: `pip install -r requirements.txt`
4. Execute o servidor: `python run.py`

### 4. Configuração do Banco de Dados e Testes
Para criar ou recriar a estrutura do banco de dados em um projeto Supabase vazio, abra o **SQL Editor** no painel do Supabase, cole o conteúdo de `docs/migrations/001_initial_schema.sql` e clique em **Run**. O script cria as tabelas e configura o **Row Level Security (RLS)**.

Execute os testes automatizados com:
    python -m unittest discover -s tests -t .

Eles usam um cliente Supabase falso e uma chave exclusiva de teste, sem expor credenciais reais.

Todos os formulários POST (cadastro, login, avaliação e logout) exigem o envio de um `csrf_token` oculto, garantindo proteção nativa conforme a documentação do Flask-WTF.

---

## 🔐 Segurança e integridade

O projeto prevê mecanismos rigorosos para garantir uma utilização segura:

- **Autenticação em Nuvem:** Gestão de usuários validada pelo Supabase Auth.
- **Row Level Security (RLS):** Políticas de acesso direto nas tabelas do PostgreSQL que impedem a escrita e manipulação de avaliações por usuários não autenticados ou não autorizados.
- **Proteção CSRF:** Tokens injetados e exigidos em toda rota POST/PATCH/DELETE.
- Atenção à **LGPD** no tratamento de dados de estudantes e professores.

---

## ⚙️ Requisitos não funcionais

- **Usabilidade:** interface intuitiva, responsiva e acessível;
- **Desempenho:** buscas e páginas de perfil com resposta inferior a 2 segundos sob carga normal;
- **Segurança:** senhas protegidas e comunicação restrita via banco RLS;
- **Confiabilidade:** atualização atômica das médias após novas avaliações válidas;
- **Portabilidade:** funcionamento via Docker e em navegadores modernos.

---

## 📁 Organização da documentação

    .
    ├── docs/
    │   ├── DOCUMENTO_DE_VISAO.md
    │   ├── migrations/
    │   └── (demais arquivos gerados para o MkDocs)
    ├── mkdocs.yml
    └── README.md

---

## 🧭 Roadmap conceitual

    [✓] Definição do problema
            ↓
    [✓] Levantamento de personas e necessidades
            ↓
    [✓] Definição da visão e requisitos
            ↓
    [✓] Entrega de Release 1 (Autenticação, Catálogo, Avaliações Básicas)
            ↓
    [✓] Refatoração de Infraestrutura (Docker) e Segurança (Supabase RLS)
            ↓
    [✓] Entrega de Release 2.0.0 (Ranking, Comparação, MkDocs)
            ↓
    [ ] Funcionalidades futuras (Gráficos, Favoritos, Moderação nativa)

---

## 📌 Restrições do projeto

De acordo com o documento de visão, o desenvolvimento deve:
- ser realizado dentro do período letivo da disciplina de **MDS na UnB**;
- utilizar **Python + Flask** no backend;
- utilizar **Supabase** como banco de dados orquestrado com Docker;
- observar rigorosamente a **LGPD** e adotar políticas contra discurso de ódio.

---

<p align="center">
  <strong>🎓 AvaliaAi UnB</strong><br>
  Informação organizada para escolhas acadêmicas mais conscientes.
</p>