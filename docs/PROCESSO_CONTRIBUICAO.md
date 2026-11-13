# Critérios de contribuição: Definition of Ready e Done

Critérios de equipe para manter issues revisáveis e entregas verificáveis.
O escopo exato pode variar entre código, documentação e pesquisa.

## Definition of Ready (DoR)

Uma issue está **pronta para iniciar** quando:

- [ ] O objetivo e o problema estão descritos em termos claros.
- [ ] Há critérios de aceite observáveis e um resultado esperado.
- [ ] O escopo está delimitado, incluindo o que não será feito.
- [ ] Dependências, arquivos/serviços afetados e responsáveis estão identificados.
- [ ] Há informação suficiente para implementar ou pesquisar sem inventar requisitos.
- [ ] Riscos relevantes (dados, segurança, compatibilidade, deploy) estão anotados.
- [ ] A estimativa e a prioridade foram alinhadas pela equipe, quando aplicável.

Se alguma dependência bloquear a entrega, marque a issue como bloqueada e
registre qual decisão ou PR é necessário antes de prosseguir.

## Definition of Done (DoD)

Uma entrega está **concluída** quando:

- [ ] Os critérios de aceite da issue foram verificados e eventuais exceções
      têm justificativa registrada.
- [ ] Alterações são pertinentes ao escopo e passaram por revisão de outra pessoa.
- [ ] Testes pertinentes foram adicionados/ajustados e executados; failures e
      limitações ficaram explícitos no PR.
- [ ] Documentação, links e exemplos foram atualizados quando necessário.
- [ ] Não há credenciais, dados pessoais, artefatos locais ou arquivos gerados
      indevidamente no commit.
- [ ] O PR explica a mudança, referencia a issue e descreve as validações.
- [ ] Checks exigidos e build aplicável passaram antes do merge.
- [ ] Alterações que dependem de banco/ambiente têm migrações, permissões e
      configuração revisadas e validadas no ambiente apropriado.
- [ ] O PR foi mesclado de acordo com o fluxo do grupo e a issue foi encerrada
      com rastreabilidade para a entrega, quando aplicável.

## Verificações por tipo de alteração

| Tipo | Validação principal |
|---|---|
| Backend e autenticação | `python -m unittest discover -s tests -t .` e cenários de acesso autorizado/negado |
| Frontend | Testes pertinentes, acessibilidade básica e conferência em telas estreitas |
| Banco e RLS | Revisão do SQL, papéis `anon`/`authenticated` e testes com usuários diferentes |
| Scraper | Testes isolados e `--dry-run` sem gravar no Supabase |
| Documentação | `mkdocs build --strict`, índice e links relativos |
| Deploy | Checks, variáveis e verificação de fluxos no ambiente correspondente |

Consulte também o [mapa da documentação](GUIA_DOCUMENTACAO.md) e o
[guia do pipeline](pipeline.md).
