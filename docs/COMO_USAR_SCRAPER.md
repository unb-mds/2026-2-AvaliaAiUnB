# Como executar o scraper do SIGAA

Este guia cobre a coleta do SIGAA e o preparo do banco. Para a atualização de cada
semestre, use o workflow do GitHub Actions descrito na
[seção 5](#5-atualizar-os-dados-a-cada-semestre-github-actions); as seções 1 a 4
explicam a execução local. Para iniciar a aplicação Flask, use o [README](https://github.com/unb-mds/2026-2-AvaliaUnB/blob/main/README.md); para o esquema, consulte o [modelo de dados](Modelo%20de%20Dados.md).

## 1. Instalação de Dependências

Com o ambiente virtual (venv) ativado, instale as bibliotecas do scraper.
O arquivo inclui também as dependências da aplicação:

```bash
pip install -r requirements-scraper.txt
```

## 2. Credenciais do Supabase

No painel do Supabase, consulte **Project Settings > API**. Crie um arquivo
`.env` na raiz a partir de `.env.example`, configure a URL e a chave de serviço
**apenas no servidor**; nunca adicione o `.env` ao Git:

```dotenv
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_KEY=chave-de-servico-do-projeto
```

A chave de serviço ignora RLS e só deve ser usada pelo scraper e por operações
administrativas estritamente necessárias. Veja [Cibersegurança](CIBERSEGURANCA.md).
## 2.1. Criando ou Recriando o Esquema do Banco no Supabase

Para configurar um projeto Supabase do zero (ou recriar o ambiente), execute a migração versionada no repositório:

1. Acesse o painel do seu projeto no [Supabase](https://supabase.com/dashboard).
2. No menu lateral esquerdo, clique em **SQL Editor** e depois em **New query**.
3. Copie todo o conteúdo do arquivo [`docs/migrations/001_initial_schema.sql`](migrations/001_initial_schema.sql) e cole no editor.
4. Clique em **Run** (ou pressione `Ctrl + Enter`). O script criará as tabelas (`professores`, `disciplinas`, `turmas`, `perfis`, `avaliacoes`), as constraints únicas usadas pelo scraper e a view `vw_professor_disciplina`.
5. Confira também as políticas RLS do SQL versionado e valide o ambiente de destino. Para verificar as tabelas, execute localmente:
   ```bash
   python scraper/checar_tabelas.py
   ```

## 3. Executando o scraper

> **Atualize o Chrome antes de rodar.** Por padrão, o `undetected_chromedriver` baixa
> o driver mais novo. Com o navegador desatualizado, o scraper falha ao abrir, com o erro
> `SessionNotCreatedException: This version of ChromeDriver only supports Chrome version N`.
> Se não puder atualizar, informe a versão principal do seu Chrome (em
> `chrome://version`) e, se quiser, o caminho do navegador:
>
> ```bash
> # Git Bash / Linux / macOS
> CHROME_VERSION_MAIN=157 python scraper/scraper_sigaa.py --dry-run
> # PowerShell
> $env:CHROME_VERSION_MAIN = "157"; python scraper/scraper_sigaa.py --dry-run
> ```
>
> | Variável | O que faz |
> |---|---|
> | `CHROME_VERSION_MAIN` | Baixa o driver dessa versão principal do Chrome (ex.: `157`). |
> | `CHROME_BINARY` | Caminho do navegador a abrir. Útil quando há mais de um Chrome/Chromium instalado. |

Rode a partir da raiz do projeto, com o ambiente virtual ativado:

```bash
python scraper/scraper_sigaa.py --dry-run                 # todas as unidades, 2026/2, sem gravar
python scraper/scraper_sigaa.py                           # todas as unidades, 2026/2, grava no Supabase
python scraper/scraper_sigaa.py --unidade 673             # só uma unidade (value do <option>)
python scraper/scraper_sigaa.py --unidade 673 --unidade 12
python scraper/scraper_sigaa.py --ano 2026 --periodo 1
```

| Opção | Padrão | O que faz |
|---|---|---|
| `--ano` | `2026` | Ano das turmas (4 dígitos). |
| `--periodo` | `2` | Período, de 1 a 4. |
| `--unidade` | todas | `value` do `<option>` da unidade de graduação. Pode ser repetida. |
| `--pausa` | `1` | Segundos de pausa entre unidades. |
| `--headless` | desligado | Roda o Chrome sem janela. |
| `--dry-run` | desligado | Mostra o que seria gravado, sem tocar no banco. |

### `--dry-run`

Não lê o `.env` e não grava nada. Além de professores, disciplinas e turmas, lista os
**professores que aparecem em mais de uma unidade**. No banco cada um deles vira um
registro só (veja abaixo).

### Professores em mais de uma unidade

O professor é único pelo **nome** (`UNIQUE (nome)`, migração
[`004_professores_unicos.sql`](migrations/004_professores_unicos.sql), issue #235). O
scraper junta os docentes repetidos de uma execução e grava a primeira unidade em que
cada um aparece. Quem já está no banco não é alterado (`ignore_duplicates`), então o
departamento não muda a cada unidade raspada. Depois do upsert, o scraper consulta os
ids pelo nome, em lotes de 100, para montar as turmas.

### Resumo e código de saída

Ao final, o scraper imprime um resumo: unidades lidas, unidades sem turmas (aviso),
unidades puladas por erro (com o motivo), linhas puladas por motivo e quantos
"A DEFINIR DOCENTE" foram ignorados.

Unidades cujo nome começa com `PROGRAMA DE PÓS-GRADUAÇÃO` são ignoradas (o scraper é só
de graduação) e listadas no resumo como "ignoradas (pós-graduação)". Isso vale também
quando o `value` é passado em `--unidade`, e não conta como erro nem muda o código de
saída. `DECANATO DE PÓS-GRADUAÇÃO / DPG` **não** é ignorado, porque a regra é só de prefixo.

- Saída `0`: nenhuma unidade falhou (unidade sem turmas é só aviso).
- Saída `1`: alguma unidade foi pulada por erro técnico, ou a lista de unidades não carregou.

### Pasta `debug/`

Em caso de falha (timeout, alerta de sessão, extração vazia) o scraper salva
screenshot e HTML da página em `debug/`, com a unidade no nome do arquivo. A pasta é
criada no diretório onde o comando foi executado e está no `.gitignore`.

### Paginação

A listagem do SIGAA vem inteira em uma página. Se o scraper detectar algum controle de
paginação, avisa no log e salva o HTML em `debug/`; nesse caso a extração leria só a
página atual, então avise a equipe.

## 4. Manutenção do banco

O script `scraper/manutencao_banco.py` usa o mesmo `.env` do scraper e tem dois
subcomandos. Rode-os da raiz do repositório.

### Verificar duplicatas

```bash
python scraper/manutencao_banco.py duplicatas
```

Só faz leitura. Compara nomes sem diferenciar acentos, caixa ou espaços e lista:

- professores com o mesmo nome;
- disciplinas com o mesmo código;
- disciplinas com o mesmo nome e códigos diferentes. Esse grupo é só informativo:
  são ofertas distintas de cada unidade (ex.: `FCE0006` e `FAR0248`, ambas
  HEMATOLOGIA CLÍNICA) e não contam como duplicata.

Sai com código `0` quando não há duplicatas e `1` quando há.

Se aparecerem professores duplicados, aplique (ou reaplique) a migração
[`004_professores_unicos.sql`](migrations/004_professores_unicos.sql) no SQL Editor do
Supabase. Ela junta os registros, leva turmas, avaliações e comentários para o
registro mantido, apaga os duplicados e cria a constraint `UNIQUE (nome)`. Tudo roda
numa transação e pode ser executado de novo sem efeito.

### Gerar backup

```bash
python scraper/manutencao_banco.py backup              # grava em docs/backup/
python scraper/manutencao_banco.py backup --destino pasta/
```

Gera `professores_rows.csv`, `disciplinas_rows.csv` e `turmas_rows.csv` no mesmo
formato do *Export to CSV* do Supabase. Só o catálogo público entra no backup.
Avaliações, comentários, perfis e e-mails verificados têm dados de usuários (LGPD) e
não vão para o repositório. Para restaurar, importe os CSVs pelo painel do Supabase
(*Table editor → Import data from CSV*), na ordem professores, disciplinas e turmas.

## 5. Atualizar os dados a cada semestre (GitHub Actions)

Este é o caminho recomendado para atualizar o catálogo. Ele roda o scraper numa
máquina do GitHub, sem precisar de Chrome, `.env` ou chave de serviço no computador
de quem executa. O workflow é
[`.github/workflows/atualizar-dados-sigaa.yml`](https://github.com/unb-mds/2026-2-AvaliaUnB/blob/main/.github/workflows/atualizar-dados-sigaa.yml)
e só é disparado manualmente.

### Quando rodar

- **No início de cada semestre**, depois que o SIGAA publicar as turmas do novo
  período. O calendário da UnB muda (greves, reposições), por isso o disparo é
  manual e não por data fixa.
- **De novo algumas semanas depois**, se quiser. A gravação é um *upsert*: não duplica
  nada e preenche professores que antes apareciam como "A DEFINIR DOCENTE". Turmas
  canceladas no SIGAA **não** são apagadas do banco.

### Configuração única (administrador do repositório)

Faça isto uma vez só; quem só vai rodar o workflow pode pular para o
[passo a passo](#passo-a-passo).

1. **Environment com aprovação.** Em *Settings → Environments → New environment*,
   crie o environment `producao`. Em *Deployment protection rules*, marque
   *Required reviewers* e escolha quem pode aprovar gravações no banco.
2. **Segredos.** Ainda no environment `producao`, em *Environment secrets*,
   adicione:
    - `SUPABASE_URL`: a URL do projeto (`https://<projeto>.supabase.co`);
    - `SUPABASE_SERVICE_KEY`: a chave `service_role` (*Project Settings → API* no
      Supabase).

    Cadastre as chaves **só no environment**, não em *Repository secrets*: assim
    apenas execuções aprovadas as recebem.
3. **Permissão para abrir PR.** Em *Settings → Actions → General → Workflow
   permissions*, marque *Allow GitHub Actions to create and approve pull requests*.
   Sem isso, a gravação funciona, mas o passo que abre o PR do backup falha.

!!! info "O workflow precisa estar na `main`"
    O GitHub só mostra o botão *Run workflow* para workflows que estão na branch
    padrão. Enquanto o arquivo existir só numa branch, ele não aparece na aba
    Actions.

### Passo a passo

**1. Dry-run (não grava nada).**

Na aba **Actions**, escolha **Atualizar dados do SIGAA** → **Run workflow** e preencha:

| Campo | Exemplo | Observação |
|---|---|---|
| `ano` | `2027` | Ano do semestre, com 4 dígitos. |
| `periodo` | `1` | Período (1 a 4; os semestres regulares são 1 e 2). |
| `modo` | `dry-run` | Padrão. Coleta e mostra o resultado, sem chaves e sem aprovação. |
| `unidades` | *(vazio)* | Vazio = todas. Para testar, use valores como `673` ou `673 12`. |

Pelo terminal, com o [GitHub CLI](https://cli.github.com/), o comando equivalente é:

```bash
gh workflow run atualizar-dados-sigaa.yml -R unb-mds/2026-2-AvaliaUnB \
  -f ano=2027 -f periodo=1 -f modo=dry-run
gh run watch -R unb-mds/2026-2-AvaliaUnB     # acompanha a execução
```

A coleta de todas as unidades pode levar dezenas de minutos.

**2. Conferir o resultado.**

Abra a execução. O **Summary** mostra o final do log, com o resumo do scraper:
unidades lidas, sem turmas e puladas por erro. O log completo, e a pasta `debug/`
se algo falhou, ficam no artifact **scraper-log**, disponível por 14 dias. Confira se:

- o número de unidades lidas e de turmas faz sentido para um semestre inteiro;
- não há unidades puladas por erro. Se houver, rode de novo só essas unidades no
  campo `unidades`.

**3. Gravar.**

Rode o workflow de novo com os mesmos `ano` e `periodo` e `modo` = `gravar`. A
execução fica parada em *Waiting* até um dos revisores do environment `producao`
clicar em **Review deployments → Approve and deploy**. Depois de aprovada, ela:

1. coleta e grava professores, disciplinas e turmas no Supabase;
2. roda `manutencao_banco.py duplicatas`. Se houver duplicatas, aparece um aviso
   amarelo na execução (veja [Verificar duplicatas](#verificar-duplicatas));
3. regenera os CSVs de `docs/backup` com `manutencao_banco.py backup`;
4. se o backup mudou, abre um PR `dados: backup do catálogo após coleta do SIGAA
   <ano>/<período>` a partir de uma branch `dados/sigaa-<ano>-<período>-<id>`.

**4. Revisar e mesclar o PR do backup.**

O banco já foi atualizado no passo 3; o PR só versiona os CSVs. PRs abertos pelo
`GITHUB_TOKEN` não disparam os outros workflows automaticamente. Como o PR só
altera CSVs, isso não atrapalha. Se a proteção da branch exigir checks, feche e
reabra o PR para dispará-los.

### Se algo der errado

| Sintoma | O que fazer |
|---|---|
| Execução vermelha com "unidades puladas por erro" | As unidades lidas **já foram gravadas**. Rode `gravar` de novo só com as unidades que falharam. |
| `SessionNotCreatedException` / versão do ChromeDriver | O workflow já define `CHROME_BINARY` e `CHROME_VERSION_MAIN` com o Google Chrome do runner (que também tem Chromium). Confira no passo "Apontar o scraper para o Google Chrome do runner" qual versão foi detectada e abra uma issue com o log. |
| Nenhuma turma em nenhuma unidade | Confira `ano`/`periodo`. O SIGAA pode ainda não ter publicado o período, ou o layout mudou (veja os HTMLs em `debug/` no artifact). |
| Passo "Abrir PR com o backup" falha | Falta a permissão do item 3 da [configuração única](#configuracao-unica-administrador-do-repositorio). Os dados já estão no banco. Rode o backup localmente (seção 4) ou ajuste a permissão e rode `gravar` de novo. |
| Aviso de duplicatas | Siga [Verificar duplicatas](#verificar-duplicatas). |

### Teste de fumaça em pull requests

O workflow
[`.github/workflows/scraper-fumaca.yml`](https://github.com/unb-mds/2026-2-AvaliaUnB/blob/main/.github/workflows/scraper-fumaca.yml)
roda em todo PR que altera `scraper/`, `requirements-scraper.txt` ou esses dois
workflows, e também pode ser disparado à mão. Ele faz um `--dry-run` só da unidade
`673` (FGA), com o ano e o período padrão de `scraper/cli_sigaa.py`, e falha se nenhuma
turma for extraída. Ele não usa chaves e serve para detectar, antes do merge, mudanças
no SIGAA ou dependências quebradas.

Ao trocar de semestre, atualize também os padrões de `--ano` e `--periodo` em
`scraper/cli_sigaa.py`. Senão o teste de fumaça continua consultando o semestre antigo.

### Segurança das chaves

- A chave de serviço existe só como *secret* do environment `producao`. Ela não fica
  no repositório nem nos logs: o GitHub mascara segredos na saída.
- O job de `dry-run` e o teste de fumaça não recebem nenhuma chave.
- Toda gravação no banco precisa de aprovação de um revisor e fica registrada na aba
  Actions, com quem disparou e quem aprovou.
- Os campos do formulário chegam ao script por variáveis de ambiente, e `unidades`
  aceita só números. Isso evita injeção de comandos pelo formulário.

Relacionado: [modelo de dados](Modelo%20de%20Dados.md), [backend](BACKEND.md) e [pipeline](pipeline.md).
