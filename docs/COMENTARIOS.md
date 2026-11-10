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
| Quantidade | Um comentário por conta, professor e disciplina |
| Tamanho | Até 1.000 caracteres após remover espaços nas extremidades. O texto precisa ter conteúdo |
| Formato | Texto simples; HTML e Markdown não são interpretados |
| Identificação pública | Todo comentário publicado mostra o nome de usuário. Ao clicar nele, qualquer visitante pode consultar o e-mail verificado que o autor confirmou para divulgação |
| Ordem da lista | Mais recentes primeiro pela data de criação, com identificador como desempate |
| Datas | Exibir criação e indicar quando houve edição |

O backend deve validar as regras antes da gravação e escapar o texto na saída.
Um texto curto pode ser enviado. O servidor recusa o campo vazio ou preenchido
apenas com espaços, tabulações ou quebras de linha.

A autoria sempre vem da sessão autenticada. O servidor deve ignorar um
`usuario_id` enviado pelo formulário. O servidor valida o vínculo entre a
disciplina e o professor. Se a conta já tiver comentado nessa combinação,
o servidor orienta a editar o relato existente.
Na listagem pública, a API retorna só os campos de exibição e o ID do comentário.
O servidor usa o vínculo privado para indicar ao autor quais ações estão
disponíveis na sua sessão.

## Reações

Cada comentário publicado exibe **👍 Curtir** e **👎 Descurtir**, com contagens
separadas. A leitura das contagens é pública. Para reagir a um comentário de
outra pessoa, é preciso entrar na conta. Cada conta tem uma reação por
comentário e pode trocar de opção ou tocar novamente para removê-la. O servidor
confere a sessão, impede votos no próprio texto e grava a reação com unicidade
por conta e comentário. A lista mostra as contagens, sem revelar quem reagiu.
Reações não alteram a ordem cronológica da lista, as notas ou o ranking.

## Estrelas e comentários

Dar estrelas e escrever um comentário são ações independentes. A pessoa pode
usar só uma delas ou as duas na ordem que preferir. Para a mesma disciplina,
pode comentar primeiro e dar estrelas mais tarde, ou dar estrelas primeiro
e comentar depois. Cada ação tem seu próprio formulário e envio.

- Criar, editar ou excluir comentário não altera notas, médias ou ranking.
- Editar ou excluir uma avaliação não remove o comentário.
- Avaliação e comentário têm limites independentes de um registro por
  usuário, professor e disciplina.

## Fluxos para as telas da #112

### Listar e escrever

O perfil do professor apresenta os comentários publicados em uma seção
separada das notas. A lista vazia convida a escrever o primeiro comentário.
Visitantes veem a opção de entrar ou criar conta para escrever ou reagir.
Cada relato exibe sua disciplina. Quem já comentou pode editar o próprio
texto e escrever sobre outra disciplina do mesmo professor.

O formulário informa que o texto e o nome de usuário serão públicos. Antes
de publicar, a pessoa confirma que seu e-mail verificado ficará disponível
para quem clicar no nome de usuário.
Mostra o limite, exige a escolha de uma disciplina ministrada pelo professor
e preserva o texto em erros de validação ou moderação. Durante a
verificação, a interface evita envios repetidos e só confirma publicação
quando o texto fica público.

### Editar e excluir

A edição é exclusiva do autor, preserva a data original e atualiza `atualizado_em`.
O identificador do professor e a autoria não podem ser alterados pela edição.
A disciplina pode ser trocada por outra ministrada pelo mesmo professor
em que a conta ainda não comentou.

A exclusão deve pedir confirmação, identificando o professor, a disciplina
e a consequência. Depois de excluir, o texto e as reações saem da lista
e a conta pode voltar a comentar naquela disciplina.

### Conteúdo ocultado

Um comentário ocultado pela moderação deixa de aparecer na listagem pública.
O autor recebe o estado e a justificativa; editar o texto não o republica
automaticamente. Um comentário ocultado continua contando no limite da
disciplina, para evitar que a pessoa o substitua por um novo registro e
contorne a análise.
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
mantida para preservar os relatos históricos e suas regras de quantidade.
A proposta é guardar o registro mínimo da denúncia e
da decisão por até 90 dias após encerrar o caso e então apagar esse registro.
O texto excluído sai da listagem imediatamente. A definição da estrutura e da
rotina de descarte fica para a implementação após revisão do grupo.

## Decisões para o grupo revisar

| ID | Decisão proposta | Situação |
|---|---|---|
| C01 | Leitura pública e participação com conta comum e e-mail verificado de qualquer domínio. Sem espaço ou perfil exclusivo para professores | Aguardando revisão |
| C02 | Disciplina obrigatória. Uma pessoa pode escrever um comentário por disciplina ministrada pelo professor | Aguardando revisão |
| C03 | Texto simples de até 1.000 caracteres, com conteúdo obrigatório e sem mínimo de caracteres | Aguardando revisão |
| C04 | Estrelas e comentários são opcionais e independentes. A pessoa pode usar só uma opção ou ambas em qualquer ordem | Aguardando revisão |
| C05 | Nome de usuário em todos os comentários. E-mail verificado disponível ao clicar no nome, após confirmação do autor | Aguardando revisão do grupo antes da publicação no site |
| C06 | Denúncia privada e moderação por responsáveis autorizados | Aguardando revisão e projeto de dados |
| C07 | Ocultação motivada, sem republicação automática por edição | Aguardando revisão |
| C08 | Dois moderadores designados, primeira análise em até três dias úteis, formulário privado de contestação e retenção de até 90 dias após o encerramento | Aguardando revisão |
| C09 | Curtir ou descurtir comentários de outras pessoas. Uma reação por conta e comentário, com opção de trocar ou remover | Aguardando revisão |
| C10 | Filtrar no servidor antes de publicar ou editar. Bloquear violações claras e encaminhar casos incertos à moderação | Aguardando revisão |

As decisões podem ser revisadas no PR ou na
[issue #116](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/116).
Os [protótipos da #112](TELAS_COMENTARIOS.md) e a [proposta de dados da #109](Modelo%20de%20Dados.md#6-proposta-tabela-comentarios)
acompanham estas regras.

## Critérios para a futura implementação

- Visitantes consultam comentários com nome de usuário e contagens de
  reações. Entrar com conta verificada é obrigatório para comentar, reagir
  ou denunciar. O fluxo aceita, por exemplo, um e-mail Outlook ou de domínio
  próprio.
- Um texto curto como «Boa aula.» passa pela validação de tamanho. Campo
  vazio, só com espaços ou quebras de linha, e texto acima de 1.000 caracteres
  recebem erro claro.
- Duplicidade e disciplina ausente ou inválida recebem erro claro e
  preservam o texto preenchido.
- A mesma conta pode comentar Cálculo 1 e Cálculo 2 com o mesmo professor.
  Um segundo relato em Cálculo 1 é rejeitado, inclusive em envios simultâneos.
- Só o autor edita ou exclui. O servidor nega tentativas de se passar por outro
  usuário e mantém os identificadores de conta fora das respostas públicas.
- Clicar no nome de um comentário visível abre o e-mail verificado autorizado.
  O endereço fica fora da resposta da listagem e a consulta deixa de funcionar
  para aquele comentário se ele for ocultado ou excluído.
- Uma conta troca ou desfaz sua reação. Pedidos simultâneos respeitam a
  unicidade, e autores não reagem ao próprio comentário.
- O filtro barra uma ofensa inequívoca e a exposição de um telefone, deixa
  passar uma crítica respeitosa e encaminha um caso ambíguo sem publicar.
- O filtro também cobre edições. Falhas deixam o texto disponível para tentar
  de novo, e edições bloqueadas preservam a última versão aprovada.
- Uma conta autorizada a usar as duas ações consegue enviar só estrelas,
  publicar só um comentário ou fazer os dois em qualquer ordem.
- As notas e os resultados de ranking e comparação não mudam por um comentário.
- A identidade do denunciante e os dados privados não aparecem na listagem pública.
- As telas cobrem vazio, envio, erro, edição, confirmação de exclusão e ocultação.
- As permissões de backend e banco seguem o modelo aprovado, com testes de
  autorização e sem execução de migrações propostas durante a fase de documentação.
