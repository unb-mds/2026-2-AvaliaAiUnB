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

No projeto Vercel vinculado a `unb-mds/2026-2-AvaliaAiUnB`, confira a raiz do
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
2. Cadastro, login, perfil do usuário e logout.
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
