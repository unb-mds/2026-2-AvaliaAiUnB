# Funcionalidades e regras de consulta

Este guia detalha as funcionalidades já disponíveis na `main`. O resumo das
entregas e do planejamento fica no
[README](https://github.com/unb-mds/2026-2-AvaliaUnB#funcionalidades-e-releases).

- **Política de Privacidade e Termos de Uso (`/privacidade`)**: página pública acessível pelo rodapé que descreve em linguagem simples os dados armazenados pelo AvaliaUnB (e-mail, nome de usuário, avaliações, comentários e formulário de feedback), as regras contra ofensas e avaliações falsas, e o canal de contato para solicitar a exclusão de dados em conformidade com a LGPD. Documentação detalhada em `docs/POLITICA-DE-PRIVACIDADE.md`.

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

## Comentários no perfil do professor

O perfil do professor tem uma seção **Comentários**, separada das notas.

- **Listagem:** mostra os 50 comentários mais recentes (ordem fixa: mais
  recentes primeiro) e avisa "Mostrando os 50 comentários mais recentes." quando
  há mais. O "ver mais" e a escolha da ordem (issue #213) ficam para depois.
- **Filtro:** o parâmetro `comentarios_disciplina` filtra por disciplina. Vazio ou
  inválido volta a "Todas as disciplinas", sem erro. Ele é independente do
  `disciplina_id`, que escolhe as médias.
- **Exibição:** cada comentário mostra o nome de usuário do autor (nunca o
  e-mail), a disciplina, a data em dd/mm/aaaa no horário de Brasília e
  "(editado)" quando a atualização é posterior à criação. O texto é simples,
  escapado, com as quebras de linha preservadas.
- **Publicar:** exige login (basta a conta Google; não se exige e-mail
  verificado). Texto de 2 a 1.000 caracteres e uma disciplina ministrada pelo
  professor. O autor vem da sessão. Há um limite de 10 comentários por hora por
  usuário, separado do das avaliações.
- **Editar e excluir:** só o autor, nas páginas `/comentarios/<id>/editar` e
  `/comentarios/<id>/excluir` (a exclusão passa por uma confirmação). O
  comentário de outra pessoa, ou inexistente, responde HTTP 404.
- Comentários não alteram notas, médias, comparação nem ranking.

Reações, denúncia, moderação, ocultação e filtro automático não fazem parte
desta entrega; veja as [regras dos comentários](COMENTARIOS.md).

## Perfil do usuário

A página `/perfil` exige login e lista as avaliações do próprio usuário.
Ele pode editar as notas e excluir suas avaliações. As consultas de médias
seguintes consideram as alterações.

A autoria é verificada com o identificador do usuário autenticado no backend.
Tentativas de editar ou excluir uma avaliação de outra pessoa recebem HTTP 404.

## Comparação de professores (RF08)

A página `/comparar` pede uma disciplina e permite selecionar dois ou mais
professores distintos que a ministram. Cada professor ocupa uma coluna com as
médias de didática, clareza, organização, disponibilidade e dificuldade e o
total de avaliações válidas na disciplina.

O acesso está disponível na lista e no perfil de cada professor. Os links
individuais preenchem a primeira seleção quando o professor ministra a
disciplina escolhida. A lista de professores selecionados pode ser ajustada
pelos botões **Adicionar professor** e **Remover professor**.

As médias consideram apenas a disciplina escolhida, com o mesmo peso por
avaliação válida em qualquer período. Os dados são consultados a cada
comparação e exibidos com duas casas decimais. Professores sem avaliações
válidas aparecem com um aviso. No celular, a tabela rola na horizontal e
mantém a coluna dos critérios visível.

Links antigos com `professor_1` e `professor_2` continuam mostrando as médias
gerais do par e oferecem acesso à comparação por disciplina.

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
reações, ordenação de comentários escolhida pela pessoa, filtro automático,
denúncias e moderação ainda não têm fluxo implementado.

A [proposta de banco para comentários](Modelo%20de%20Dados.md#6-proposta-tabela-comentarios)
já está publicada. A [especificação](COMENTARIOS.md) reúne nome de usuário
visível, reações, filtro e denúncias; o que ainda é proposta está indicado nela.
A proposta começou na
[issue #116](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/116).

Relacionado: [visão e requisitos](DOCUMENTO_DE_VISAO.md), [backend](BACKEND.md),
[frontend](FRONTEND.md) e [mapa da documentação](GUIA_DOCUMENTACAO.md).
