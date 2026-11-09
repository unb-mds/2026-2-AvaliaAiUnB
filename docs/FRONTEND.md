# Frontend

A interface do AvaliaAi é renderizada pelo Flask com templates Jinja2 em
`app/templates/` e folhas de estilo em `app/static/`. A navegação e o envio de
dados usam links e formulários HTML; a aplicação não exige um build de frontend
separado para executar essas telas.

## Páginas e estilos atuais

| Template | Conteúdo | CSS carregado |
|---|---|---|
| `index.html` | Início, consulta, ranking e acesso à conta | `base.css`, `index.css` |
| `cadastro.html` | Cadastro, validações e mensagem de sucesso | `base.css`, `auth.css` |
| `login.html` | Login e mensagem de erro | `base.css`, `auth.css` |
| `lista_professores.html` | Filtros, catálogo paginado, média geral em estrelas e estados sem resultado | `indicadores.css` (que importa `base.css`), `lista_professores.css` |
| `perfil_professor.html` | Disciplinas (campo digitável), indicadores, média geral, comparação e avaliação | `indicadores.css`, `perfil_professor.css` |
| `avaliacao.html` | Criação e edição de notas (botões de 1 a 5) | `indicadores.css`, `avaliacao.css` |
| `perfil.html` | Avaliações do usuário e ações de editar e excluir | `base.css`, `perfil.css` |
| `comparacao.html` | Escolha por nome e comparação de professores | `indicadores.css`, `comparacao.css` |
| `ranking.html` | Classificação e estado sem professores elegíveis | `indicadores.css`, `ranking.css` |

Fragmentos reutilizados: `_topo.html` (faixa azul com o menu de acesso rápido de três
traços, a marca, a conta e o Sair, usada na home, na busca, na comparação, no ranking
e nos dois perfis; espera `usuario` no contexto) e `_macros.html` (macro `nota`, que formata notas com vírgula e sem
decimal quando inteiras, como 5 em vez de 5,0).

As rotas preparam os dados e chamam `render_template`. Os nomes dos endpoints,
parâmetros e regras de autorização estão no [guia do backend](BACKEND.md).

## Componentes e estados existentes

O arquivo `base.css` concentra os tokens do [design system](DESIGN_SYSTEM.md)
como variáveis em `:root` (`--cor-*`, `--espaco-*`, `--raio`, `--altura-controle`,
larguras e margens) e os componentes reutilizáveis: `.botao` com `-primario`,
`-secundario` e `-destrutivo`, `.campo` (com `.campo-ajuda` e `.campo-erro`),
`.card`, `.mensagem` e `.mensagem-erro`, o topo (`.topo`, `.marca`, `.topo-conta`),
a nota em estrelas (`.estrelas` e `.preenche-0` a `.preenche-100`) e o foco visível
de 2 px. Cada tela carrega `base.css` diretamente ou por meio de `indicadores.css`,
que o importa com `@import`.

O arquivo `indicadores.css` reúne estilos compartilhados para filtros, listas,
indicadores, comparação e ranking. Entre as classes existentes estão `.filtros`,
`.lista-professores`, `.indicadores`, `.ajuda`, `.erros`, `.tabela-comparacao`
e `.tabela-ranking`. As telas de busca, perfil do professor, avaliação e comparação
carregam depois uma folha própria que ajusta o que é específico delas, sem alterar
`indicadores.css`, porque o ranking depende dele.

O catálogo mostra mensagens diferentes para ausência de dados e ausência de
resultados dos filtros, pagina 100 professores por vez (`?pagina=N`) e exibe a média
geral em cinco estrelas ou `N/A (Não avaliado)`. O filtro de departamento é um campo
de texto com sugestões. O perfil informa quando não há avaliações válidas e mostra a
média geral do professor; cadastro e avaliação exibem erros de campo; a comparação
exige dois professores diferentes; e o ranking informa quando ninguém atinge o
mínimo de avaliações. No perfil do usuário, Apagar abre uma confirmação (`<details>`,
sem JavaScript) antes de enviar a exclusão.

A média geral usa didática, clareza, organização e disponibilidade, sem a
dificuldade, como o ranking. A política de segurança (`style-src 'self'` em
`app/seguranca.py`) bloqueia `style=""` inline, então valores dinâmicos de estilo
precisam virar classes de CSS.

Cores, Arial, espaçamentos, raios e alturas seguem o design system e vêm das
variáveis de `base.css`. O ranking ainda não usa o novo visual e será removido em
outra issue.

Scripts em `app/static/` (a política de segurança só aceita scripts do próprio
domínio): `topo.js` fecha o menu do topo ao clicar fora ou apertar Esc, e
`campo-busca.js` transforma os `<select>` dentro de `.campo-busca` (professores na
comparação e disciplina no perfil do professor) em campos digitáveis com sugestões.
O `<select>` continua no formulário, então a tela funciona sem JavaScript.

## Design system e visual final

A [issue #112](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/112) reúne a
consolidação de cores, tipografia, espaçamentos, componentes e estados. A aplicação do visual nas telas principais está na
[issue #114](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/114).

O inventário acima registra a interface que existe hoje. O
[design system](DESIGN_SYSTEM.md) reúne o padrão proposto para os componentes.
Os [protótipos de comentários](TELAS_COMENTARIOS.md) aplicam esse padrão.

As telas futuras de comentários devem seguir a
[especificação para revisão](COMENTARIOS.md). A #112 depende dessa especificação
para desenhar os fluxos de listar, escrever, editar e apagar comentários.

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
na #116; o recurso ainda não tem interface implementada.
