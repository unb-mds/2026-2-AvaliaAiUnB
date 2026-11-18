# Hospedagem e ambientes

O repositório já contém configuração para Vercel em `pyproject.toml`, com
`tool.vercel.entrypoint = "run:app"`. Este guia registra como configurar e
validar os ambientes dessa integração, acompanhada na issue #106.

## Registro do lançamento

| Item | Situação |
|---|---|
| Provedor configurado | Vercel |
| Aplicação | Flask, exposta como `app` no módulo `run.py` |
| Endereço público | [avaliaunb.com.br](https://avaliaunb.com.br/), conforme a página inicial da documentação |
| Endereço de staging | A URL oficial precisa ser confirmada no painel da Vercel |
| Data do lançamento | O histórico da publicação precisa ser conferido no painel da Vercel |

Para uma próxima publicação, registre a data e o horário planejados no fuso
de Brasília. O histórico no painel é a referência para a data efetiva.

## Configuração do projeto

No projeto Vercel vinculado a `unb-mds/2026-2-AvaliaUnB`, confira a raiz do
repositório e a detecção do backend Flask. O ponto de entrada configurado é
`run:app`; não é necessário iniciar `python run.py` como servidor da hospedagem.
A integração pode usar esse ponto de entrada de módulo, conforme o
[guia oficial de Flask na Vercel](https://vercel.com/kb/guide/ship-a-flask-app-on-vercel).

## Variáveis do ambiente

Em Settings → Environment Variables, configure os valores para os escopos
Preview e Production que forem usados. Uma alteração de variável vale para
novos deployments, exigindo nova publicação para produzir efeito.
[Referência da Vercel](https://vercel.com/docs/environment-variables).

| Variável | Configuração no projeto |
|---|---|
| `SECRET_KEY` | Chave privada aleatória, estável entre reinícios e com pelo menos 32 caracteres |
| `SUPABASE_URL` | URL do projeto Supabase destinado ao ambiente |
| `SUPABASE_SERVICE_KEY` | Chave de serviço do projeto correspondente, restrita ao servidor |
| `FLASK_DEBUG` | `0` em Preview e Production |
| `PROXY_HOPS` | Configurar conforme a quantidade de proxies confiáveis à frente do app; não presumir um valor sem conferir a topologia |
| `RATELIMIT_STORAGE_URI` | Opcional; definir armazenamento compartilhado quando necessário para que os contadores não fiquem separados por processo |

As duas últimas variáveis são usadas por `app/seguranca.py`. Sem configuração
de armazenamento compartilhado, o limite atual usa memória; esse comportamento
e os ajustes planejados estão descritos na [auditoria](AUDITORIA_SEGURANCA.md).

O `.env.example` contém apenas o formato local. Cadastre os valores reais no
ambiente da hospedagem. Para manter os dados de teste separados dos reais,
configure no Preview um projeto Supabase de testes; essa separação precisa ser
confirmada no ambiente, não é criada por esta documentação.

## Login com Google e URLs do Supabase Auth

O login com Google usa o provedor do próprio Supabase Auth (fluxo PKCE). O
client ID e o client secret do Google ficam **somente** no painel do Supabase
(Authentication → Sign In / Providers → Google). A aplicação e a Vercel não
precisam de variável nova.

Em Authentication → URL Configuration, em cada projeto Supabase:

| Campo | Valor |
|---|---|
| Site URL | `https://avaliaunb.com.br` (endereço público, nunca `localhost` em produção) |
| Redirect URLs | `https://avaliaunb.com.br/login/google/retorno` e, para desenvolvimento, `http://127.0.0.1:5000/login/google/retorno` |

Se o `redirect_to` enviado pela aplicação não estiver na lista, o Supabase usa
a Site URL; com uma Site URL `localhost`, o usuário volta para o `localhost`.
A aplicação monta o endereço de retorno com o host e o esquema da requisição,
então `PROXY_HOPS` precisa estar correto na Vercel para o endereço sair com
`https://`.

O login com Google é a única forma de entrada. Em Authentication → Sign In /
Providers → Email, desative "Allow new users to sign up" para que ninguém crie
conta por e-mail e senha diretamente na API do Supabase.

Quem tinha conta pelo antigo cadastro com senha e entra com o Google usando o
mesmo e-mail é vinculado pelo Supabase à mesma conta, com o mesmo perfil e as mesmas
avaliações. No primeiro acesso de uma conta nova, o perfil é criado com o nome
do Google e um nome de usuário derivado do e-mail.

## Verificação de e-mail

Aplique [`003_emails_verificados.sql`](migrations/003_emails_verificados.sql)
depois do esquema inicial. Configure `VERIFICACAO_EMAIL_ORIGEM` com o endereço
HTTPS do site naquele ambiente e use um provedor de e-mail com SMTP sobre TLS
na porta 465. Informe `VERIFICACAO_EMAIL_SMTP_HOST`,
`VERIFICACAO_EMAIL_SMTP_USUARIO`, `VERIFICACAO_EMAIL_SMTP_SENHA` e
`VERIFICACAO_EMAIL_REMETENTE` nas variáveis do ambiente. O remetente deve
estar autorizado pelo provedor. Use uma configuração separada no Preview e
confira a entrega do link e a confirmação com uma conta de teste.

A titularidade é registrada pelo fluxo do perfil e vale para o endereço
atual da conta. Os comentários implementados na
[#167](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/167) não usam essa
verificação: para comentar basta estar logado, porque o login é só pelo Google,
e o e-mail do autor nunca é exibido. O fluxo de verificação continua no projeto
(`app.verificacao_email.email_verificado(usuario)`), disponível para uma
decisão futura.

## Staging com Preview

Na integração Git, branches que não são a de produção podem gerar Previews.
Cada deployment recebe uma URL. Use o painel Deployments para abrir o Preview
escolhido e copie o endereço do aplicativo, distinguindo-o do endereço do painel
de administração. Uma URL de branch acompanha seu deployment mais recente;
uma URL de commit identifica uma versão específica.
[Referência dos ambientes](https://vercel.com/docs/deployments/environments).

Registre o endereço escolhido na tabela de lançamento. Confira se as pessoas
que vão validar o site conseguem acessá-lo, inclusive quando a proteção de
deployment da Vercel exige autenticação.

## Produção e data de lançamento

Confira em Settings → Environments qual branch está configurada como Production.
Na integração Git padrão, um merge nessa branch pode gerar publicação
automática. Escolher uma data na documentação não desativa essa automação.
Se for necessário controlar o momento exato, o responsável com acesso à Vercel
deve configurar e executar esse fluxo no painel antes do lançamento.
[Referência da integração Git](https://vercel.com/docs/git).

No horário definido, confirme a versão escolhida, as variáveis de Production
e o endereço que atenderá os usuários. O mecanismo de promoção ou nova
publicação deve ser o configurado no projeto. Registre depois a data real e
o endereço publicado, distinguindo-os da data inicialmente planejada.

## Validação do ambiente

Antes de considerar o endereço validado, confira com dados de teste:

1. Página inicial, busca, filtros e perfil do professor.
2. Login com Google (primeiro acesso e conta já existente), perfil do usuário e logout.
3. Criação, edição e exclusão de uma avaliação própria.
4. Médias, ranking, comparação e mensagens sem dados suficientes.
5. Formulários, cookies e navegação em HTTPS, com debug desligado.

Registre o ambiente, a versão e o resultado da conferência. Os testes e a
auditoria do código já existentes são referências complementares; um check de
build aprovado não substitui a validação dos fluxos no ambiente publicado.

Para abertura e conclusão de entregas, consulte
[Definition of Ready e Done](PROCESSO_CONTRIBUICAO.md). Veja ainda o
[pipeline de CI](pipeline.md), a [auditoria](AUDITORIA_SEGURANCA.md) e o
[guia de scraper](COMO_USAR_SCRAPER.md) para dependências de atualização do catálogo.
