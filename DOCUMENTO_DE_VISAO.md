# DOCUMENTO DE VISÃO

*Projeto AvaliaAi — Plataforma de Consulta, Comparação e Avaliação de Professores da UnB*

---

## 1. Introdução

### 1.1 Finalidade
Este documento visa o entendimento geral do projeto ao definir as necessidades para o desenvolvimento do sistema AvaliaAi, uma plataforma voltada para consulta, indicação e avaliação pedagógica de professores e disciplinas na Universidade de Brasília (UnB). As informações são apresentadas em alto nível de abstração, servindo como guia de alinhamento comum entre estudantes e docentes.

### 1.2 Escopo
São tratados neste documento os aspectos estratégicos, funcionais, arquiteturais e estruturais do projeto AvaliaAi, abrangendo desde a fase de imersão e análise das causas-raiz do problema e arquitetura do sistema. O sistema engloba busca e filtragem de docentes/disciplinas, avaliação por critérios pedagógicos objetivos, visualização de médias consolidadas, rankings, arquitetura baseada em Python/Flask com banco SQLite e mecanismos de moderação.

### 1.3 Visão Geral
Este documento detalha o posicionamento do produto, analisa as causas-raiz da desinformação na matrícula, mapeia os perfis de usuários e personas, estabelece a arquitetura e stack tecnológica, e especifica os Requisitos Funcionais, Não Funcionais e Restrições.

---

## 2. Posicionamento

### 2.1 Oportunidade de Negócios
Durante o período semestral de matrícula na UnB, os estudantes precisam selecionar disciplinas e docentes que definem seu percurso acadêmico. Contudo, a ausência de uma base centralizada de avaliações didáticas faz com que as decisões ocorram no escuro ou através de grupos dispersos no WhatsApp/Telegram. O AvaliaAi surge para transformar essa realidade, estruturando métricas de didática, organização e clareza, oferecendo transparência aos estudantes e feedback pedagógico construtivo aos professores.

### 2.2 Análise do Problema e Causas-Raiz (Diagrama de Ishikawa)
O problema central identificado é a **"Insegurança e falta de transparência na escolha de docentes e disciplinas na matrícula da UnB"**. A análise aprofundada revelou 6 causas-raiz principais:

- **Sistemas Oficiais (SIGAA):** Exibem apenas dados operacionais (horários, salas e vagas), sem qualquer informação sobre metodologia de ensino ou perfil didático do docente.
- **Dispersão de Dados:** Opiniões e relatos ficam espalhados em grupos não moderados de WhatsApp e Telegram, sem organização por semestre, histórico ou mecanismo de busca estruturada.
- **Avaliação Institucional da UnB:** O processo formal de avaliação docente é anual/semestral com finalidade burocrática de progressão de carreira, e os resultados consolidados não são acessíveis aos alunos no momento da matrícula.
- **Subjetividade e Viés:** Poucos relatos de veteranos focam na facilidade em 'passar fácil' e sofrem com afinidade pessoal, carecendo de métricas objetivas (clareza, didática, organização e pontualidade).
- **Transparência de Ementas:** Planos de ensino despadronizados e sem detalhes práticos sobre métodos de avaliação (pesos de provas, listas e projetos).
- **Pressão de Matrícula:** Janela curta de montagem de grade que força decisões precipitadas, resultando em trancamentos e reprovações posteriores.

### 2.3 Descrição do Problema

| Elemento | Descrição |
| --- | --- |
| **O problema** | Insegurança e falta de transparência na escolha de docentes e disciplinas no período de matrícula da UnB. |
| **Afeta** | Estudantes da UnB (que realizam escolhas desinformadas) e Docentes (que carecem de feedback formal e estruturado para aprimoramento pedagógico). |
| **Cujo impacto é** | Alta taxa de reprovações e trancamentos surpresa, estresse na montagem da grade e falta de canal para evolução metodológica docente. |
| **Uma boa solução seria** | Uma plataforma web dedicada (AvaliaAi) com autenticação segura, busca e filtragem de disciplinas/professores, avaliações por critérios padronizados (didática, clareza, organização, disponibilidade, dificuldade), cálculo de médias e moderação de conteúdo. |

### 2.4 Sentença de Posição do Produto

| Elemento | Descrição |
| --- | --- |
| **Para** | Estudantes e professores da Universidade de Brasília (UnB) |
| **Que** | Necessitam de informações claras para escolher disciplinas e receber feedback didático |
| **O** | AvaliaAi |
| **Que** | Centraliza pesquisas, permite avaliações por critérios objetivos e exibe médias e comparações |
| **Diferente de** | Redes sociais genéricas, grupos informais de WhatsApp/Telegram e fóruns sem moderação |
| **Nosso produto** | Oferece uma estrutura focada na realidade acadêmica da UnB, com métricas pedagógicas específicas, arquitetura modular e moderação de conteúdo. |

---

## 3. Descrições dos Usuários

### 3.1 Perfil das Personas

#### Persona 1: Lucas Martins (Estudante)
- **Idade / Cargo:** 20 anos | Estudante de Engenharia na UnB.
- **Biografia:** Lucas possui uma rotina intensa, equilibrando disciplinas pesadas de exatas com estágio e responsabilidades diárias. Precisa de máxima eficiência no seu tempo. Para ele, escolher professores com boa didática em matérias críticas (Física, Cálculo) é fundamental para aprender e evitar reprovações surpresas.
- **Interesses:** Professores didáticos, economizar tempo na montagem da grade, evitar turmas com alta taxa de reprovação.
- **Objetivos:** Aprovação nas disciplinas semestrais, montagem de grade equilibrada e escolha consciente de professores.
- **Necessidades & Expectativas:** Plataforma rápida e intuitiva; avaliações objetivas por critérios (didática, clareza, organização); comparação visual clara entre professores.
- **Dores & Frustrações:** Falta de informação no SIGAA/MW, informações dispersas em grupos de WhatsApp, matricular-se em turmas sem saber o estilo do professor.

#### Persona 2: Profa. Dra. Helena Vasconcelos (Docente)
- **Idade / Cargo:** 52 anos | Professora Associada e Pesquisadora na UnB há 15 anos.
- **Biografia:** Leciona disciplinas obrigatórias e optativas. Divide seu tempo entre aulas, pesquisas e orientações. Busca constantemente aprimorar sua didática pedagógica, mas sente falta de um canal rápido e estruturado para receber feedback construtivo dos alunos.
- **Interesses:** Evolução metodológica, engajamento dos estudantes, transparência e respeito nas avaliações.
- **Objetivos:** Receber feedback construtivo por critérios, identificar pontos de melhoria e manter bom relacionamento acadêmico.
- **Necessidades & Expectativas:** Critérios claros de avaliação (sem ofensas/ataques pessoais); dados agregados e médias por quesitos; moderação eficaz de conteúdo.
- **Dores & Frustrações:** Falta de diagnóstico contínuo sobre o aprendizado dos alunos, receio de comentários difamatórios anônimos.

### 3.2 Ambiente do Usuário
O AvaliaAi será disponibilizado através de aplicação web responsiva, acessível fluidamente em desktops e notebooks. O Sistema deve suportar múltiplos acessos simultâneos durante os picos de matrícula acadêmica.

---

## 4. Visão Geral do Produto e Arquitetura

### 4.1 Perspectiva e Diagrama de Contexto
O AvaliaAi atua como um sistema autônomo complementar aos sistemas acadêmicos da UnB. O diagrama de contexto estabelece a relação entre os atores e módulos:

- **Estudante (Ator Principal):** Acessa a plataforma para consultar perfis, visualizar notas consolidadas, comparar professores e submeter avaliações.
- **Plataforma AvaliaAi:** Aplicação central que processa regras de negócio, calcula médias ponderadas e gerencia o catálogo.
- **Sistema de Autenticação:** Serviço de validação de identidade (conta própria / OAuth) para garantir que apenas estudantes reais submetam avaliações.
- **Portal SIGAA / Dados Públicos:** Fonte pública de dados de turmas, códigos de disciplinas, horários e departamentos para cruzamento inicial de informações.

### 4.2 Pilha Tecnológica (Tech Stack)

| Camada / Área | Tecnologias Selecionadas |
| --- | --- |
| **Frontend** | HTML5, CSS3, JavaScript e Figma (Design e Prototipagem da Interface). |
| **Backend** | Python, Flask (Microframework Web), Jinja2 (Engine de Templates) e Render / Heroku (Deploy e Hospedagem). |
| **Banco de Dados & Ferramentas** | SQLite (Banco de dados relacional), Git e GitHub (Versionamento e Integração Contínua). |

### 4.3 Arquitetura do Sistema e Componentes
O sistema é estruturado em uma arquitetura modular em camadas:

- **Camada de Apresentação (Frontend / Client UI):** Interface web construída com HTML5/CSS3/JS e templates renderizados dinamicamente via Jinja2.
- **Camada de Controle (Controllers):** Contém o *Autenticação Controller* (gestão de sessões e segurança), *Avaliação Controller* (cálculo de notas e validação) e *Professor/Turma Controller* (consultas, buscas e filtros).
- **Camada de Serviços e Repositórios:** Inclui o *Serviço de Autenticação*, *Avaliação Repository* (persistência SQL das avaliações e comentários) e *Serviço de Sincronização / Parser* (processamento de dados de turmas).
- **Camada de Dados:** Persistência principal via SQLite, dados temporários de sessão em cache e integração com fontes públicas do SIGAA.

---

## 5. Requisitos Funcionais

| Código | Nome | Descrição | Prioridade |
| --- | --- | --- | --- |
| **RF01** | Cadastro de Usuário | Permitir que estudantes criem uma conta no AvaliaAi. | Alta (MVP) |
| **RF02** | Login / Autenticação | Permitir que usuários cadastrados façam login com credenciais seguras. | Alta (MVP) |
| **RF03** | Busca de Professores e Disciplinas | Pesquisar professores por nome, código, departamento ou disciplina. | Alta (MVP) |
| **RF04** | Perfil do Professor | Exibir informações do professor, disciplinas ministradas e histórico de notas. | Alta (MVP) |
| **RF05** | Avaliação por Critérios | Permitir avaliar o professor em critérios: didática, organização, clareza, disponibilidade e dificuldade. | Alta (MVP) |
| **RF06** | Visualização de Médias | Exibir o cálculo de médias agregadas e estatísticas dos professores. | Alta (MVP) |
| **RF07** | Ranking de Professores | Exibir a classificação dos professores mais bem avaliados por departamento ou geral. | Média (Pós-MVP) |
| **RF08** | Comparação entre Professores | Selecionar e comparar lado a lado dois ou mais professores da mesma disciplina. | Média (Pós-MVP) |
| **RF09** | Filtros Avançados | Filtrar professores por faixa de nota, departamento e volume de avaliações. | Média (Pós-MVP) |
| **RF10** | Moderação de Avaliações | Permitir a denúncia e remoção de comentários com linguagem ofensiva. | Média (Pós-MVP) |
| **RF11** | Favoritar Professores | Salvar professores na lista pessoal do usuário para acompanhamento rápido. | Baixa (Pós-MVP) |
| **RF12** | Gráficos de Desempenho | Apresentar gráficos visuais da evolução das notas do professor ao longo dos semestres. | Baixa (Pós-MVP) |

---

## 6. Restrições

- **Restrição de Prazo e Recursos:** O desenvolvimento do projeto deve ser concluído no período letivo da disciplina de MDS na UnB.
- **Tecnologias:** O backend deve ser desenvolvido em Python utilizando o microframework Flask com banco de dados SQLite e hospedagem em nuvem (Render/Heroku).
- **Conformidade com a LGPD:** O tratamento de dados de estudantes e professores deve atender à Lei Geral de Proteção de Dados (LGPD).
- **Diretrizes de Moderação:** O sistema deve barrar conteúdos ofensivos, difamatórios ou discursos de ódio, garantindo a ética nas avaliações docentes.

---

## 7. Requisitos Não Funcionais

- **RNF01 - Usabilidade:** A interface do sistema deve ser intuitiva, responsiva e acessível em dispositivos desktops sem necessidade de treinamento prévio.
- **RNF02 - Desempenho:** A busca por professores e o carregamento das páginas de perfil devem responder em menos de 2 segundos sob carga normal de uso.
- **RNF03 - Segurança:** As senhas dos usuários devem ser armazenadas com criptografia forte e a comunicação deve utilizar HTTPS.
- **RNF04 - Confiabilidade:** O cálculo das médias deve ser exato e atualizado atomicamente a cada nova avaliação válida submetida.
- **RNF05 - Portabilidade:** A aplicação deve rodar de forma consistente em diferentes navegadores modernos.
