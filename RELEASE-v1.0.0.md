# Release Notes – v1.0.0 | AvaliaAi UnB

Nesta primeira versão do AvaliaAi, focamos em entregar a estrutura inicial para que os estudantes da UnB possam acessar a plataforma de forma segura e consultar as informações consolidadas sobre os professores e disciplinas.

## Novidades
* O aluno consegue criar uma conta e realizar o login seguro na plataforma.
* O usuário consegue visualizar as médias dos professores organizadas por disciplina.
* O aluno consegue navegar no sistema tanto pelo computador quanto pelo celular, graças aos ajustes de responsividade da interface.
* Qualquer usuário consegue ler a documentação do projeto e o Documento de Visão acessando nossa página pública gerada via GitHub Pages (MkDocs).

## Limitações conhecidas
* O sistema de banco de dados ainda é local (SQLite). A persistência definitiva em nuvem com PostgreSQL será integrada na próxima atualização.
* O scraper (extrator de dados) do SIGAA ainda não está ativo para alimentar as turmas automaticamente.
* Funcionalidades avançadas previstas para o futuro, como ranking de professores, comparação direta entre docentes e moderação de avaliações, não estão disponíveis nesta versão.

## Como rodar
Para testar a aplicação localmente, certifique-se de ter o Python instalado e execute os comandos abaixo na raiz do projeto:

1. Instale as dependências necessárias:
`pip install -r requirements.txt`

2. Inicie o servidor:
`python run.py`

3. Acesse no navegador o endereço local (geralmente `http://127.0.0.1:5000/`).

## Issues entregues

**Sprint 2:**
* #04 
* #14 
* #15 
* #16 

**Sprint 3:**
* #24 
* #25 
* #26 
* #27 
* #28 
* #29 
* #30 
* #31 
* #32 
* #33 
* #34 
* #35 
* #36 
* #37 
* #38 
* #39 
* #40 
* #41 
* #42 
* #43 
* #44 
