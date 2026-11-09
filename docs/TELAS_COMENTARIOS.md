# Telas de comentários

Protótipos da #112 para revisar a experiência em uma tela estreita. Os fluxos
seguem a [especificação da #116](COMENTARIOS.md) e os componentes do
[design system](DESIGN_SYSTEM.md). Os nomes e textos das telas são exemplos.
O perfil de professor organiza os relatos em uma seção própria, ao lado das
notas.

## Listar

![Perfil com comentários anônimos, contagens de reações e ações de editar, apagar e denunciar](mockups/comentarios/listar.svg)

Visitantes leem os comentários anônimos e suas contagens. A área convida a
entrar ou criar conta com qualquer e-mail verificado para escrever ou reagir.
A pessoa logada que ainda não comentou vê **Escrever comentário**. O autor vê
**Editar** e **Apagar** somente no próprio comentário. Na lista vazia, a seção
convida a escrever o primeiro relato.

Os polegares mostram as contagens de **Curtir** e **Descurtir** nos comentários
de outras pessoas. A reação selecionada tem cor e marca de confirmação. É
possível trocar a reação ou desfazê-la com outro toque. Se a sessão não estiver
ativa, tocar no botão leva ao login sem gravar voto.

## Escrever

![Formulário com disciplina opcional, contador e aviso de publicação anônima com verificação automática](mockups/comentarios/escrever.svg)

O formulário avisa que o texto será público, a autoria ficará privada e o
conteúdo passará por verificação. Durante o envio, o botão mostra
**Verificando**. Se o filtro bloquear o texto, a mensagem junto ao campo
explica o que precisa ser revisto e preserva o que foi digitado. Se a análise
precisar de moderação, a confirmação informa **Em revisão** e o texto fica
privado até a decisão.

## Editar

![Formulário de edição com texto preservado e alerta do filtro sobre um e-mail no texto](mockups/comentarios/editar.svg)

O autor edita o texto e a disciplina dentro dos vínculos do professor. O
exemplo mostra uma edição bloqueada pelo filtro. A última versão aprovada
continua visível até uma nova versão passar pela verificação. Após uma edição
aprovada, a lista indica que o comentário foi editado.

## Apagar

![Diálogo com a consequência da exclusão e Cancelar em foco](mockups/comentarios/apagar.svg)

O diálogo avisa que o texto e as reações serão apagados e oferece Cancelar
antes de Apagar comentário. Após confirmar, a lista é atualizada e o foco retorna a uma
ação visível. Em falha, o diálogo mantém o contexto e permite tentar novamente.

## Denúncia e ocultação

A ação Denunciar abre um formulário com motivo obrigatório e explicação
opcional. A confirmação de recebimento fica visível à pessoa que denunciou.
A identidade de quem enviou a denúncia fica no fluxo privado de moderação.
O autor vê a justificativa quando seu comentário é ocultado e pode pedir revisão
no canal descrito na [especificação](COMENTARIOS.md).
