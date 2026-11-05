# Especificação de comentários avaliativos

**Status: proposta para revisão do grupo na issue #116.** Este documento define
o comportamento futuro; comentários e denúncias ainda não foram implementados.
A aprovação deve ser registrada no PR ou na issue antes de tratar as regras
como decisões finais. A implementação não faz parte desta entrega.

A base é a [proposta de dados da #109](Modelo%20de%20Dados.md#6-proposta-tabela-comentarios).
O SQL dessa proposta permanece como referência e não é aplicado por este trabalho.

## Objetivo

Permitir relatos sobre a experiência pedagógica com um professor, complementando
as notas objetivas. O conteúdo deve tratar de aspectos como didática, organização,
avaliação e disponibilidade, com contexto útil para outros estudantes.

## Quem pode consultar e participar

| Pessoa | Comportamento proposto |
|---|---|
| Visitante | Lê comentários publicados no perfil do professor |
| Usuário autenticado | Publica um comentário por professor, edita e exclui o próprio comentário e denuncia conteúdo |
| Autor | Vê o próprio texto e as datas de criação e atualização; alterações de autoria são bloqueadas |
| Moderador autorizado | Analisa denúncias e oculta ou restaura conteúdo, com justificativa registrada |

O usuário comum não pode editar, excluir nem moderar comentários de outra pessoa.
O papel de moderador e o fluxo de denúncia ainda precisam de desenho de dados e
controle de acesso; não existem no esquema atual. Cadastrar uma conta não deve
conceder acesso à moderação.

## Texto, quantidade e vínculo

| Regra | Proposta para revisão |
|---|---|
| Professor | Obrigatório e existente no catálogo |
| Disciplina | Opcional; quando selecionada, deve estar vinculada ao professor |
| Quantidade | Um comentário por usuário e professor, mesmo que o usuário avalie várias disciplinas |
| Tamanho | De 10 a 1.000 caracteres após remover espaços nas extremidades, conforme o `btrim` e o `char_length` da proposta de banco |
| Formato | Texto simples; HTML e Markdown não são interpretados |
| Identificação pública | Nome de usuário (`username`), sem nome completo, e-mail ou identificador interno |
| Ordem da lista | Mais recentes primeiro pela data de criação, com identificador como desempate |
| Datas | Exibir criação e indicar quando houve edição |

O backend deve validar as regras antes da gravação e escapar o texto na saída.
Espaços ou quebras de linha não devem ser usados para contornar o limite mínimo
de conteúdo. A interpretação exata de texto composto só por espaços deve ser
alinhada com a constraint do banco durante a futura implementação.

A autoria sempre vem da sessão autenticada. O servidor deve ignorar um
`usuario_id` enviado pelo formulário. A tentativa de criar um segundo comentário
para o mesmo professor deve orientar o autor a editar o comentário existente.

## Relação entre avaliação e comentário

A proposta mantém comentário e avaliação como registros independentes,
conforme o desenho inicial da #109:

- Não é obrigatório ter enviado notas antes de comentar.
- Criar, editar ou excluir comentário não altera notas, médias ou ranking.
- Editar ou excluir uma avaliação não remove o comentário.
- Uma avaliação permanece única por usuário, professor e disciplina; o
  comentário permanece único por usuário e professor.

Exigir avaliação prévia é uma alternativa que o grupo pode aprovar. Nesse caso,
será preciso definir qual avaliação habilita o comentário e o que acontece
quando ela é excluída, além de ajustar a validação e a proposta de dados.

## Fluxos para as telas da #112

### Listar e escrever

O perfil do professor deve apresentar os comentários publicados e um estado
vazio quando não houver nenhum. O visitante vê a orientação para entrar na
conta antes de escrever. O usuário autenticado sem comentário vê o formulário;
quem já comentou vê a ação de editar o próprio texto.

O formulário informa o limite, oferece seleção opcional de disciplina e preserva
o texto em erros de validação. Em caso de falha de envio, não deve indicar que
o comentário foi publicado. O estado de envio deve evitar submissões repetidas.

### Editar e excluir

A edição é exclusiva do autor, preserva a data original e atualiza `atualizado_em`.
O identificador do professor e a autoria não podem ser alterados pela edição.
A disciplina opcional pode ser ajustada dentro dos vínculos do mesmo professor.

A exclusão deve pedir confirmação, identificando o professor e a consequência.
Depois de excluir, o texto deixa de aparecer e o usuário pode criar um novo
comentário para esse professor. A exclusão do texto e a retenção de registros de
moderação são decisões distintas; o grupo precisa definir a segunda antes de
implementar a moderação.

### Conteúdo ocultado

Um comentário ocultado pela moderação deixa de aparecer na listagem pública.
O autor recebe o estado e a justificativa; editar o texto não o republica
automaticamente. A unicidade por usuário e professor continua valendo para
evitar substituir o texto ocultado por um novo registro e contornar a análise.
O grupo deve definir um canal de revisão da decisão.

## Denúncia e moderação

Proposta de fluxo:

1. Um usuário autenticado denuncia um comentário, selecionando motivo e, se
   necessário, acrescentando uma explicação.
2. O sistema confirma o recebimento sem expor a identidade do denunciante ao
   autor ou a visitantes. Uma denúncia ativa por usuário e comentário evita
   duplicação; a regra precisa ser refletida no futuro modelo.
3. Um moderador autorizado consulta texto, motivo e contexto e registra a
   decisão de manter, ocultar ou restaurar, com justificativa.
4. O autor pode solicitar revisão pelo canal que o grupo definir.

Os motivos propostos são ofensa ou ataque pessoal, exposição de dados pessoais,
discriminação, ameaça, spam ou conteúdo alheio à experiência pedagógica.
Uma avaliação negativa ou discordância com a opinião não são, por si só,
motivos para remoção. O número de denúncias não oculta automaticamente o texto.

A [proposta de banco](Modelo%20de%20Dados.md) ainda não contém armazenamento de
denúncias, estado de moderação nem permissões de moderador. A implementação
futura precisa acrescentar esses elementos e revisar políticas de acesso,
inclusive o uso de service key descrito em [Cibersegurança](CIBERSEGURANCA.md).
Responsáveis, prazo de análise e canal de revisão ficam pendentes da decisão do grupo.

## Privacidade e ciclo dos dados

A interface deve informar que o texto e o nome de usuário propostos serão
públicos antes da publicação. Não deve exibir nome completo, e-mail, tokens,
dados de denúncias ou identificadores internos na listagem.

A orientação ao autor deve pedir que não publique matrículas, contatos,
documentos, informações pessoais de terceiros ou relatos que exponham pessoas
sem necessidade. O acesso às denúncias e aos registros de moderação deve ficar
restrito aos responsáveis autorizados. Logs operacionais não devem copiar
indiscriminadamente o texto ou dados pessoais.

As cascatas propostas na #109 apagam comentários quando o perfil do autor ou o
professor é excluído. Ao excluir a disciplina, o vínculo passa a ser nulo,
preservando o comentário. O prazo de retenção e o destino de denúncias e
registros de moderação precisam de definição própria; este documento não
presume que esses dados serão guardados indefinidamente.

## Decisões para o grupo revisar

| ID | Decisão proposta | Situação |
|---|---|---|
| C01 | Leitura pública e participação autenticada | Aguardando revisão |
| C02 | Um comentário por usuário e professor; disciplina opcional | Aguardando revisão |
| C03 | Texto simples de 10 a 1.000 caracteres | Aguardando revisão |
| C04 | Comentário independente de avaliação prévia | Aguardando revisão |
| C05 | Autor identificado publicamente apenas por username | Aguardando revisão |
| C06 | Denúncia privada e moderação por responsáveis autorizados | Aguardando revisão e projeto de dados |
| C07 | Ocultação motivada, sem republicação automática por edição | Aguardando revisão |
| C08 | Responsáveis, prazo de análise, canal de revisão e retenção | A definir pelo grupo |

As decisões podem ser revisadas no PR ou na
[issue #116](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/116).
Após a aprovação, atualizar este documento, a proposta da #109 e os desenhos
da #112 para refletirem as mesmas regras.

## Critérios para a futura implementação

- Visitantes consultam comentários publicados e precisam entrar para participar.
- Duplicidade, limites de texto e disciplina inválida recebem erro claro e
  preservam o texto preenchido.
- Só o autor edita ou exclui; o usuário de teste não altera o comentário de outro.
- As notas e os resultados de ranking e comparação não mudam por um comentário.
- A identidade do denunciante e os dados privados não aparecem na listagem pública.
- As telas cobrem vazio, envio, erro, edição, confirmação de exclusão e ocultação.
- As permissões de backend e banco seguem o modelo aprovado, com testes de
  autorização e sem execução de migrações propostas durante a fase de documentação.
