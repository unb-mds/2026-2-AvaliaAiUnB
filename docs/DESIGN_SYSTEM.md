# Design system

A nova interface segue o modelo editorial aprovado: fundo preto, verde claro de destaque, títulos expressivos, painéis discretos e capelo branco com estrela dourada.

## Tokens e temas

Os tokens visuais foram importados do arquivo `avaliaunb_editorial_premium_ajuste_logo_chapeu (3).html` para `app/static/modelo-editorial.css`. `base.css` mantém os componentes funcionais e as fontes locais. O escuro é o padrão. O claro usa `data-theme="light"` no elemento `html`. A preferência fica na chave `tema` do localStorage, com tratamento para armazenamento indisponível. O arquivo `tema.js` é carregado no head para evitar o piscar do tema errado.

| Papel | Escuro | Claro |
|---|---|---|
| Fundo | `#050505` | `#f6f7f2` |
| Painel | `#111211` | `#ffffff` |
| Texto | `#f4f5f0` | `#1a2119` |
| Texto secundário | `#a1a69d` | `#647062` |
| Destaque | `#b2ff80` | `#3f842e` |
| Divisor | `#292b28` | `#dfe4d9` |

A fonte de texto é Inter; os títulos usam Inter Tight variável, pesos 400–800. Ambas são hospedadas localmente com suas licenças. O símbolo é o PNG original incorporado no modelo, extraído sem redesenho para `logo-chapeu-modelo.png`. O chapéu e a estrela mantêm a proporção do arquivo aprovado.

## Componentes

- Botão primário com preenchimento verde; secundário com fundo neutro e contorno. Os botões seguem as proporções do modelo e mantêm foco visível.
- Formulários mantêm rótulos associados, mensagens de erro, dados após validação e proteção CSRF.
- Cartões usam borda discreta, raio de 16 px e espaçamento amplo. Comentários são organizados em linhas, sem painéis sobrepostos.
- Estados vazios e de indisponibilidade permanecem visíveis e não recebem notas ou conteúdo fictício.
- Reações apresentam ícone, quantidade, nome acessível e `aria-pressed`. A cor reforça a escolha sem ser o único sinal.

## Composição e responsividade

`modelo-editorial.css` contém a composição do arquivo enviado: navegação, hero, cartões, perfil, linhas de ranking e comparação. `integracao-editorial.css` adapta os formulários, a paginação, as notas e os estados reais a essa composição. Ambos são carregados por `_tema.html`; os antigos estilos de página não são carregados.

A página inicial mantém o título, os textos, o chapéu em marca-d’água e os blocos de acesso do arquivo. Os três destaques usam notas reais do catálogo, ordenado por quantidade de avaliações; isso não altera o mínimo de cinco avaliações do ranking.

O catálogo usa iniciais e nota no topo dos cartões, nome e departamento no centro e acesso ao perfil no rodapé. Disciplinas, dificuldade e ações adicionais continuam acessíveis em detalhes expansíveis. O perfil usa cabeçalho com iniciais e nota, painel lateral de critérios reais e comentários em linhas.

O ranking usa as linhas da referência. A comparação mostra cartões de resumo; a tabela completa de critérios permanece disponível em uma seção expansível. Os controles para mesma disciplina, seleção livre e múltiplos professores continuam disponíveis.

O menu móvel abre no topo e fecha com Escape. Informa seu estado por `aria-expanded`. O acesso à conta permanece visível no cabeçalho do celular; o menu também oferece conta e saída. Não há navegação fixa inferior.

## Acessibilidade e movimento

O foco usa os tokens compartilhados e não é removido. Imagens decorativas são ocultadas de leitores de tela. Nomes longos quebram sem alargar a página. Os estados de avaliação e dificuldade continuam identificados por texto e números.

A barra de progresso e os efeitos de luz são decorativos e respeitam `prefers-reduced-motion`. Os filtros e formulários continuam funcionando sem JavaScript; o autocompletar aprimora esses fluxos quando disponível.

Consulte [Nova interface](NOVA_INTERFACE.md) para execução, dados da prévia e limites da validação.

## Barra de dificuldade

A macro `barra_dificuldade` mantém a escala de 1 a 5: 1 significa muito fácil e 5, muito difícil. A barra de degraus e o texto acessível apresentam o mesmo valor, inclusive nas médias fracionárias. O formulário continua gravando somente notas inteiras nessa escala. Dificuldade não entra na média geral e, na comparação, a menor dificuldade vence entre os professores elegíveis ao destaque.
