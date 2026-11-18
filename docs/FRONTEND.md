# Frontend

A interface do AvaliaUnb é renderizada pelo Flask com templates Jinja2 em
`app/templates/` e folhas de estilo em `app/static/`. A navegação e o envio de
dados usam links e formulários HTML; a aplicação não exige um build de frontend
separado para executar essas telas.

## Páginas e estilos atuais

| Template | Conteúdo | CSS carregado |
|---|---|---|
| `index.html` | Início, consulta, ranking e acesso à conta | `base.css`, `index.css` |
| `login.html` | Botão "Entrar com Google" (login e cadastro) e mensagem de erro | `base.css`, `auth.css` |
| `sobre.html` | Apresentação do projeto, critérios e privacidade | `base.css`, `sobre.css` |
| `lista_professores.html` | Filtros, catálogo, média geral em estrelas e estados sem resultado | `indicadores.css` (que importa `base.css`), `lista_professores.css` |
| `perfil_professor.html` | Disciplinas (campo digitável), indicadores, média geral, comparação, avaliação e a seção de comentários (filtro por disciplina, lista, formulário de publicar e convite para entrar) | `indicadores.css`, `perfil_professor.css`, `comentarios.css` |
| `avaliacao.html` | Criação e edição de notas (botões de 1 a 5; dificuldade em barra de crescimento) | `indicadores.css`, `avaliacao.css` |
| `editar_comentario.html` | Edição do próprio comentário (disciplina e texto) | `indicadores.css`, `avaliacao.css`, `comentarios.css` |
| `excluir_comentario.html` | Confirmação de exclusão do próprio comentário | `indicadores.css`, `avaliacao.css`, `comentarios.css` |
| `perfil.html` | Avaliações do usuário e ações de editar e excluir | `base.css`, `perfil.css` |
| `comparacao.html` | Escolha por nome e comparação de professores | `indicadores.css`, `comparacao.css` |
| `ranking.html` | Classificação e estado sem professores elegíveis | `indicadores.css`, `ranking.css` |

Fragmentos reutilizados: `_topo.html` (faixa azul com o menu de acesso rápido de três
traços, a marca, a conta e o Sair, usada na home, na busca, na comparação, no ranking
e nos dois perfis; espera `usuario` no contexto) e `_macros.html` (macro `nota`, que formata notas com vírgula e sem
decimal quando inteiras, como 5 em vez de 5,0, e macro `barra_dificuldade`, que
desenha a dificuldade como barra de crescimento, e macro `logo`, com o símbolo e o
nome usados no topo e na tela de entrar no perfil do professor, no perfil
do usuário e na comparação; veja o [design system](DESIGN_SYSTEM.md#barra-de-dificuldade)).

As rotas preparam os dados e chamam `render_template`. Os nomes dos endpoints,
parâmetros e regras de autorização estão no [guia do backend](BACKEND.md).

## Componentes e estados existentes

O arquivo `base.css` concentra os tokens do [design system](DESIGN_SYSTEM.md)
como variáveis em `:root` (`--cor-*`, `--espaco-*`, `--raio`, `--altura-controle`,
larguras e margens) e os componentes reutilizáveis: `.botao` com `-primario`,
`-secundario` e `-destrutivo`, `.campo` (com `.campo-ajuda` e `.campo-erro`),
`.card`, `.mensagem` e `.mensagem-erro`, o topo (`.topo`, `.marca`, `.abas`, `.aba`, `.botao-sair`),
a nota em estrelas (`.estrelas` e `.preenche-0` a `.preenche-100`) e o foco visível
de 2 px. Cada tela carrega `base.css` diretamente ou por meio de `indicadores.css`,
que o importa com `@import`.

O topo (`_topo.html`) é uma barra branca fixa ao rolar, com a marca e as abas
**Consulta**, **Ranking**, **Sobre** e **Perfil** (ou **Entrar**, sem login). A aba
da página atual recebe `aria-current="page"`, definido pelo `request.endpoint`.
No celular, as abas ficam numa segunda linha com rolagem horizontal.

O arquivo `indicadores.css` reúne estilos compartilhados para filtros, listas,
indicadores, comparação e ranking. Entre as classes existentes estão `.filtros`,
`.lista-professores`, `.indicadores`, `.ajuda`, `.erros`, `.tabela-comparacao`
e `.tabela-ranking`. As telas de busca, perfil do professor, avaliação e comparação
carregam depois uma folha própria que ajusta o que é específico delas, sem alterar
`indicadores.css`, porque o ranking depende dele.

Os comentários têm folha própria, `comentarios.css`, carregada depois do CSS da
tela e só com tokens de `base.css`, então vale nos dois temas. Ela estiliza a
seção do perfil (filtro "Disciplina", cartão de cada comentário com a disciplina
em etiqueta, links Editar e Excluir, convite "Entrar para comentar", aviso de
erro e frase dos 50 comentários) e o formulário, que também aparece na página de
editar. A confirmação de exclusão usa `.botao-destrutivo` (cor `--cor-erro`) e
deixa o "Cancelar" em destaque. Em telas de até 600 px, a seção usa coluna única
e botões em largura total. A confirmação de exclusão do comentário é uma página
própria, sem JavaScript.

O catálogo mostra mensagens diferentes para ausência de dados e ausência de
resultados dos filtros e exibe a média
geral em cinco estrelas ou `N/A (Não avaliado)`. O filtro de departamento é um campo
de texto com sugestões. O perfil informa quando não há avaliações válidas e mostra a
média geral do professor; a avaliação exibe erros de campo; a comparação
exige dois professores diferentes; e o ranking informa quando ninguém atinge o
mínimo de avaliações. No perfil do usuário, Apagar abre uma confirmação (`<details>`,
sem JavaScript) antes de enviar a exclusão.

A média geral usa didática, clareza, organização e disponibilidade, sem a
dificuldade, como o ranking. A política de segurança (`style-src 'self'` em
`app/seguranca.py`) bloqueia `style=""` inline, então valores dinâmicos de estilo
precisam virar classes de CSS (como `.preenche-N` nas barras e `.degrau-ativo` na
barra de dificuldade).

Cores, Arial, espaçamentos, raios e alturas seguem o design system e vêm das
variáveis de `base.css`. O ranking possui uma folha de estilos própria e segue disponível na rota `/ranking`;
qualquer alteração de escopo deve ser tratada em sua issue específica.

Scripts em `app/static/` (a política de segurança só aceita scripts do próprio
domínio): `campo-busca.js` transforma os `<select>` dentro de `.campo-busca` (professores na
comparação e disciplina no perfil do professor) em campos digitáveis com sugestões.
O `<select>` continua no formulário, então a tela funciona sem JavaScript.
O mesmo arquivo liga a busca unificada aos campos `.campo-sugestoes` (Consulta e
Comparação): consulta `data-sugestoes` com o `data-contexto` do campo e mostra as
sugestões no padrão *combobox* da WAI-ARIA (setas, Enter, Esc, `aria-activedescendant`
e uma região `status` que anuncia a quantidade). Sem JavaScript, o formulário envia o
termo (`q` na Consulta, `busca` na Comparação, que lista os resultados como links).

## Design system e visual final

A [issue #112](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/112) reúne a
consolidação de cores, tipografia, espaçamentos, componentes e estados. A aplicação do visual nas telas principais está na
[issue #114](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/114).

O inventário acima registra a interface que existe hoje. O
[design system](DESIGN_SYSTEM.md) reúne o padrão proposto para os componentes.
Os [protótipos de comentários](TELAS_COMENTARIOS.md) aplicam esse padrão.
O [mapa da documentação](GUIA_DOCUMENTACAO.md) conecta as regras de interface,
[funcionalidades](FUNCIONALIDADES.md) e [contribuição](PROCESSO_CONTRIBUICAO.md).

As telas de comentários seguem a
[especificação para revisão](COMENTARIOS.md). A #112 depende dessa especificação
para desenhar os fluxos de listar, escrever, editar e apagar comentários, que
já estão implementados (#167). Reações, ordenação, denúncia e moderação ainda
são propostas.

## Como contribuir com as telas

1. Identifique a rota e o template afetados e preserve os nomes de campos e
   parâmetros esperados pelo backend. Use `url_for` para endpoints e recursos
   estáticos ao adicionar links.
2. Reutilize os estilos compartilhados existentes. Ao extrair CSS repetido,
   confira as demais páginas que carregam a folha alterada.
3. Mantenha `csrf_token` em formulários POST, inclusive logout e exclusão.
   Nas telas de autenticação, preserve o campo `formato=html`.
4. Preserve os rótulos associados aos campos, mensagens de erro, cabeçalhos e
   captions das tabelas. Confira foco visível e navegação por teclado.
5. Confira desktop e mobile, textos longos, estados vazios e erros. Para ranking
   e comparação, verifique também a rolagem horizontal e a legibilidade das tabelas.
6. Execute os testes do fluxo alterado e a suíte descrita em [Backend](BACKEND.md).
   Registre no PR as telas e estados conferidos no navegador.

A conferência de contraste e o inventário de estados de carregamento continuam
no escopo da #112. A aprovação das regras de comentários é uma etapa do grupo
na #116; a interface de listar, publicar, editar e excluir comentários está
implementada, e a de reações, ordenação, denúncia e moderação ainda não.
