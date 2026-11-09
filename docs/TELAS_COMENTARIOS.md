# Telas de comentários

Protótipos da #112 para revisar a experiência em uma tela estreita. Os fluxos
seguem a [especificação da #116](COMENTARIOS.md) e os componentes do
[design system](DESIGN_SYSTEM.md). Os nomes e textos das telas são exemplos.

## Listar

![Perfil com comentários, autoria, disciplina e ações de editar, apagar e denunciar](mockups/comentarios/listar.svg)

Visitantes veem os comentários publicados e um convite para entrar. A sessão
do autor mostra Editar e Apagar no próprio comentário. Para quem está autenticado
e ainda não escreveu sobre o professor, a lista oferece Escrever comentário.
Em uma lista vazia, o texto orienta como escrever o primeiro comentário.

## Escrever

![Formulário para escrever com disciplina opcional, contador e aviso de visibilidade](mockups/comentarios/escrever.svg)

O formulário exibe o limite e a visibilidade antes de Publicar. Durante o envio,
a ação muda para Publicando e fica desabilitada. Em caso de erro, mantém o
conteúdo digitado e mostra a causa junto ao campo ou no início do formulário.

## Editar

![Formulário de edição com texto preservado e mensagem de erro de comprimento](mockups/comentarios/editar.svg)

O autor edita o texto e a disciplina dentro dos vínculos do professor. O exemplo
mostra o estado de texto curto. Após salvar, volta para a lista com confirmação
e indicação de que o comentário foi editado.

## Apagar

![Diálogo com a consequência da exclusão e Cancelar em foco](mockups/comentarios/apagar.svg)

O diálogo indica qual comentário será afetado e oferece Cancelar antes de
Apagar comentário. Após confirmar, a lista é atualizada e o foco retorna a uma
ação visível. Em falha, o diálogo mantém o contexto e permite tentar novamente.

## Denúncia e ocultação

A ação Denunciar abre um formulário com motivo obrigatório e explicação
opcional. A confirmação de recebimento fica visível à pessoa que denunciou.
A identidade de quem enviou a denúncia fica no fluxo privado de moderação.
O autor vê a justificativa quando seu comentário é ocultado e pode pedir revisão
no canal descrito na [especificação](COMENTARIOS.md).
