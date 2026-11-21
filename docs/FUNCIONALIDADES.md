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

O seletor **Departamento** é preenchido com os departamentos distintos do
catálogo completo, em ordem alfabética. Substitui os atalhos fixos de áreas.
O botão **Filtrar departamento** combina a seleção com a pesquisa atual e
reinicia a paginação. A busca também preserva o departamento selecionado.
**Todos os departamentos** remove somente esse filtro; **Limpar filtros**
restaura a consulta completa. Os formulários funcionam sem JavaScript.

Em cada cartão da lista, cada disciplina mostra a dificuldade média e a
quantidade de avaliações daquela disciplina, ou "Sem avaliações ainda" quando
não há nenhuma. A dificuldade usa a mesma regra da página do professor. As
disciplinas do cartão aparecem com as avaliadas primeiro (a mais avaliada antes)
e depois as sem avaliações, com desempate por nome. Até 5 disciplinas aparecem
todas; com mais de 5, aparecem 4 e as demais ficam em "Ver mais N disciplinas"
dentro do cartão. Nenhuma disciplina deixa de aparecer. O botão Comentários do
cartão leva à seção de comentários do perfil.

O departamento identifica a unidade que oferece a disciplina no SIGAA, e a
chave de professor é a combinação de nome e departamento. Um mesmo docente
pode aparecer em registros distintos quando leciona em unidades diferentes;
as médias e avaliações pertencem a cada registro.

### Busca unificada com autocompletar

Um único campo aceita nome do professor, disciplina (nome ou código) ou
departamento, com as mesmas regras de normalização. Na Consulta, o termo vai
para `/professores?q=`; ao digitar, as sugestões aparecem com o tipo indicado
(Professor, Disciplina ou Departamento) e levam ao perfil do professor ou à
Consulta filtrada pela disciplina ou pelo departamento. Na Comparação, as
sugestões são só de professores e disciplinas e já abrem a comparação com a
seleção feita. Busca por ementa ou por turma não faz parte da funcionalidade.

## Perfil do professor e avaliações

O perfil `/professores/<professor_id>` mostra as disciplinas vinculadas e os
indicadores da disciplina selecionada. A URL pode informar `disciplina_id`.
O topo do perfil tem um link Comentários que pula para a seção de comentários,
e a tela de avaliar uma nova avaliação tem uma linha convidando a comentar, com
link para essa seção, fora do formulário de notas.

Cada usuário autenticado pode registrar uma avaliação por combinação de
professor e disciplina, com notas inteiras de um a cinco para os cinco critérios:

| Critério | Interpretação |
|---|---|
| Didática | De muito ruim (1) a excelente (5) |
| Clareza | De muito ruim (1) a excelente (5) |
| Organização | De muito ruim (1) a excelente (5) |
| Disponibilidade | De muito ruim (1) a excelente (5) |
| Dificuldade | De muito fácil (1) a muito difícil (5); indica exigência |

### Turma (semestre) cursada (issue #252)

- **A pessoa escolhe a turma.** O formulário de avaliação tem o campo **Turma
  cursada**, com os semestres em que o professor deu aquela disciplina (vindos do
  SIGAA pelo scraper, em `turmas`). Cada turma é a combinação professor +
  disciplina + semestre: o código de turma do SIGAA não é gravado, então dois
  horários do mesmo professor na mesma disciplina e semestre contam como uma turma.
  O padrão é a turma mais recente que a pessoa ainda não avaliou; um link de
  avaliar com `?semestre=2025-2` já vem com essa turma marcada.
- **Uma avaliação por semestre cursado.** A restrição única de `avaliacoes` é
  `(usuario_id, professor_id, disciplina_id, ano, periodo)` (migração
  [`007_avaliacao_por_semestre.sql`](migrations/007_avaliacao_por_semestre.sql)).
  Quem cursou a mesma disciplina com o mesmo professor duas vezes pode avaliar as
  duas turmas. Turmas já avaliadas aparecem riscadas como "já avaliada"; quando
  todas foram avaliadas, a tela leva ao perfil para editar.
- **Validação no backend:** o semestre precisa ser de uma turma do professor na
  disciplina (senão HTTP 400) e não pode repetir uma avaliação da pessoa (HTTP
  409). A restrição do banco também recusa envios simultâneos.
- **Clientes sem o campo** (`semestre` ausente no POST) continuam funcionando como
  antes: a avaliação vai para a turma mais recente.
- **Edição:** mostra a turma ("Turma de 2026/1"), mas não permite trocá-la; para
  mudar o semestre, a pessoa exclui e avalia de novo.

### Médias: todos os semestres ou um semestre

- O **topo do perfil** (nota grande e estrelas) é sempre a média de todas as
  avaliações do professor, em todos os semestres e disciplinas.
- Em **Médias Consolidadas**, o padrão **Todos** é a média de todas as avaliações
  da disciplina escolhida. Os botões de semestre (parâmetro `semestre=2026-2`)
  mostram só as avaliações daquela turma; o resumo indica o recorte
  ("CÁLCULO 1 · 2025/2 · 3 avaliações"). Semestre inválido volta para Todos. Os
  botões só aparecem quando a disciplina tem mais de uma turma.
- O botão **Avaliar este Professor** leva o semestre filtrado para o formulário.

Uma avaliação só entra no cálculo das médias quando todos os cinco critérios
têm notas inteiras de um a cinco. Sem avaliações válidas, a página informa
essa condição e não atribui uma nota artificial.

### Evolução por semestre (RF12)

Abaixo das médias, a seção **Evolução por semestre** mostra um gráfico de linha
com a média do professor em cada semestre, somando todas as disciplinas. O
semestre é a turma cursada que a pessoa escolheu ao avaliar. Avaliações feitas
antes da #252 ficaram com a turma mais recente do par na época (todas as
avaliações de produção até 21/11/2026 estão em 2026/2).

- **Critério:** os botões trocam o que o gráfico mostra (parâmetro
  `evolucao_criterio`): média geral (padrão; média dos quatro critérios, sem a
  dificuldade, como no topo do perfil) ou um dos cinco critérios. Valor
  desconhecido volta para a média geral.
- **Escala fixa de 1 a 5**, para não exagerar pequenas variações. O gráfico mostra
  os 6 semestres mais recentes; a tabela mostra todos.
- **Alternativa em texto:** o SVG tem título e descrição (do primeiro ao último
  semestre), cada ponto mostra semestre, média e número de avaliações ao passar o
  mouse, e "Ver os dados em tabela" lista todos os semestres e critérios.
- **Estado vazio:** com avaliações de um só semestre, ou nenhuma, a seção mostra
  uma mensagem no lugar do gráfico.
- Só avaliações válidas entram, pela mesma regra das médias. O SVG é gerado no
  servidor (`app/grafico.py` calcula as coordenadas; o template desenha) e usa
  apenas classes CSS (`evolucao.css`), sem JavaScript nem `style` inline, por
  causa da CSP.

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

### Professores favoritos (RF11)

No perfil do professor, quem está logado usa o botão **Favoritar** para salvar
o professor numa lista pessoal; o mesmo botão passa a mostrar **Favorito ·
remover** para desfazer. Visitantes veem um link para entrar. A seção
**Favoritos** do `/perfil` lista os professores salvos (mais recentes primeiro),
com link para o perfil e botão para remover. A lista é visível apenas para o
dono. Os dados ficam na tabela `favoritos`
([modelo de dados](Modelo%20de%20Dados.md#8-professores-favoritos-favoritos)).

## Comparação de professores (RF08)

A página `/comparar` oferece dois modos de comparação:

- **Por mesma disciplina (padrão):** pede uma disciplina e permite selecionar
  dois ou mais professores distintos que a ministram, exibindo as médias
  restritas àquela disciplina.
- **Disciplinas diferentes (`modo=livre`):** permite selecionar livremente
  dois ou mais professores de qualquer disciplina para comparar a média geral
  (média de didática, clareza, organização e disponibilidade) e cada critério
  individual. Quando os professores não possuem disciplina em comum, a tela
  lista as disciplinas de cada docente e exibe um aviso indicando que as
  disciplinas são diferentes.

O acesso está disponível na lista e no perfil de cada professor. Os links
individuais preenchem a primeira seleção automaticamente e direcionam para a
comparação por disciplina (quando há outro docente na mesma matéria) ou para a
seleção livre. A lista de professores selecionados pode ser ajustada pelos
botões **Adicionar professor** e **Remover professor**.

As médias consideram apenas a disciplina escolhida, com o mesmo peso por
avaliação válida em qualquer período. Os dados são consultados a cada
comparação e exibidos com duas casas decimais. Professores sem avaliações
válidas aparecem com um aviso. No celular, a tabela rola na horizontal e
mantém a coluna dos critérios visível.
Para evitar distorções por amostras pequenas, apenas professores com pelo menos
cinco avaliações válidas são elegíveis ao destaque visual na comparação. Entre
os elegíveis, o sistema destaca o melhor desempenho geral (média de didática,
clareza, organização e disponibilidade) e o melhor resultado em cada critério:
nos quatro primeiros critérios vence a maior média, enquanto em **Dificuldade**
aplica-se a regra inversa (vence a menor média). Em caso de empate na liderança,
todos os professores empatados recebem o destaque.

Links antigos com `professor_1` e `professor_2` continuam mostrando as médias
gerais do par e oferecem acesso à comparação por disciplina.

## Ranking de professores (RF07)

## Ranking de professores (RF07)

A página `/ranking` mostra posição, média geral, quantidade de avaliações e
acesso ao perfil. Por padrão exibe o ranking geral, mas aceita o parâmetro
`departamento` (via seletor na tela ou pela URL) para filtrar a classificação
por unidade acadêmica, mantendo a exigência de pelo menos cinco avaliações
válidas.

A média geral é a soma das notas de didática, clareza, organização e
disponibilidade, dividida pelo número de avaliações válidas vezes quatro.
Dificuldade fica fora da média por medir exigência.

A ordem usa a média sem arredondamento, depois a quantidade de avaliações
(maior primeiro), o nome normalizado e o identificador. As posições são
sequenciais e a média exibida usa duas casas decimais.

O ranking consulta as avaliações a cada acesso, sem depender do cache do
catálogo. Se ninguém atingir o mínimo, a página informa esse estado.

## Funcionalidades planejadas

Filtros por faixa de nota e volume de avaliações, outros gráficos,
reações, ordenação de comentários escolhida pela pessoa, filtro automático,
denúncias e moderação ainda não têm fluxo implementado.

A [proposta de banco para comentários](Modelo%20de%20Dados.md#6-proposta-tabela-comentarios)
já está publicada. A [especificação](COMENTARIOS.md) reúne nome de usuário
visível, reações, filtro e denúncias; o que ainda é proposta está indicado nela.
A proposta começou na
[issue #116](https://github.com/unb-mds/2026-2-AvaliaUnB/issues/116).

Relacionado: [visão e requisitos](DOCUMENTO_DE_VISAO.md), [backend](BACKEND.md),
[frontend](FRONTEND.md) e [mapa da documentação](GUIA_DOCUMENTACAO.md).
