# 🎓 AvaliaAi UnB

> **Plataforma de consulta, comparação e avaliação de professores e disciplinas da Universidade de Brasília (UnB).**

O **AvaliaAi** nasce para tornar a escolha de disciplinas e docentes mais informada, centralizando avaliações pedagógicas e transformando relatos dispersos em informações organizadas, objetivas e fáceis de consultar.

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

| Funcionalidade | Release prevista |
|---|:---:|
| Cadastro de usuário | 🚀 R1 |
| Login / autenticação | 🚀 R1 |
| Busca de professores e disciplinas | 🚀 R1 |
| Perfil do professor | 🚀 R1 |
| Avaliação por critérios | 🚀 R1 |
| Visualização de médias | 🚀 R1 |
| Ranking de professores | 🔮 R2 |
| Comparação entre professores | 🔮 R2 |
| Filtros avançados | 🔮 R2 |
| Moderação de avaliações | 🔮 R2 |
| Favoritar professores | 🔮 R2 |
| Gráficos de desempenho | 🔮 R2 |

---

## 🏗️ Arquitetura

O AvaliaAi UnB utiliza uma arquitetura web modular, desenvolvida em Python com Flask, organizada em camadas responsáveis pela interface, pelo processamento das requisições, pelas regras da aplicação e pela persistência de dados.

```text
┌─────────────────────────────────────────────┐
│                FRONTEND                     │
│       HTML5 · CSS3 · JavaScript · Jinja2    │
└─────────────────────┬───────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│                 BACKEND                     │
│              Python · Flask                 │
│                                             │
│  auth_routes.py       professor_routes.py   │
└─────────────────────┬───────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│             LÓGICA DA APLICAÇÃO             │
│                                             │
│  session_controller.py · validacoes.py      │
│  Autenticação · Sessões · Avaliações         │
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
│                 Supabase                    │
│  Usuários · Professores · Disciplinas       │
│  Avaliações · Sessões                       │
└─────────────────────────────────────────────┘
```

---

## 🛠️ Stack tecnológica

| Camada | Tecnologias |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript |
| **Templates** | Jinja2 |
| **Backend** | Python, Flask e Blueprints |
| **Banco de dados** | Supabase |
| **Design / Prototipagem** | Figma |
| **Versionamento** | Git + GitHub |
| **Deploy / Hospedagem** | Render / Heroku |

---

## Configuração e execução

Instale as dependências com `pip install -r requirements.txt`, copie `.env.example`
para `.env` na raiz e preencha as variáveis abaixo. O `.env` é ignorado pelo Git;
em produção, configure as variáveis diretamente no ambiente da hospedagem.
Variáveis já definidas no ambiente têm prioridade sobre o `.env`.

| Variável | Obrigatória | Uso |
|---|---|---|
| `SECRET_KEY` | Sim | Assina a sessão Flask e os tokens CSRF. Use uma chave aleatória, privada e estável entre processos e reinícios. A aplicação não inicia se estiver ausente ou vazia. |
| `SUPABASE_URL` | Sim | URL do projeto Supabase, usada pela aplicação e pelo scraper. |
| `SUPABASE_SERVICE_KEY` | Sim | Chave de serviço do Supabase, restrita ao servidor. |
| `FLASK_DEBUG` | Não | Desligado por padrão. Somente em desenvolvimento, habilite com `1`, `true`, `yes` ou `on` (sem distinção de maiúsculas). Outros valores mantêm o debug desligado. |

Gere uma `SECRET_KEY` com `python -c "import secrets; print(secrets.token_hex(32))"`
e salve o resultado no ambiente ou no `.env`, sem incluí-lo no controle de versão.
Execute localmente com `python run.py`. Para publicar, use um servidor WSGI e
mantenha `FLASK_DEBUG` ausente ou definido como `0`.

Todos os formulários POST (cadastro, login, avaliação e logout) enviam um campo
oculto `csrf_token`. Requisições sem token, com token inválido ou expirado recebem
HTTP 400 antes de executar a operação. Recarregue a página para obter um novo token.
Clientes que enviam POSTs diretamente também precisam carregar o formulário por GET,
preservar o cookie de sessão Flask e enviar o token no campo `csrf_token` ou no
cabeçalho `X-CSRFToken`, conforme a [documentação do Flask-WTF](https://flask-wtf.readthedocs.io/en/stable/csrf/).

Para criar ou recriar a estrutura do banco de dados em um projeto Supabase vazio,
abra o **SQL Editor** no painel do Supabase, cole o conteúdo de
`docs/migrations/001_initial_schema.sql` e clique em **Run**. O script cria as
tabelas (`professores`, `disciplinas`, `turmas`, `perfis` e `avaliacoes`), as
constraints únicas e a view `vw_professor_disciplina`.

Execute os testes com `python -m unittest discover -s tests -t .`. Eles usam um
cliente Supabase falso e uma chave exclusiva de teste, sem credenciais reais.

---

## 🔐 Segurança e moderação

O projeto prevê mecanismos para garantir uma utilização responsável da plataforma, incluindo:

- autenticação segura;
- armazenamento seguro de senhas;
- comunicação via HTTPS;
- moderação de avaliações;
- denúncia e remoção de conteúdos ofensivos;
- prevenção de conteúdos difamatórios e discursos de ódio;
- atenção à **LGPD** no tratamento de dados de estudantes e professores.

---

## ⚙️ Requisitos não funcionais

O documento de visão estabelece, entre outros pontos:

- **Usabilidade:** interface intuitiva, responsiva e acessível;
- **Desempenho:** buscas e páginas de perfil com resposta inferior a 2 segundos sob carga normal;
- **Segurança:** senhas protegidas e comunicação via HTTPS;
- **Confiabilidade:** atualização atômica das médias após novas avaliações válidas;
- **Portabilidade:** funcionamento consistente em navegadores modernos.

---

## 📁 Organização da documentação

```text
.
├── docs/
│   └── DOCUMENTO_DE_VISAO.md
└── README.md
```

O diretório `docs/` concentra a documentação de visão do projeto.

---

## 🚀 Release 1

A realese 1 prioriza o fluxo essencial para consulta e avaliação:

```text
Cadastro
   ↓
Login
   ↓
Busca por professor/disciplina
   ↓
Perfil do professor
   ↓
Consulta das avaliações
   ↓
Avaliação por critérios
   ↓
Atualização das médias
```

As funcionalidades de ranking, comparação, filtros avançados, favoritos e gráficos ficam previstas para etapas posteriores.

---

## 📌 Restrições do projeto

De acordo com o documento de visão, o desenvolvimento deve:

- ser realizado dentro do período letivo da disciplina de **MDS na UnB**;
- utilizar **Python + Flask** no backend;
- utilizar **Supabase** como banco de dados;
- utilizar hospedagem em nuvem;
- observar a **LGPD**;
- aplicar diretrizes de moderação para conteúdos ofensivos, difamatórios ou de discurso de ódio.

---

## 🧭 Roadmap conceitual

```text
[✓] Definição do problema
        ↓
[✓] Levantamento de personas e necessidades
        ↓
[✓] Definição da visão e requisitos
        ↓
[✓] Entrega de Release 1
        ↓
[✓] Autenticação e cadastro
        ↓
[✓] Catálogo de professores e disciplinas
        ↓
[✓] Sistema de avaliações
        ↓
[✓] Médias e estatísticas
        ↓
[✓] Funcionalidades da Release 2
```

---

## 📚 Documentação

| Recurso | Acesso |
|---|---|
| 🎨 **Protótipo / Board Figma** | [Abrir no Figma](https://www.figma.com/board/PgqkPopVXOiSqm9gD5RRNv/AvaliaAi---Template-MDS?node-id=0-1&p=f&t=Rxu6jVCgeVZHCyg2-0) |
| 📖 **Documento de Visão** | [docs/DOCUMENTO_DE_VISAO.md](docs/DOCUMENTO_DE_VISAO.md) |

---

## 💡 Sobre o projeto

O **AvaliaAi** é um projeto acadêmico desenvolvido no contexto de **MDS — Métodos de Desenvolvimento de Software na Universidade de Brasília (UnB)**.

A proposta é criar uma ferramenta que aproxime estudantes e informações relevantes sobre sua experiência acadêmica, transformando avaliações dispersas em dados estruturados e úteis para consulta.

## Como rodar o projeto

### Opção A: Execução Local
1. Crie o ambiente virtual: `python -m venv venv`
2. Ative o ambiente: `venv\Scripts\activate` (Windows) ou `source venv/bin/activate` (Linux/Mac)
3. Instale as dependências: `pip install -r requirements.txt`
4. Copie o ficheiro .env.example e mude o nome da cópia para .env. Preencha as seguintes variáveis: SECRET_KEY (chave de segurança da aplicação Flask), SUPABASE_URL (URL de conexão ao banco) e SUPABASE_SERVICE_KEY (chave de serviço para acesso aos dados). Aviso: O ficheiro .env contém dados sensíveis e nunca deve ser enviado para o GitHub!
5. Inicie o servidor: `python run.py`

### Opção B: Execução com Docker
1. Certifique-se de que tem o Docker instalado e o ficheiro `.env` criado na raiz.
2. No terminal, execute: `docker compose up --build`
3. Aceda à aplicação no navegador em `http://localhost:8000`

---

<p align="center">
  <strong>🎓 AvaliaAi UnB</strong><br>
  Informação organizada para escolhas acadêmicas mais conscientes.
</p>
