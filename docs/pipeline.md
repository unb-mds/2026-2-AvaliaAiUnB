# Pipeline (GitHub Actions)

Na `main`, os workflows ficam em `.github/workflows/`: `testes.yml`,
`seguranca.yml`, `docs.yml`, `scraper-fumaca.yml` e `atualizar-dados-sigaa.yml`. Uma validação do MkDocs em PR foi proposta
separadamente na [issue #171](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/171);
ela só passa a integrar a `main` após o respectivo PR ser mesclado.

<div class="grid cards" markdown>

- :material-check-circle-outline: **Testes**

    ---

    Roda os testes automatizados em todo pull request e em todo push na main.

- :material-shield-bug-outline: **Segurança**

    ---

    Roda o pip-audit (procura vulnerabilidades nas dependências) e o bandit (analisa o código Python). Por enquanto eles só avisam e não bloqueiam o merge. O relatório da auditoria está publicado em [Auditoria](AUDITORIA_SEGURANCA.md)
e as correções são acompanhadas em [Cibersegurança](CIBERSEGURANCA.md).

- :material-book-open-page-variant-outline: **Documentação**

    ---

    Quando alguém altera a pasta `docs/` ou o `mkdocs.yml` na main, o site da documentação é publicado automaticamente. Não precisa mais rodar `mkdocs gh-deploy` na mão.

- :material-spider-web: **Scraper (teste de fumaça)**

    ---

    `scraper-fumaca.yml`: em PRs que alteram o `scraper/`, roda o scraper em `--dry-run` para uma unidade, sem chaves, e falha se nenhuma turma for extraída.

- :material-database-sync-outline: **Atualizar dados do SIGAA**

    ---

    `atualizar-dados-sigaa.yml`: só roda quando alguém dispara pela aba Actions. Faz o dry-run ou, com aprovação no environment `producao`, grava o semestre no Supabase e abre um PR com o backup. Veja o [passo a passo](COMO_USAR_SCRAPER.md#5-atualizar-os-dados-a-cada-semestre-github-actions).

</div>

## Como ver o resultado dos testes

Para ver o resultado, abra o pull request e olhe a seção de checks no final da página. Se ficar vermelho, clique em "Details" para ver qual teste falhou.

!!! info "Política de merge"
    A execução de um workflow não garante que ele seja obrigatório pela proteção
    de branch. Confirme a lista de checks exigidos nas regras atuais do GitHub.
    Nos workflows de segurança, `pip-audit` e `bandit` têm `continue-on-error`,
    então um status verde pode coexistir com avisos desses scanners.

Veja também: [critérios DoR/DoD](PROCESSO_CONTRIBUICAO.md),
[mapa da documentação](GUIA_DOCUMENTACAO.md) e [hospedagem](HOSPEDAGEM.md).