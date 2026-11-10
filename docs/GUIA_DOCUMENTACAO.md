# Mapa da documentação

Este guia organiza a documentação atual do repositório. O [README](https://github.com/unb-mds/2026-2-AvaliaAiUnB/blob/main/README.md)
é a entrada para instalação e resumo do produto; as páginas abaixo concentram
os detalhes. **Descrição do estado atual não equivale a funcionalidade planejada.**

## Encontre a informação

| Assunto | Documento de referência | Complementos |
|---|---|---|
| Problema, público e requisitos | [Documento de visão](DOCUMENTO_DE_VISAO.md) | [Funcionalidades disponíveis](FUNCIONALIDADES.md) |
| Visão técnica e diagramas | [Arquitetura](ARQUITETURA.md) | [Backend](BACKEND.md), [Frontend](FRONTEND.md) |
| Tabelas, relacionamentos e políticas | [Modelo de dados](Modelo%20de%20Dados.md) | [SQL versionado](migrations/001_initial_schema.sql) |
| Coleta e atualização do SIGAA | [Guia do scraper](COMO_USAR_SCRAPER.md) | [Modelo de dados](Modelo%20de%20Dados.md) |
| Rotas e autenticação | [Backend](BACKEND.md) | [Cibersegurança](CIBERSEGURANCA.md) |
| Templates e componentes | [Frontend](FRONTEND.md) | [Design system](DESIGN_SYSTEM.md) |
| CI, checks e publicação | [Pipeline](pipeline.md) | [Hospedagem](HOSPEDAGEM.md) |
| Auditoria e plano de correção | [Auditoria de segurança](AUDITORIA_SEGURANCA.md) | [Cibersegurança](CIBERSEGURANCA.md) |
| Funcionalidade futura de comentários | [Especificação](COMENTARIOS.md) | [Mockups](TELAS_COMENTARIOS.md) |
| Pronto para começar/concluído | [Critérios de contribuição](PROCESSO_CONTRIBUICAO.md) | Templates de issue/PR em `.github/` |

## Inventário da revisão (issue #136)

| Documento | Desatualização ou atenção identificada | Tratamento |
|---|---|---|
| `DOCUMENTO_DE_VISAO.md` | Referência a Render/Heroku e comentários como código pronto | Hospedagem e separação de visão vs. entrega corrigidas |
| `Modelo de Dados.md` | Declarava ausência de políticas, embora o SQL versionado contenha RLS | Corrigido e distinguido do banco efetivamente implantado |
| `COMO_USAR_SCRAPER.md` | Exemplo de configuração impreciso e links insuficientes | Corrigido e conectado ao modelo |
| `FRONTEND.md` | Paginação e futura remoção do ranking sem evidência na rota atual | Inventário ajustado |
| `pipeline.md` | Misturava alerta do scanner com política obrigatória de merge | Esclarecido |
| `BACKEND.md` | Papel das camadas e fluxo de teste espalhados | Acrescentadas referências |
| `ARQUITETURA.md` | Mostrava diagramas sem apontar para os guias detalhados | Acrescentadas referências |
| `FUNCIONALIDADES.md` | Guia pouco conectado à arquitetura e visão | Acrescentadas referências |
| `CIBERSEGURANCA.md` | Auditoria histórica confundida com correções atuais | Separação e referências reforçadas |
| `AUDITORIA_SEGURANCA.md` | Foto de 02/11 poderia parecer estado corrente | Marcado explicitamente como histórico |
| `HOSPEDAGEM.md` | Sem referências a pipeline/segurança no fluxo de validação | Conectado |
| `COMENTARIOS.md`, `TELAS_COMENTARIOS.md` | Proposta confundível com funcionalidade pronta | Status e links reforçados |
| `DESIGN_SYSTEM.md` | Não apontava para o guia de contribuição | Conectado |
| `index.md`, `mkdocs.yml` | Não davam acesso direto a todos os temas | Índice e navegação ampliados |
| `IMPLEMENTACAO_26_36_37.md` | Registro de Release 1, não representa a arquitetura atual | Mantido como arquivo histórico, fora do menu |

A revisão de documentação não altera a implementação nem comprova implantações
de banco. O novo nome público do produto é tratado exclusivamente na #171 para
evitar sobreposição de PRs.

## Limites e fontes de verdade

- **Em produção:** o comportamento deve ser confirmado nas rotas e no deploy;
  o [guia de hospedagem](HOSPEDAGEM.md) distingue configuração de publicação efetiva.
- **Banco:** o SQL em [migrations](migrations/001_initial_schema.sql) mostra o
  esquema versionado. As políticas aplicadas no projeto Supabase precisam ser
  verificadas no ambiente; uma migração no Git não comprova sua execução.
- **RLS e autorização:** a [auditoria](AUDITORIA_SEGURANCA.md) é um registro
  histórico, enquanto [cibersegurança](CIBERSEGURANCA.md) acompanha mudanças em
  andamento. Não confundir a análise de 02/11 com o estado posterior.
- **Comentários e moderação:** documentos e desenhos são propostas, não telas
  funcionais. As regras dependem de aprovação e implementação específica.
- **Histórico:** [Release 1](https://github.com/unb-mds/2026-2-AvaliaAiUnB/blob/main/RELEASE-v1.0.0.md),
  [Release 2](https://github.com/unb-mds/2026-2-AvaliaAiUnB/blob/main/RELEASE-v2.0.0.md) e
  [implementações antigas](https://github.com/unb-mds/2026-2-AvaliaAiUnB/blob/main/docs/IMPLEMENTACAO_26_36_37.md) registram entregas
  passadas; não devem substituir as instruções atuais.

## Manutenção e validação

1. Alterou uma rota, tabela, tela ou workflow? Atualize sua página de referência
   e revise os documentos relacionados na tabela.
2. Prefira links relativos para páginas internas; preserve nomes de arquivos,
   URLs permanentes e identificadores usados pelo código.
3. Rode `python -m unittest discover -s tests -t .` para mudanças de código.
4. Rode `mkdocs build --strict` para a documentação e verifique links
   internos, títulos e navegação antes do PR.
5. Use o [Definition of Ready e Definition of Done](PROCESSO_CONTRIBUICAO.md).
