# Design system

Proposta da #112 para a aplicação AvaliaUnb. A paleta parte das telas atuais e
hoje existe em dois temas: o **escuro**, que é o padrão, e o **claro**, com
texto escuro sobre fundo claro e o azul `#174b83` como cor principal. A fonte
é a Inter, hospedada no próprio site. O padrão orienta os
protótipos de comentários e os ajustes da #114. O [inventário do frontend](FRONTEND.md)
registra os estilos que já existem no código.

Os tokens e os componentes compartilhados ficam em `app/static/base.css`. As
telas o carregam diretamente ou por meio de `indicadores.css` (`@import`). Os
comentários têm folha própria, `app/static/comentarios.css`, que usa só esses
tokens.

## Temas

O tema escuro é o padrão e vale quando o `<html>` não tem o atributo
`data-theme`. O tema claro é ativado por `data-theme="light"` no `<html>`.
Cada tema declara `color-scheme` (`dark` no `:root` e `light` em
`:root[data-theme="light"]`), para que controles nativos e barras de rolagem
acompanhem o tema.

A escolha é feita pelo botão de tema no topo (`.botao-tema`, em
`app/templates/_topo.html`) e tratada por `app/static/tema.js`:

- a escolha fica em `localStorage`, na chave `tema`, com os valores `claro` ou
  `escuro`. Sem valor salvo, vale o escuro;
- o acesso ao `localStorage` fica dentro de `try/catch`; se o armazenamento
  estiver indisponível, a escolha vale só para a página aberta;
- o tema do sistema (`prefers-color-scheme`) **não** é seguido;
- o clique usa delegação de evento no `document`, porque o script roda antes de
  o botão existir.

O script é carregado no `<head>` **sem `defer` nem `async`**, pelo parcial
`app/templates/_tema.html`. Assim, o tema salvo é aplicado antes de a página
aparecer, evitando o piscar do tema errado. **Todo template de página completa
(com `<html>` e `<head>`) deve incluir `{% include '_tema.html' %}` no
`<head>`.** O script é externo porque a política de segurança de conteúdo
(`app/seguranca.py`) só aceita scripts do próprio site.

`tests/test_tema.py` verifica que todas as páginas completas incluem o parcial,
que `tema.js` não usa `eval(`, `new Function`, `innerHTML` nem URLs externas,
que o `localStorage` só é acessado dentro de `try` e que o botão do topo tem
`aria-pressed` e `aria-label`.

## Cores

Use sempre os tokens de cor de `base.css` (`var(--cor-...)`) e nunca cores fixas
(`#hex`, `rgb()`) nas folhas de estilo das telas. Os valores ficam em dois
lugares: o bloco `:root` (tema escuro) e o bloco `:root[data-theme="light"]`
(tema claro). Um token novo deve ser definido nos dois. A exceção é o botão
"Fazer login com o Google" (`.botao-google`, em `auth.css`), que mantém as
cores da marca do Google nos dois temas.

`tests/test_tokens.py` garante que todo token usado com `var(--nome)` em
`app/static/*.css` esteja definido no `:root` de `base.css` ou no próprio
arquivo que o usa (como os `--auth-*` de `auth.css`). Usos com valor de reserva,
como `var(--x, 10px)`, são ignorados.

### Destaque e preenchimento

A cor principal tem duas funções, com tokens separados para manter o contraste
nos dois temas:

- **Destaque** (`--cor-principal`): texto, links, bordas e foco. No escuro é um
  azul claro e, no claro, um azul profundo.
- **Preenchimento** (`--cor-principal-fundo`, com `--cor-sobre-principal` no
  texto ou ícone sobre ele): fundo de elementos preenchidos, como o botão
  primário, a aba ativa, a opção de nota selecionada, o avatar e o quadrado do
  ícone dos cartões da home. O hover usa `--cor-principal-fundo-hover`.

Não use `--cor-principal` como fundo de elemento preenchido nem
`--cor-principal-fundo` como cor de texto.

### Tokens de cor

Superfícies e topo:

| Token | Escuro | Claro | Uso |
|---|---|---|---|
| `--cor-superficie` | `#0f1a2b` | `#ffffff` | Formulários, cards e diálogos |
| `--cor-fundo-suave` | `#070d17` | `#eaf1fb` | Fundo da página, cabeçalhos de tabela e mensagens informativas |
| `--cor-hover-suave` | `#14243b` | `#e6edf5` | Fundo de hover em linhas de tabela e no botão de tema |
| `--cor-topo-fundo` | `rgb(7 13 23 / 0.92)` | `rgb(255 255 255 / 0.92)` | Fundo da barra do topo |
| `--cor-topo-fundo-blur` | `rgb(7 13 23 / 0.72)` | `rgb(255 255 255 / 0.8)` | Fundo do topo quando o navegador suporta `backdrop-filter` |

Texto:

| Token | Escuro | Claro | Uso |
|---|---|---|---|
| `--cor-texto` | `#e8eef7` | `#202124` | Títulos, rótulos e texto principal |
| `--cor-texto-secundario` | `#a9b6c8` | `#4f5357` | Ajuda, detalhes e datas |
| `--cor-sobre-principal` | `#ffffff` | `#ffffff` | Texto e ícones sobre `--cor-principal-fundo` |

Destaque:

| Token | Escuro | Claro | Uso |
|---|---|---|---|
| `--cor-principal` | `#4f93e6` | `#174b83` | Links, foco, bordas e texto de destaque |
| `--cor-principal-hover` | `#7ab3f2` | `#123c69` | Destaque sob o ponteiro |
| `--cor-principal-suave` | `rgb(79 147 230 / 0.14)` | `rgb(23 75 131 / 0.1)` | Selos, fundos de hover e de foco, degradê dos cartões |
| `--cor-brilho` | `rgb(79 147 230 / 0.25)` | `rgb(23 75 131 / 0.6)` | Brilho em sombras de hover e de seleção |

Preenchimento:

| Token | Escuro | Claro | Uso |
|---|---|---|---|
| `--cor-principal-fundo` | `#1f5fae` | `#1f5fae` | Fundo de botão primário, aba ativa, avatar e ícone dos cartões |
| `--cor-principal-fundo-hover` | `#2a70c8` | `#174b83` | Fundo de preenchimento sob o ponteiro |

Bordas:

| Token | Escuro | Claro | Uso |
|---|---|---|---|
| `--cor-borda-campo` | `#6b7a90` | `#767676` | Limite visível dos controles |
| `--cor-divisor` | `#22334d` | `#c5d3e6` | Borda do topo, dos botões do topo e dos cartões da home |
| `--cor-divisor-suave` | `#1a2a42` | `#dbe5f2` | Bordas de cards, divisórias de tabela e listas e trilho das barras |

Estados e erro:

| Token | Escuro | Claro | Uso |
|---|---|---|---|
| `--cor-erro` | `#f28b82` | `#a01818` | Mensagens de erro e botão de exclusão |
| `--cor-erro-hover` | `#ffb4ad` | `#801212` | Botão de exclusão sob o ponteiro |
| `--cor-erro-suave` | `rgb(242 139 130 / 0.1)` | `rgb(160 24 24 / 0.07)` | Fundo de mensagens de erro |
| `--cor-estrela` | `#f5b94a` | `#b45309` | Estrelas de nota e degraus da barra de dificuldade |

Sombras (também definidas por tema):

| Token | Uso |
|---|---|
| `--sombra-card` | Cards em repouso |
| `--sombra-elevada` | Cards interativos no hover |

Medalhas do ranking (três primeiras posições):

| Token | Escuro | Claro |
|---|---|---|
| `--cor-ouro-fundo` / `--cor-ouro-texto` | `#3a2f0b` / `#f5d77a` | `#fdf0c4` / `#7a5a00` |
| `--cor-prata-fundo` / `--cor-prata-texto` | `#2a3341` / `#cbd5e1` | `#e8ebef` / `#3d4652` |
| `--cor-bronze-fundo` / `--cor-bronze-texto` | `#3a2516` / `#e9b48a` | `#f6dfcc` / `#7a3f12` |

Fundo animado:

| Token | Escuro | Claro |
|---|---|---|
| `--cor-mancha-1` | `#4f93e6` | `#7ab2f8` |
| `--cor-mancha-2` | `#1f5fae` | `#a8cdfa` |
| `--cor-mancha-3` | `#7ab3f2` | `#5a9cf2` |
| `--cor-rede` | `#4f93e6` | `#4a86d6` |

O azul `#007BFF` da home original tinha contraste de 3,98:1 com branco. Por
isso o tema claro usa `#174B83` para destaque e `#1F5FAE` para preenchimento.

### Contraste

Relações calculadas a partir dos valores de `base.css`.

| Elemento | Escuro | Claro |
|---|---|---|
| Texto sobre superfície | 14,97:1 | 16,10:1 |
| Texto sobre fundo suave | 16,69:1 | 14,16:1 |
| Texto secundário sobre superfície | 8,49:1 | 7,76:1 |
| Texto secundário sobre fundo suave | 9,46:1 | 6,82:1 |
| Link (`--cor-principal`) sobre superfície | 5,53:1 | 8,86:1 |
| Foco (`--cor-principal`) sobre fundo suave | 6,16:1 | 7,79:1 |
| Texto sobre preenchimento (`--cor-sobre-principal` sobre `--cor-principal-fundo`) | 6,35:1 | 6,35:1 |
| Texto sobre preenchimento em hover | 4,94:1 | 8,86:1 |
| Erro (`--cor-erro`) sobre superfície | 7,31:1 | 7,96:1 |
| Borda de campo sobre superfície | 4,00:1 | 4,54:1 |
| Número no degrau de dificuldade preenchido (`--cor-superficie` sobre `--cor-estrela`) | 9,91:1 | 5,02:1 |

A escala usa 4,5:1 como mínimo para texto comum e 3:1 para sinais visuais
necessários para identificar controles. No teclado, use um contorno de foco
de 2 px com distância de 2 px. A distância deixa o fundo aparecer entre botão
e contorno. Combine cores com rótulos ou ícones em erros, seleção e confirmação.
Ao criar um par novo de cores, confira o contraste nos dois temas.
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

A fonte é a **Inter** em versão variável (pesos de 100 a 900), subconjunto
latino. O arquivo `app/static/fonts/inter-latin-wght-normal.woff2` é servido
pelo próprio site e declarado por `@font-face` em `base.css`, com
`font-display: swap`. Não se usa CDN nem Google Fonts, porque a política de
segurança de conteúdo (`app/seguranca.py`) só aceita fontes, estilos e scripts
do próprio domínio (`font-src 'self'`). A licença (SIL Open Font License) está
em `app/static/fonts/OFL.txt` e deve acompanhar o arquivo da fonte.

A variável `--fonte` define a pilha: `"Inter"`, `system-ui`, `-apple-system`,
`"Segoe UI"`, `Roboto`, `Arial` e `sans-serif`. Se a Inter não carregar, o
navegador usa a fonte do sistema. Todas as telas usam a Inter por meio de
`--fonte`; a única exceção é o botão "Fazer login com o Google", que mantém a
fonte da marca. O título da home usa tamanho fluido
(`clamp(2.25rem, 1.6rem + 3.2vw, 3.25rem)`), peso 800 e entrelinha 1,1
(`index.css`).

Use espaçamentos de 4, 8, 12, 16, 24, 32 e
48 px. A área de conteúdo tem até 720 px e o formulário de autenticação, até
400 px. Use 16 px de margem lateral em mobile e 24 px em desktop. Campos e
botões têm altura mínima de 44 px. Campos têm raio de 10 px e botões, formato
de pílula. Cards e diálogos têm raio de 16 px e sombra suave em camadas
(`--sombra-card`; `--sombra-elevada` no hover de cards interativos). Em telas estreitas, empilhe controles e ações e preserve os cabeçalhos
das tabelas com rolagem horizontal quando necessário. Os cabeçalhos da tabela
do ranking não quebram no meio da palavra (`white-space: nowrap`); a tabela
rola na horizontal só dentro do próprio card.

## Estética e movimento

As telas seguem uma estética limpa: cards com borda e sombra suave sobre a cor
de superfície, botões e abas em pílula, cabeçalho de página com **selo**
(`.selo`), título e subtítulo (`.cabecalho-pagina`), e link de voltar em pílula
(`.voltar`). As médias por critério usam **barras** (`.barra` e
`.barra-cheia` com `.preenche-N`); a dificuldade usa a
[barra de crescimento](#barra-de-dificuldade). O topo
é uma barra fixa, semitransparente (`--cor-topo-fundo`), com abas e o botão de
tema. Mantêm a identidade do projeto: o azul
principal, a [logo](#logo), as estrelas (`--cor-estrela`) e o rodapé de feedback.

O conteúdo principal entra com um fade curto (`surgir`, 420 ms) e os elementos
interativos têm transições de 160 ms (`--transicao`). Com
`prefers-reduced-motion: reduce`, animações e transições são desligadas.
Evite gradientes chamativos e efeitos de vidro sem função. O único fundo
decorativo é o fundo animado descrito a seguir, restrito às telas listadas.

## Logo

Os arquivos-fonte ficam em `docs/logo/` (`lockup-*` com nome, `simbolo-*` só o
capelo com estrela, e `teste-fundos` com o teste em vários fundos). No site, a
logo é a macro `logo()` de `_macros.html`: o símbolo em SVG inline mais o texto
"Avalia" + "UnB" (`.logo-texto` e `.logo-destaque`, em Inter 700/800). Ela é
usada na marca do topo (`.marca.logo`, símbolo de 44 × 30 px) e no cartão de
entrar (`.auth-logo`, símbolo de 64 × 44 px, com `aria-label="AvaliaUnb"`).

As cores vêm dos tokens `--cor-logo-*`, então a logo acompanha o tema sem
trocar de arquivo:

| Token | Escuro | Claro | Parte |
|---|---|---|---|
| `--cor-logo-texto` | `#ffffff` | `#111111` | "Avalia" |
| `--cor-logo-destaque` | `#ffc72c` | `#174b83` | "UnB" |
| `--cor-logo-capelo` | `#ffffff` | `#174b83` | Topo do capelo |
| `--cor-logo-base` | `#ffffff` | `#111111` | Base do capelo e cordão |
| `--cor-logo-estrela` | `#ffc72c` | `#ffc72c` | Estrela da borla |
| `--cor-logo-contorno` | `transparent` | `#111111` | Contorno da estrela |

O favicon (`app/static/favicon.svg`, ligado em `_tema.html`) usa a versão
branca com estrela amarela sobre um quadrado azul (`#174B83`) de cantos
arredondados, legível em abas claras e escuras. Não altere a proporção do
símbolo (242 × 166 no `viewBox`) nem use a logo sobre fundos sem contraste.

## Fundo animado

O fundo animado é um `<canvas>` desenhado por `app/static/fundo-animado.js`, em
JavaScript puro, sem bibliotecas: manchas de degradê radial em azul que se
movem devagar e uma rede de pontos ligados por linhas finas quando estão
próximos. O canvas ocupa a largura inteira do `<body>`, fica atrás do conteúdo
(`z-index: -1`), não captura cliques (`pointer-events: none`) e tem as quatro
bordas esmaecidas por máscara, para não aparecer um retângulo. As regras do
canvas estão em `base.css` (`.fundo-animado`).

**Densidades**, escolhidas pelo atributo `data-densidade` do canvas:

| Densidade | Telas | Altura | Pontos (por largura da janela) |
|---|---|---|---|
| `normal` | Home | 28rem | 40 (abaixo de 600 px), 55 (abaixo de 1000 px) ou 70 |
| `leve` | Consulta, Ranking, Sobre e Entrar | 14rem | 20, 25 ou 30 |

No modo leve também há menos linhas e as manchas, as linhas e os pontos têm
opacidade menor. As demais telas (avaliação, perfil, comparação e perfil do
professor) não usam o fundo.

**Cores.** O script lê as cores dos tokens `--cor-mancha-1`, `--cor-mancha-2`,
`--cor-mancha-3` e `--cor-rede` com `getComputedStyle`; não há cores fixas no
JavaScript. No tema claro esses tokens são azuis claros e luminosos, e o script
aplica um fator de opacidade menor (0,9) por detectar fundo claro. O fundo se
redesenha quando o `data-theme` do `<html>` muda.

**Comportamento e desempenho:**

- com `prefers-reduced-motion: reduce`, desenha um único quadro parado, sem
  animar;
- pausa quando a aba está oculta (`visibilitychange`) e quando o canvas sai da
  tela (`IntersectionObserver`), e retoma sem salto;
- anima a cerca de 30 quadros por segundo, com número de pontos e de linhas
  limitado;
- ajusta o tamanho ao redimensionar a janela e limita o `devicePixelRatio` a 2
  (1,5 abaixo de 600 px de largura);
- **não reage ao mouse**: o movimento é o mesmo com ou sem ponteiro.

`tests/test_fundo_animado.py` garante que o script trata `prefers-reduced-motion`,
`visibilitychange` e `IntersectionObserver`, que não contém `eval(`,
`new Function`, `innerHTML` nem URLs `http://` ou `https://`, e que todo
template com o canvas também carrega o script por `url_for` e usa
`aria-hidden="true"`.

**Para incluir o fundo em uma tela nova:**

1. No template, logo após o topo (ou no início do `<body>`), adicione
   `<canvas class="fundo-animado" data-densidade="leve" aria-hidden="true"></canvas>`
   (use `normal` só se a tela for tão destacada quanto a home).
2. Antes do `</body>`, carregue o script:
   `<script src="{{ url_for('static', filename='fundo-animado.js') }}" defer></script>`.
3. No CSS da tela, o `body` precisa de `position: relative` para o canvas
   ficar atrás do conteúdo.
4. Não use o fundo em telas com tabelas ou formulários longos.

## Microinteração e acessibilidade

- **Cartões da home:** no hover, o cartão sobe 3 px, a borda passa a
  `--cor-principal`, a sombra combina `--sombra-elevada` com um brilho
  (`--cor-brilho`) e o ícone cresce 5%. Isso só vale dentro de
  `@media (hover: hover) and (pointer: fine)`, para não "prender" o efeito em
  telas de toque.
- **Botões:** no clique (`:active`), `.botao` encolhe para `scale(0.98)`, com a
  mesma transição de 160 ms. Botões desabilitados não reagem.
- **Movimento reduzido:** com `prefers-reduced-motion: reduce`, as transições e a
  entrada do conteúdo são desligadas, o hover dos cartões não move nada e o
  fundo animado desenha um quadro parado.
- **Foco visível:** links, botões, campos, seletores, áreas de texto e elementos
  com `tabindex` usam contorno de 2 px na cor `--cor-principal`, com distância
  de 2 px. Os campos somam um anel suave (`--cor-principal-suave`).
- **Botão de tema:** é um `<button type="button">` com `aria-pressed` (`true`
  quando o tema claro está ativo) e `aria-label` que alterna entre "Ativar tema
  claro" e "Ativar tema escuro". Os ícones de sol e lua são decorativos
  (`aria-hidden="true"`): o sol aparece no escuro e a lua, no claro.
- **Elementos decorativos:** o canvas do fundo animado tem
  `aria-hidden="true"`.

## Home

O cabeçalho da home é centralizado: selo, título "Bem-vindo ao AvaliaUnb" e a
frase de apresentação (com largura limitada a 40rem). Logo abaixo da frase fica
a **busca de professor**: um formulário `GET` para a Consulta
(`url_for('professores.listar')`) com o campo `nome`, o mesmo parâmetro do
filtro "Nome do professor" da Consulta. O campo (`type="search"`) é uma pílula
com largura máxima de 36rem, tem rótulo acessível visualmente oculto (`.sr-only`)
e botão "Buscar"; até 480 px, campo e botão empilham.
`tests/test_home_busca.py` verifica o formulário, o parâmetro e o acesso à
Consulta com ele.

Abaixo ficam os **cartões de acesso rápido** ("Ranking de Professores" e
"Comparar Professores"), empilhados no celular e lado a lado a partir de
481 px, com o mesmo tamanho. Cada cartão tem fundo de superfície com um degradê
suave no canto (`--cor-principal-suave`), borda `--cor-divisor` e um ícone em
quadrado preenchido (`--cor-principal-fundo`). O acesso à Consulta fica pela
busca e pela aba "Consulta" do topo.

## Barra de dificuldade

A dificuldade (1 a 5) aparece como uma **barra de crescimento**: cinco degraus
cada vez mais altos, da esquerda para a direita, como o sinal de celular, na
cor `--cor-estrela`. Os outros quatro critérios continuam com botões numerados
e barras comuns. O valor salvo continua sendo um inteiro de 1 a 5; a mudança é
só de interface.

- **Leitura:** a macro `barra_dificuldade(valor, mostrar_valor=true)` de
  `_macros.html` gera `.degraus-leitura` > `.degraus` > cinco `.degrau`; os
  degraus de 1 até o nível recebem `.degrau-ativo` (preenchidos), os demais
  ficam só com o contorno, então a barra não depende só da cor. Médias com
  decimais são arredondadas para o degrau mais próximo (3,4 → 3; 3,5 → 4),
  e o valor exato fica no `aria-label` ("Dificuldade 3,4 de 5") e em texto
  (`.degraus-valor`, ou ao lado, com `mostrar_valor=false`). Valor `None` não
  desenha nada. Usada no perfil do professor, no perfil do usuário e na
  comparação.
- **Seleção:** no formulário de avaliação, o grupo da dificuldade ganha
  `.degraus-selecao`. Os `<input type="radio" name="dificuldade">` continuam
  os mesmos, então o POST não muda, a tela funciona sem JavaScript e as setas
  do teclado trocam o degrau. Os `<label>` viram degraus com o número visível;
  ao marcar o degrau N, `:has(input:checked)` preenche todos e
  `input:checked + label ~ label` esvazia os posteriores. Sem suporte a
  `:has()`, só o degrau marcado é preenchido. O foco usa o mesmo contorno dos
  outros botões de nota, e os rótulos "1 = Muito fácil" e "5 = Muito difícil"
  ficam abaixo.
- **CSP:** nenhum `style=""`; o nível vem de classes, como em `.preenche-N`.
- **Compacta (Consulta):** nos itens de disciplina do cartão da Consulta, a
  barra usa `.barra-hp-compacta` (tamanho fixo pequeno, sem a escala) e é
  decorativa para leitores de tela (`aria-hidden="true"`), porque o texto
  "Dificuldade X/5" ao lado traz o valor. Os estilos ficam em
  `lista_professores.css`, só com tokens.

## Componentes e estados

| Componente | Comportamento | Estados |
|---|---|---|
| Botão principal | Fundo `--cor-principal-fundo`, texto `--cor-sobre-principal` e uma ação principal por formulário | Padrão, hover, clique, foco, desabilitado e envio |
| Botão secundário | Fundo de superfície, borda e texto na cor principal e rótulo Voltar ou Cancelar | Padrão, hover, clique, foco e desabilitado |
| Botão destrutivo | Cor de erro (`--cor-erro`), com texto na cor de superfície, na confirmação de exclusão, inclusive a de comentário | Padrão, foco e envio |
| Campo, seletor e área de texto | Rótulo visível, borda, ajuda e erro junto ao campo | Vazio, preenchido, foco, erro e desabilitado |
| Card de professor | Nome, departamento, disciplinas e ações | Padrão e resultado de filtro |
| Card de comentário | Texto, nome de usuário, data, disciplina (em etiqueta) e ações permitidas. O nome é só texto: o e-mail do autor nunca é exibido | Publicado, em edição e ocultado para o autor |
| Reação a comentário | Ícones de polegar sempre visíveis. Cada número aparece só com reações recebidas. Os botões têm nomes acessíveis Curtir e Descurtir e usam `aria-pressed` para indicar a seleção | Neutro, selecionado com marca e cor, foco, envio e leitura no próprio comentário |
| Mensagem | Explica o estado e a próxima ação | Informação, sucesso, erro, vazio e carregamento |
| Diálogo de exclusão | Identifica o item e sua consequência. Cancelar recebe o foco inicial | Aberto, confirmando e falha |
| Tabela de indicadores | Legenda, cabeçalhos associados e valores legíveis | Com dados, sem dados e erro |
| Barra de dificuldade | Cinco degraus crescentes na cor da estrela, com o valor em texto e no `aria-label` | Leitura (média arredondada), seleção, marcado, foco e sem dados |
| Botão de tema | Botão de 40 px em pílula no topo, com ícones de sol e lua | Padrão, hover, foco, tema escuro e tema claro |

Durante o envio, preserve o texto digitado, informe o progresso e evite envios
duplicados. Quando houver erro, devolva o controle ao usuário com a mensagem
visível. No estado vazio, informe se faltam dados ou se o filtro não encontrou
resultados. Ao fechar o diálogo de exclusão, devolva o foco ao contexto de origem.

Os [protótipos de comentários](TELAS_COMENTARIOS.md) mostram os fluxos de
listar, reagir, escrever, editar e apagar.

## Checklist para criar ou alterar uma tela

- Use apenas tokens de `base.css` para cor, sombra, espaçamento e fonte; não
  escreva `#hex` nem `rgb()` nas folhas de estilo das telas.
- Para um elemento preenchido de azul, use `--cor-principal-fundo` com
  `--cor-sobre-principal`; use `--cor-principal` só para texto, links, bordas e
  foco.
- Se criar um token, defina-o no `:root` e em `:root[data-theme="light"]`.
- Inclua `{% include '_tema.html' %}` no `<head>` de todo template de página
  completa.
- Não use CDN, estilo inline nem script inline (política de segurança de
  conteúdo).
- Confira a tela nos dois temas (use o botão de tema) e com movimento reduzido
  (`prefers-reduced-motion: reduce`).
- Verifique o contraste de texto (4,5:1) e o foco visível por teclado.
- Se a tela usar o fundo animado, siga a seção "Fundo animado".
- Rode a suíte de testes:
  `python -m unittest discover -s tests -t .`

Relacionado: [inventário do frontend](FRONTEND.md),
[protótipos de comentários](TELAS_COMENTARIOS.md) e
[checklist de contribuição](PROCESSO_CONTRIBUICAO.md).
