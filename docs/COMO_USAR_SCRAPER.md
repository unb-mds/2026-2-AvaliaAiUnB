# 🚀 Como Usar o Projeto

Este documento centraliza as instruções para configurar o ambiente, subir o banco de dados e executar o scraper.

## 1. Instalação de Dependências

Com o ambiente virtual (venv) ativado, instale as bibliotecas necessárias: 
pip install -r requirements-scraper.txt

```bash
pip install -r requirements.txt
```

## 2. Credenciais do Supabase

```
Acesse o painel do Supabase e vá em Project Settings > API.

Copie a Project URL (ex: https://xxxx.supabase.co).

Copie a chave service_role.

Crie um arquivo .env na pasta raiz do projeto, e coloque as credenciais dessa fora:

SUPABASE_URL=credencial1
SUPABASE_SERVICE_KEY=credencial2
```
## 2.1. Criando ou Recriando o Esquema do Banco no Supabase

Para configurar um projeto Supabase do zero (ou recriar o ambiente), execute a migração versionada no repositório:

1. Acesse o painel do seu projeto no [Supabase](https://supabase.com/dashboard).
2. No menu lateral esquerdo, clique em **SQL Editor** e depois em **New query**.
3. Copie todo o conteúdo do arquivo [`docs/migrations/001_initial_schema.sql`](migrations/001_initial_schema.sql) e cole no editor.
4. Clique em **Run** (ou pressione `Ctrl + Enter`). O script criará as tabelas (`professores`, `disciplinas`, `turmas`, `perfis`, `avaliacoes`), as constraints únicas usadas pelo scraper e a view `vw_professor_disciplina`.
5. Para validar se todas as tabelas foram criadas corretamente, execute localmente:
   ```bash
   python scraper/checar_tabelas.py

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
**professores que aparecem em mais de uma unidade**, útil para decidir a chave de
unicidade do professor.

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
