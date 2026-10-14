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
│                  SQLite                     │
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
| **Banco de dados** | SQLite, Postgre |
| **Design / Prototipagem** | Figma |
| **Versionamento** | Git + GitHub |
| **Deploy / Hospedagem** | Render / Heroku |

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
- utilizar **SQLite** como banco de dados;
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
[ ] Autenticação e cadastro
        ↓
[ ] Catálogo de professores e disciplinas
        ↓
[ ] Sistema de avaliações
        ↓
[ ] Médias e estatísticas
        ↓
[ ] Funcionalidades da Release 2
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

---

<p align="center">
  <strong>🎓 AvaliaAi UnB</strong><br>
  Informação organizada para escolhas acadêmicas mais conscientes.
</p>
