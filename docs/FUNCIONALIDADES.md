# Funcionalidades e regras de consulta

Este guia detalha as funcionalidades já disponíveis na `main`. O resumo das
entregas e do planejamento fica no
[README](https://github.com/unb-mds/2026-2-AvaliaAiUnB#funcionalidades-e-releases).

## Busca de professores e disciplinas

A página `/professores` aceita os filtros `nome`, `disciplina` e `departamento`
pela URL. Eles podem ser usados juntos. Nome do professor e nome ou código da
disciplina aceitam correspondência parcial; departamento exige igualdade
depois da normalização.

A normalização ignora acentos, maiúsculas e espaços extras. A lista é ordenada
pela quantidade de avaliações, com desempate por nome e identificador.
Essa ordenação é diferente do ranking, que usa a média das notas.

O departamento identifica a unidade que oferece a disciplina no SIGAA, e a
chave de professor é a combinação de nome e departamento. Um mesmo docente
pode aparecer em registros distintos quando leciona em unidades diferentes;
as médias e avaliações pertencem a cada registro.

## Perfil do professor e avaliações

O perfil `/professores/<professor_id>` mostra as disciplinas vinculadas e os
indicadores da disciplina selecionada. A URL pode informar `disciplina_id`.

Cada usuário autenticado pode registrar uma avaliação por combinação de
professor e disciplina, com notas inteiras de um a cinco para os cinco critérios:

| Critério | Interpretação |
|---|---|
| Didática | De muito ruim (1) a excelente (5) |
| Clareza | De muito ruim (1) a excelente (5) |
| Organização | De muito ruim (1) a excelente (5) |
| Disponibilidade | De muito ruim (1) a excelente (5) |
| Dificuldade | De muito fácil (1) a muito difícil (5); indica exigência |

Ano e período são obtidos da turma mais recente disponível para o par. Como
o semestre não faz parte da chave de unicidade da avaliação, a mesma conta
não pode criar outra avaliação para o mesmo par em um semestre diferente.

Uma avaliação só entra no cálculo das médias quando todos os cinco critérios
têm notas inteiras de um a cinco. Sem avaliações válidas, a página informa
essa condição e não atribui uma nota artificial.

## Perfil do usuário

A página `/perfil` exige login e lista as avaliações do próprio usuário.
Ele pode editar as notas e excluir suas avaliações. As consultas de médias
seguintes consideram as alterações.

A autoria é verificada com o identificador do usuário autenticado no backend.
Tentativas de editar ou excluir uma avaliação de outra pessoa recebem HTTP 404.

## Comparação de professores (RF08)

A página `/comparar` permite selecionar dois professores diferentes e consultar
lado a lado as médias de didática, clareza, organização, disponibilidade e
dificuldade, além da quantidade de avaliações válidas. Os parâmetros da URL são
`professor_1` e `professor_2`.

O acesso está disponível na lista e no perfil de cada professor. Os links
individuais já preenchem a primeira seleção.

As médias consideram todas as disciplinas e períodos, com o mesmo peso por
avaliação. Os dados são consultados a cada comparação e exibidos com duas casas
decimais. Professores sem avaliações válidas aparecem com um aviso.

## Ranking de professores (RF07)

A página `/ranking` mostra posição, média geral, quantidade de avaliações e
acesso ao perfil. Participam professores com pelo menos cinco avaliações válidas,
considerando todas as disciplinas e períodos.

A média geral é a soma das notas de didática, clareza, organização e
disponibilidade, dividida pelo número de avaliações válidas vezes quatro.
Dificuldade fica fora da média por medir exigência.

A ordem usa a média sem arredondamento, depois a quantidade de avaliações
(maior primeiro), o nome normalizado e o identificador. As posições são
sequenciais e a média exibida usa duas casas decimais.

O ranking consulta as avaliações a cada acesso, sem depender do cache do
catálogo. Se ninguém atingir o mínimo, a página informa esse estado.

## Funcionalidades planejadas

Filtros por faixa de nota e volume de avaliações, favoritos, gráficos,
comentários, denúncias e moderação ainda não têm fluxo implementado.

A [proposta de banco para comentários](https://github.com/unb-mds/2026-2-AvaliaAiUnB/blob/main/docs/Modelo%20de%20Dados.md#6-proposta-tabela-comentarios)
já está publicada. As regras de participação, quantidade, vínculo com a avaliação,
denúncia e privacidade serão especificadas e revisadas pelo grupo na
[issue #116](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/116).
