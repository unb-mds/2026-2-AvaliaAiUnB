# Especificação de comentários avaliativos

**Status: proposta para revisão do grupo, com origem na issue #116.** Este
documento descreve o comportamento futuro dos comentários, das reações e da
moderação.

A base é a [proposta de dados da #109](Modelo%20de%20Dados.md#6-proposta-tabela-comentarios).
O SQL dessa proposta permanece como referência e não é aplicado por este trabalho.

## Objetivo

Permitir relatos sobre a experiência pedagógica com um professor. O conteúdo
deve tratar de aspectos como didática, organização,
avaliação e disponibilidade, com contexto útil para outros estudantes.

## Quem pode consultar e participar

| Pessoa | Comportamento proposto |
|---|---|
| Visitante | Lê comentários publicados no perfil do professor |
| Usuário autenticado | Usa uma conta comum com e-mail verificado de qualquer domínio para comentar, reagir e denunciar |
| Autor | Edita ou exclui seu próprio comentário e acompanha sua análise em privado |
| Moderador autorizado | Analisa textos sinalizados e denúncias, com decisão e justificativa registradas |

O perfil do professor tem uma área de comentários sobre a experiência pedagógica.
A participação usa a mesma conta comum para todos, sem perfil docente, espaço
de resposta oficial ou selo de professor. O cadastro atual aceita Gmail. Para
liberar a área de comentários, o fluxo de cadastro e verificação deve aceitar
outros domínios e preservar as permissões das demais áreas, como o envio de notas.
Uma conta de comentários não concede acesso à moderação.

## Texto, quantidade e vínculo

| Regra | Proposta para revisão |
|---|---|
| Professor | Obrigatório e existente no catálogo |
| Disciplina | Obrigatória. Deve ter sido ministrada pelo professor |
| Quantidade | Sem limite por conta, inclusive para o mesmo professor e disciplina |
| Tamanho | De 2 a 1.000 caracteres após remover espaços, tabulações e quebras de linha das extremidades |
| Formato | Texto simples; HTML e Markdown não são interpretados |
| Identificação pública | Todo comentário publicado mostra o nome de usuário. Ao clicar nele, qualquer visitante pode consultar o e-mail verificado que o autor confirmou para divulgação |
| Ordem da lista | Mais recentes por padrão. A pessoa pode escolher Mais curtidos, Mais antigos ou Mais reações |
| Datas | Exibir a data da primeira publicação em cada comentário e indicar quando houve edição |

O backend deve validar as regras antes da gravação e escapar o texto na saída.
Um texto curto como «ok» passa pela validação de tamanho. O servidor recusa
o texto que fica com menos de dois caracteres depois de remover os espaços
em branco das extremidades.

A autoria sempre vem da sessão autenticada. O servidor deve ignorar um
`usuario_id` enviado pelo formulário. O servidor valida o vínculo entre a
disciplina e o professor.
Na listagem pública, a API retorna só os campos de exibição e o ID do comentário.
O servidor usa o vínculo privado para indicar ao autor quais ações estão
disponíveis na sua sessão.

## Reações

Os ícones **👍** e **👎** ficam sempre visíveis em cada comentário para
qualquer visitante. Cada ícone exibe seu total quando houver reações
daquele tipo. Os nomes das ações ficam disponíveis para leitores de tela.
Para reagir a um comentário de outra pessoa, é preciso entrar na conta.
Cada conta tem uma reação por comentário e pode trocar de opção ou tocar
novamente para removê-la. O servidor
confere a sessão, impede votos no próprio texto e grava a reação com unicidade
por conta e comentário. A lista mostra as contagens, sem revelar quem reagiu.
Reações podem mudar a posição de um comentário nas ordenações por curtidas
ou reações. As notas e o ranking são independentes.

## Ordenação dos comentários

| Opção | Como a lista é ordenada |
|---|---|
| Mais recentes | Primeira publicação mais recente primeiro. É a ordem padrão |
| Mais curtidos | Maior quantidade de curtidas primeiro |
| Mais antigos | Primeira publicação mais antiga primeiro |
| Mais reações | Maior soma de curtidas e descurtidas primeiro |

Em empate por curtidas ou reações, o comentário mais recente vem primeiro.
Se dois comentários tiverem a mesma data e hora de publicação, o
identificador desempata na mesma direção da ordenação por data. Editar um comentário
preserva sua data original.

## Estrelas e comentários

Dar estrelas e escrever um comentário são ações independentes. A pessoa pode
usar só uma delas ou as duas na ordem que preferir. Para a mesma disciplina,
pode comentar primeiro e dar estrelas mais tarde, ou dar estrelas primeiro
e comentar depois. Cada ação tem seu próprio formulário e envio.

- Criar, editar ou excluir comentário não altera notas, médias ou ranking.
- Editar ou excluir uma avaliação não remove o comentário.
- Cada estudante pode registrar uma avaliação por estrelas para cada par
  de professor e disciplina. Pode avaliar o mesmo professor em Cálculo 1
  e Cálculo 2. Para mudar a nota de Cálculo 1, edita a avaliação existente.
  A pessoa pode publicar vários comentários para a mesma disciplina.

## Fluxos para as telas da #112

### Listar e escrever

O perfil do professor apresenta os comentários publicados em uma seção
separada das notas. A lista vazia convida a escrever o primeiro comentário.
Visitantes veem a opção de entrar ou criar conta para escrever ou reagir.
Cada relato exibe sua disciplina. Quem já comentou pode editar os próprios
textos e escrever outro relato para a mesma disciplina ou para outra
ministrada pelo professor.

O formulário informa que o texto e o nome de usuário serão públicos. Antes
de publicar, a pessoa confirma que seu e-mail verificado ficará disponível
para quem clicar no nome de usuário.
Mostra o limite, exige a escolha de uma disciplina ministrada pelo professor
e preserva o texto em erros de validação ou moderação. Durante a
verificação, a interface desabilita o botão de envio e só confirma a
publicação quando o texto fica público.

### Editar e excluir

A edição é exclusiva do autor, preserva a data original e atualiza `atualizado_em`.
O identificador do professor e a autoria não podem ser alterados pela edição.
A disciplina pode ser trocada por outra ministrada pelo mesmo professor.

A exclusão deve pedir confirmação, identificando o professor, a disciplina
e a consequência. Depois de excluir, o texto e as reações daquele
comentário saem da lista.

### Conteúdo ocultado

Um comentário ocultado pela moderação deixa de aparecer na listagem pública.
O autor recebe o estado e a justificativa. A edição continua privada até a
decisão da moderação. Qualquer novo relato passa pelo filtro antes da
publicação.
O autor pode pedir revisão pelo formulário privado descrito abaixo.

## Filtro automático antes da publicação

O backend verifica comentários novos e edições antes de disponibilizá-los.
A proposta começa com regras em português para ofensas, discriminação,
ameaças, spam e dados pessoais, como e-mails, telefones e matrículas. O filtro
normaliza espaços e variações de escrita para reconhecer tentativas simples de
disfarçar termos. Uma crítica à didática ou uma avaliação negativa, por si só,
deve passar.

| Resultado | Comportamento |
|---|---|
| Aprovado | Publica o texto ou aplica a edição |
| Bloqueado | Mostra o motivo ao autor e mantém o texto no formulário para revisão |
| Incerto | Encaminha o texto para análise privada e informa ao autor que está em revisão |
| Filtro indisponível | Mantém o texto no formulário e pede nova tentativa sem publicar |

Uma edição bloqueada ou em análise preserva a última versão aprovada de um
comentário publicado. Se o comentário já estiver oculto, a edição continua
privada até decisão da moderação. O filtro e a denúncia cumprem papéis
complementares, pois uma regra automática pode deixar passar conteúdo impróprio.

## Denúncia e moderação

Proposta de fluxo:

1. Um usuário autenticado denuncia um comentário, selecionando motivo e, se
   necessário, acrescentando uma explicação.
2. O sistema confirma o recebimento sem expor a identidade do denunciante ao
   autor ou a visitantes. Uma denúncia ativa por usuário e comentário evita
   duplicação; a regra precisa ser refletida no futuro modelo.
3. Um moderador autorizado consulta texto, motivo e contexto e registra a
   decisão de manter, ocultar ou restaurar, com justificativa.
4. O autor pode pedir revisão em um formulário privado associado ao comentário.
   O pedido fica visível ao autor e aos moderadores designados.

Os motivos propostos são ofensa ou ataque pessoal, exposição de dados pessoais,
discriminação, ameaça, spam ou conteúdo alheio à experiência pedagógica.
Uma avaliação negativa ou discordância com a opinião não são, por si só,
motivos para remoção. O número de denúncias não oculta automaticamente o texto.

A [proposta de banco](Modelo%20de%20Dados.md) descreve a proteção das tabelas
de comentários e reações. A implementação futura precisa definir o registro
privado das análises e denúncias e revisar as permissões de moderação,
inclusive o uso de service key descrito em [Cibersegurança](CIBERSEGURANCA.md).
A proposta operacional é que o grupo designe dois moderadores antes de liberar
comentários e use três dias úteis como meta para a primeira análise. Sempre
que possível, outra pessoa moderadora analisa a contestação. Se ninguém puder
atender a fila, a publicação de novos comentários fica pausada até haver cobertura.

## Privacidade e ciclo dos dados

Cada comentário publicado mostra o nome de usuário da conta. Ao clicar ou
tocar nesse nome, o visitante pode consultar o e-mail verificado autorizado
para divulgação. O endereço é carregado só quando solicitado e fica fora da
resposta da listagem. O servidor entrega o endereço apenas enquanto o
comentário estiver público e a divulgação daquele endereço estiver autorizada.
Uma troca de e-mail exige nova confirmação antes de exibir o novo endereço.

Um endereço acessível a visitantes pode ser copiado ou coletado mesmo quando
aparece só após um clique. Antes de liberar essa consulta no site, o grupo
deve revisar a necessidade de expor o e-mail de cadastro e o aviso apresentado
ao autor. Nome completo, tokens, dados de denúncias e identificadores internos
da conta ficam privados.

A orientação ao autor deve pedir que não publique matrículas, contatos,
documentos, informações pessoais de terceiros ou relatos que exponham pessoas
sem necessidade. O acesso às denúncias e aos registros de moderação deve ficar
restrito aos responsáveis autorizados. Logs operacionais não devem copiar
indiscriminadamente o texto ou dados pessoais.

As cascatas propostas na #109 apagam comentários quando o perfil do autor ou o
professor é excluído. Uma disciplina com comentários vinculados deve ser
mantida para preservar o vínculo dos relatos históricos.
A proposta é guardar o registro mínimo da denúncia e
da decisão por até 90 dias após encerrar o caso e então apagar esse registro.
O texto excluído sai da listagem imediatamente. A definição da estrutura e da
rotina de descarte fica para a implementação após revisão do grupo.

## Decisões para o grupo revisar

| ID | Decisão proposta | Situação |
|---|---|---|
| C01 | Leitura pública e participação com conta comum e e-mail verificado de qualquer domínio. Sem espaço ou perfil exclusivo para professores | Aguardando revisão |
| C02 | Disciplina obrigatória. A pessoa pode comentar quantas vezes quiser para o mesmo professor e disciplina | Aguardando revisão |
| C03 | Texto simples de 2 a 1.000 caracteres após remover espaços em branco das extremidades | Aguardando revisão |
| C04 | Estrelas e comentários são independentes e podem ser enviados em qualquer ordem. Uma avaliação por estrelas por estudante, professor e disciplina | Aguardando revisão |
| C05 | Nome de usuário em todos os comentários. E-mail verificado disponível ao clicar no nome, após confirmação do autor | Aguardando revisão do grupo antes da publicação no site |
| C06 | Denúncia privada e moderação por responsáveis autorizados | Aguardando revisão e projeto de dados |
| C07 | Ocultação motivada, sem republicação automática por edição | Aguardando revisão |
| C08 | Dois moderadores designados, primeira análise em até três dias úteis, formulário privado de contestação e retenção de até 90 dias após o encerramento | Aguardando revisão |
| C09 | Ícones 👍 e 👎 sempre visíveis, com números apenas nas reações recebidas. Uma reação por conta e comentário, com opção de trocar ou remover | Aguardando revisão |
| C10 | Filtrar no servidor antes de publicar ou editar. Bloquear violações claras e encaminhar casos incertos à moderação | Aguardando revisão |
| C11 | Data em cada comentário. Ordenação por Mais recentes, Mais curtidos, Mais antigos ou Mais reações | Aguardando revisão |

As decisões podem ser revisadas no PR ou na
[issue #116](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/116).
Os [protótipos da #112](TELAS_COMENTARIOS.md) e a [proposta de dados da #109](Modelo%20de%20Dados.md#6-proposta-tabela-comentarios)
acompanham estas regras.

## Critérios para a futura implementação

- Visitantes consultam comentários com nome de usuário e contagens de
  reações. Entrar com conta verificada é obrigatório para comentar, reagir
  ou denunciar. O fluxo aceita, por exemplo, um e-mail Outlook ou de domínio
  próprio.
- «ok» passa pela validação de tamanho. Campo vazio, texto com menos de
  dois caracteres após retirar os espaços em branco das extremidades e
  texto acima de 1.000 caracteres recebem erro claro.
- Disciplina ausente ou inválida recebe erro claro e preserva o texto
  preenchido.
- A mesma conta pode publicar dois relatos distintos em Cálculo 1 com o
  mesmo professor. Cada relato tem seu próprio texto, reações e ações de
  editar ou apagar.
- Só o autor edita ou exclui. O servidor nega tentativas de se passar por outro
  usuário e mantém os identificadores de conta fora das respostas públicas.
- Clicar no nome de um comentário visível abre o e-mail verificado autorizado.
  O endereço fica fora da resposta da listagem e a consulta deixa de funcionar
  para aquele comentário se ele for ocultado ou excluído.
- Uma conta troca ou desfaz sua reação. Pedidos simultâneos respeitam a
  unicidade, e autores não reagem ao próprio comentário.
- A lista exibe a data e os dois ícones em cada comentário, inclusive para
  visitantes sem login e com o e-mail recolhido.
  Os números aparecem só para reações recebidas.
  Com 8 curtidas e 1 descurtida, o comentário aparece com 8 e 1 separados.
  Na opção Mais reações, as duas contagens somam 9 para a ordenação.
- Com 3 curtidas e nenhuma descurtida, a lista exibe 👍 3 e 👎 sem número.
  Sem nenhuma reação, aparecem só os dois ícones.
- Mais recentes abre por padrão. Mais curtidos ordena apenas pelas
  curtidas, e Mais antigos inverte a ordem por data. A edição preserva
  a posição nas duas ordens por data.
- O filtro barra uma ofensa inequívoca e a exposição de um telefone, deixa
  passar uma crítica respeitosa e encaminha um caso ambíguo sem publicar.
- O filtro também cobre edições. Falhas deixam o texto disponível para tentar
  de novo, e edições bloqueadas preservam a última versão aprovada.
- Uma conta autorizada a usar as duas ações consegue enviar só estrelas,
  publicar só um comentário ou fazer os dois em qualquer ordem.
- A mesma conta pode avaliar com estrelas Cálculo 1 e Cálculo 2 com o mesmo
  professor. Uma segunda avaliação por estrelas em Cálculo 1 é recusada.
- As notas e os resultados de ranking e comparação não mudam por um comentário.
- A identidade do denunciante e os dados privados não aparecem na listagem pública.
- As telas cobrem vazio, envio, erro, edição, confirmação de exclusão e ocultação.
- As permissões de backend e banco seguem o modelo aprovado, com testes de
  autorização e sem execução de migrações propostas durante a fase de documentação.

Documentos relacionados: [modelo de dados](Modelo%20de%20Dados.md),
[protótipos](TELAS_COMENTARIOS.md), [frontend](FRONTEND.md) e
[cibersegurança](CIBERSEGURANCA.md). A execução depende de decisões
registradas em issue/PR; este arquivo não ativa um sistema de comentários.
