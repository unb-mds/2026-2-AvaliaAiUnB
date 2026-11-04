# AvaliaAi UnB

Plataforma de consulta, comparação e avaliação de professores e disciplinas
da Universidade de Brasília.

## Documentação

| Assunto | Referência |
|---|---|
| Produto e requisitos | [Documento de visão](DOCUMENTO_DE_VISAO.md) |
| Funcionalidades | [Busca, avaliações, comparação e ranking](FUNCIONALIDADES.md) |
| Backend | [Estrutura, rotas, sessões e repositórios](BACKEND.md) |
| Frontend | [Templates, estilos, estados e contribuição](FRONTEND.md) |
| Dados | [Modelo de dados e proposta de comentários](Modelo%20de%20Dados.md) |
| Arquitetura | [Diagramas do sistema](ARQUITETURA.md) |
| Coleta | [Guia do scraper](COMO_USAR_SCRAPER.md) |
| Segurança | [Mecanismos e correções](CIBERSEGURANCA.md) · [Auditoria de 02/11/2026](AUDITORIA_SEGURANCA.md) |
| Comentários | [Especificação proposta para revisão](COMENTARIOS.md) |
| Qualidade e publicação | [Pipeline do GitHub Actions](pipeline.md) |
| Design | [Board do Figma](https://www.figma.com/board/PgqkPopVXOiSqm9gD5RRNv/AvaliaAi---Template-MDS?node-id=0-1&p=f&t=Rxu6jVCgeVZHCyg2-0) |

## Funcionalidades disponíveis

O fluxo essencial inclui cadastro, login, busca, perfil do professor, avaliações
por cinco critérios e consulta das médias. A Release 2 já acrescenta ranking,
comparação entre dois professores, filtro por departamento, busca que ignora
acentos e espaços extras e gestão das próprias avaliações em `/perfil`.

Filtros por faixa de nota e volume de avaliações, favoritos, gráficos,
comentários, denúncias e moderação continuam planejados. Consulte as
[regras das funcionalidades](FUNCIONALIDADES.md) e o
[resumo das releases no README](https://github.com/unb-mds/2026-2-AvaliaAiUnB#funcionalidades-e-releases).

## Como rodar o projeto localmente

Use Python 3.11 ou superior:

```bash
git clone https://github.com/unb-mds/2026-2-AvaliaAiUnB.git
cd 2026-2-AvaliaAiUnB
python -m venv .venv
```

Ative o ambiente com `.\.venv\Scripts\Activate.ps1` no PowerShell ou
`source .venv/bin/activate` no Linux/macOS. Instale as dependências com
`pip install -r requirements.txt`.

Copie `.env.example` para `.env` na raiz e preencha `SECRET_KEY`, `SUPABASE_URL`
e `SUPABASE_SERVICE_KEY`. Gere uma chave privada e estável com
`python -c "import secrets; print(secrets.token_hex(32))"`.
O `.env` é ignorado pelo Git. O debug fica desligado por padrão;
`FLASK_DEBUG=1` deve ser usado somente no desenvolvimento local.

A preparação do banco está no [guia do scraper](COMO_USAR_SCRAPER.md).
A reprodução do RLS na migração está em correção na
[issue #123](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/123).

Execute `python run.py` e acesse `http://127.0.0.1:5000`.

## Docker e hospedagem

Com Docker, Docker Compose e o `.env` configurados, execute
`docker compose up --build`. A aplicação será servida pelo Gunicorn em
`http://localhost:8000`. O scraper é executado separadamente.

A [issue #106](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/106) está
concluída e a `main` contém configuração para Vercel. Falta registrar o link
do staging, a data de produção e as instruções do ambiente.

## Testes e documentação

Execute `python -m unittest discover -s tests -t .` na raiz. A suíte usa um
cliente Supabase falso e dispensa credenciais reais e Chrome.

Instale `mkdocs-material` no ambiente virtual para editar este site. Execute
`mkdocs serve` para visualizar e `mkdocs build --strict` para validar a geração.
Na `main`, mudanças em `docs/` ou `mkdocs.yml` disparam a publicação no GitHub Pages.
O [guia do pipeline](pipeline.md) explica os checks e a publicação.

## Comentários e revisão do grupo

A [especificação de comentários](COMENTARIOS.md) propõe participação, limites,
relação com as avaliações, denúncia, moderação e privacidade, a partir do
[modelo de dados](Modelo%20de%20Dados.md). O documento ainda aguarda revisão do
grupo; esta entrega não implementa comentários nem aplica o SQL proposto.

## Alinhamentos para concluir as issues #115 e #116

Situação consultada em **03/11/2026**:

| Parte | Disponível | Complemento necessário |
|---|---|---|
| Hospedagem — #106, caiionog | Issue concluída e configuração para Vercel no PR #131 | Registrar link de staging, data de produção e instruções do ambiente |
| Modelo — #109, caiionog | Documento do esquema e SQL proposto de comentários | Alinhar com o grupo as escolhas da proposta e atualizar o modelo após aprovação |
| Segurança — #111, gsm22 | Relatório e plano de correção publicados | Atualizar a documentação conforme as correções forem entregues; a auditoria já pode ser documentada |
| Design system — #112, giiicostaa | Inventário do frontend atual documentado | Incorporar os valores e componentes aprovados na #112 |
| Comentários — #116, Geovanaduartee e grupo | Especificação proposta e pontos de decisão C01 a C08 | Revisar as regras, definir responsáveis de moderação, canal de revisão e retenção |

A #112 depende da especificação da #116 para desenhar comentários. A revisão
das regras pode avançar agora, sem aguardar as telas futuras.
