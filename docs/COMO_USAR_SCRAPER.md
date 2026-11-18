# Como executar o scraper do SIGAA

Este guia cobre a coleta do SIGAA e o preparo do banco. Para iniciar a aplicação Flask, use o [README](https://github.com/unb-mds/2026-2-AvaliaUnB/blob/main/README.md); para o esquema, consulte o [modelo de dados](Modelo%20de%20Dados.md).

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

> **Atualize o Chrome antes de rodar.** O `undetected_chromedriver` usa o driver
> compatível com o Chrome instalado; com o navegador desatualizado o scraper falha
> ao abrir (erro de versão do ChromeDriver).

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

Relacionado: [modelo de dados](Modelo%20de%20Dados.md), [backend](BACKEND.md) e [pipeline](pipeline.md).
