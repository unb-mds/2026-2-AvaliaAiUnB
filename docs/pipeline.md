# Pipeline (GitHub Actions)

O projeto usa três workflows, que ficam em `.github/workflows/`.

<div class="grid cards" markdown>

- :material-check-circle-outline: **Testes**

    ---

    Roda os testes automatizados em todo pull request e em todo push na main.

- :material-shield-bug-outline: **Segurança**

    ---

    Roda o pip-audit (procura vulnerabilidades nas dependências) e o bandit (analisa o código Python). Por enquanto eles só avisam e não bloqueiam o merge. Os resultados serão tratados na auditoria de segurança.

- :material-book-open-page-variant-outline: **Documentação**

    ---

    Quando alguém altera a pasta `docs/` ou o `mkdocs.yml` na main, o site da documentação é publicado automaticamente. Não precisa mais rodar `mkdocs gh-deploy` na mão.

</div>

## Como ver o resultado dos testes

Para ver o resultado, abra o pull request e olhe a seção de checks no final da página. Se ficar vermelho, clique em "Details" para ver qual teste falhou.

!!! info "Checks obrigatórios"
    Só o check "Testes" é obrigatório para fazer merge. Os de segurança passam a ser obrigatórios depois da auditoria.