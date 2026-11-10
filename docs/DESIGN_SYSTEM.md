# Design system

Proposta da #112 para a aplicação AvaliaAi UnB. A paleta parte das telas atuais,
com Arial, fundo branco, texto escuro e links azuis. O padrão orienta os
protótipos de comentários e os ajustes da #114. O [inventário do frontend](FRONTEND.md)
registra os estilos que já existem no código.

## Cores

| Token | Valor | Uso |
|---|---|---|
| Superfície | `#FFFFFF` | Formulários, cards e diálogos |
| Fundo suave | `#F2F4F7` | Seções, cabeçalhos de tabela e mensagens informativas |
| Texto | `#202124` | Títulos, rótulos e texto principal |
| Texto secundário | `#4F5357` | Ajuda, detalhes e datas |
| Principal | `#174B83` | Links, foco e botões com texto branco |
| Principal em hover | `#123C69` | Botão principal sob o ponteiro |
| Borda de campo | `#767676` | Limite visível dos controles |
| Erro e ação destrutiva | `#A01818` | Mensagens de erro e botão de exclusão com texto branco |

O azul `#007BFF` da home atual tem contraste de 3,98:1 com branco.
Os protótipos usam `#174B83` para atender ao contraste de texto comum.

### Contraste

| Elemento | Par de cores | Relação |
|---|---|---|
| Texto | `#202124` e `#FFFFFF` | 16,10:1 |
| Texto secundário | `#4F5357` e `#FFFFFF` | 7,76:1 |
| Link ou botão principal | `#174B83` e `#FFFFFF` | 8,86:1 |
| Botão principal em hover | `#123C69` e `#FFFFFF` | 11,19:1 |
| Erro e ação destrutiva | `#A01818` e `#FFFFFF` | 7,96:1 |
| Borda de campo | `#767676` e `#FFFFFF` | 4,54:1 |
| Foco em superfície clara | `#174B83` e `#F2F4F7` | 8,04:1 |

A escala usa 4,5:1 como mínimo para texto comum e 3:1 para sinais visuais
necessários para identificar controles. No teclado, use um contorno de foco
de 2 px com distância de 2 px. A distância deixa o fundo aparecer entre botão
e contorno. Combine cores com rótulos ou ícones em erros, seleção e confirmação.
[Contraste de texto](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) ·
[Contraste de controles](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) ·
[Foco visível](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html)

## Tipografia e espaçamento

| Elemento | Tamanho | Peso e entrelinha |
|---|---|---|
| Título da página | `2rem` | 700 e 1,2 |
| Título de seção | `1.5rem` | 700 e 1,3 |
| Título de card | `1.25rem` | 700 e 1,3 |
| Texto e controles | `1rem` | 400 e 1,5. Botões usam peso 700 |
| Ajuda e metadados | `0.875rem` | 400 e 1,5 |

Use Arial com fallback `sans-serif` e espaçamentos de 4, 8, 12, 16, 24, 32 e
48 px. A área de conteúdo tem até 720 px e o formulário de autenticação, até
400 px. Use 16 px de margem lateral em mobile e 24 px em desktop. Campos e
botões têm altura mínima de 44 px e raio de 8 px. Cards e diálogos têm raio de
12 px. Em telas estreitas, empilhe controles e ações e preserve os cabeçalhos
das tabelas com rolagem horizontal quando necessário.

## Componentes e estados

| Componente | Comportamento | Estados |
|---|---|---|
| Botão principal | Azul, texto branco e uma ação principal por formulário | Padrão, hover, foco, desabilitado e envio |
| Botão secundário | Fundo branco, borda azul e rótulo Voltar ou Cancelar | Padrão, hover, foco e desabilitado |
| Botão destrutivo | Vermelho e texto branco na confirmação de exclusão | Padrão, foco e envio |
| Campo, seletor e área de texto | Rótulo visível, borda, ajuda e erro junto ao campo | Vazio, preenchido, foco, erro e desabilitado |
| Card de professor | Nome, departamento, disciplinas e ações | Padrão e resultado de filtro |
| Card de comentário | Texto, nome de usuário, data, disciplina e ações permitidas. O nome é um botão que abre ou fecha o e-mail do autor | Publicado, contato aberto, em edição e ocultado para o autor |
| Reação a comentário | Botões de polegar com rótulo Curtir ou Descurtir. Só contagens positivas aparecem. A seleção é anunciada com `aria-pressed` | Neutro, selecionado com ícone e cor, foco e envio |
| Mensagem | Explica o estado e a próxima ação | Informação, sucesso, erro, vazio e carregamento |
| Diálogo de exclusão | Identifica o item e sua consequência. Cancelar recebe o foco inicial | Aberto, confirmando e falha |
| Tabela de indicadores | Legenda, cabeçalhos associados e valores legíveis | Com dados, sem dados e erro |

Durante o envio, preserve o texto digitado, informe o progresso e evite envios
duplicados. Quando houver erro, devolva o controle ao usuário com a mensagem
visível. No estado vazio, informe se faltam dados ou se o filtro não encontrou
resultados. Ao fechar o diálogo de exclusão, devolva o foco ao contexto de origem.

Os [protótipos de comentários](TELAS_COMENTARIOS.md) mostram os fluxos de
listar, reagir, escrever, editar e apagar.
