# Agentes de IA utilizados

Registro das ferramentas de IA usadas no projeto, para transparência e reprodutibilidade.

## Logo AvaliaUnB (novembro de 2026)

| Item | Detalhe |
|---|---|
| Ferramenta | [Claude Code](https://claude.com/claude-code) (CLI), modelo Claude Opus 5.5 |
| Skill/plugin | `logo-design` do marketplace [kaankiziltug/logo-design-skill](https://github.com/kaankiziltug/logo-design-skill) (v1.4.5) |
| Resultado | `docs/logo/` (símbolos, lockups e folha de teste em fundos claros e escuros) |
| Instruções da skill | [`skills/logo-design/SKILL.md`](skills/logo-design/SKILL.md) (cópia da v1.4.5, licença MIT em `skills/logo-design/LICENSE`) |
### Instalação da skill

Dentro do Claude Code:

```text
/plugin marketplace add kaankiziltug/logo-design-skill
/plugin install logo-design@logo-design-skill
/reload-plugins
```

### Pedidos feitos ao agente

1. "Utilizando a ideia de logo que já tenho no site, use essa skill e crie algo que misture uma estrela de avaliação com UnB."
   - Foram gerados 3 conceitos (estrela com capelo, U com estrela, estrela de 5 critérios). Descartados.
2. "Utilize a primeira com chapéu de formando, mas faça a estrela bem menor que o chapéu, e utilize azul, branco e preto, de forma que fique boa em fundos escuros e claros. Pode usar amarelo também."
   - Versão aprovada: capelo com a estrela pendurada na borla.

### Scripts da skill usados

- `render_png.py` — renderiza os SVGs em PNG para inspeção visual;
- `svg_audit.py` — confere geometria, cores e detalhes pequenos;
- `concept_sheet.py` — folha de comparação dos conceitos iniciais.

### Observações

- Os lockups ainda usam texto (`<text>`) com fonte do sistema; para a versão final, converter as letras em contornos.
- Em 16 px a estrela praticamente some; o favicon deve ter uma versão própria com a estrela ampliada.
- O logo oficial da UnB não foi copiado. Ele é marca registrada da universidade.
