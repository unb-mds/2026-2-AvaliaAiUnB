# Frontend

A interface do AvaliaAi é renderizada pelo Flask com templates Jinja2 em
`app/templates/` e folhas de estilo em `app/static/`. A navegação e o envio de
dados usam links e formulários HTML; a aplicação não exige um build de frontend
separado para executar essas telas.

## Páginas e estilos atuais

| Template | Conteúdo | CSS carregado |
|---|---|---|
| `index.html` | Início, consulta, ranking e acesso à conta | `indicadores.css`, `index.css` |
| `cadastro.html` | Cadastro, validações e mensagem de sucesso | `auth.css` |
| `login.html` | Login e mensagem de erro | `auth.css` |
| `lista_professores.html` | Filtros, catálogo e estados sem resultado | `indicadores.css` |
| `perfil_professor.html` | Disciplinas, indicadores, comparação e avaliação | `indicadores.css`, `perfil_professor.css` |
| `avaliacao.html` | Criação e edição de notas | `indicadores.css`, `avaliacao.css` |
| `perfil.html` | Avaliações do usuário e ações de editar e excluir | `perfil.css` |
| `comparacao.html` | Seleção e comparação de professores | `indicadores.css` |
| `ranking.html` | Classificação e estado sem professores elegíveis | `indicadores.css` |

As rotas preparam os dados e chamam `render_template`. Os nomes dos endpoints,
parâmetros e regras de autorização estão no [guia do backend](BACKEND.md).

## Componentes e estados existentes

O arquivo `indicadores.css` reúne estilos compartilhados para filtros, listas,
indicadores, comparação e ranking. Entre as classes existentes estão `.filtros`,
`.lista-professores`, `.indicadores`, `.ajuda`, `.erros`, `.tabela-comparacao`
e `.tabela-ranking`.

O catálogo mostra mensagens diferentes para ausência de dados e ausência de
resultados dos filtros. O perfil informa quando não há avaliações válidas;
cadastro e avaliação exibem erros de campo; a comparação exige dois professores
diferentes; e o ranking informa quando ninguém atinge o mínimo de avaliações.

O CSS compartilhado usa Arial, texto `#202124`, links `#174b83`, mensagens de
ajuda `#4f5357` e erros `#a01818`. Esses valores são um inventário do código atual.
A home usa também `#007BFF` nos botões. Os arquivos ainda têm definições próprias
por tela e o perfil do professor contém estilo inline.

## Design system e visual final

A [issue #112](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/112) reúne a
consolidação de cores, tipografia, espaçamentos, componentes e estados. A aplicação do visual nas telas principais está na
[issue #114](https://github.com/unb-mds/2026-2-AvaliaAiUnB/issues/114).

O inventário acima registra a interface que existe hoje. O catálogo de padrões
e os protótipos de comentários são entregues separadamente na #112.

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
