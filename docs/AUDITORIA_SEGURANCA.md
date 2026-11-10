# Auditoria de Segurança

**Registro histórico, não checklist de correções implantadas.**

Auditoria feita em 02/11/2026, na Sprint 7 (issue #111). O objetivo foi saber se existe algum problema grave de segurança no projeto e ter um plano de correção por prioridade.

## Resultado

Não foi encontrado nenhum problema crítico. Foram encontrados 1 achado de prioridade alta, 3 de prioridade média e 8 de prioridade baixa. Cada um tem uma issue com o plano de correção.

## O que foi verificado

- **Chave de serviço do Supabase:** onde é usada, se aparece no código, no histórico do Git ou no navegador.
- **Políticas de RLS:** consulta ao banco para ver quais tabelas têm RLS ligado e quais políticas existem.
- **Dependências:** pip-audit nos arquivos `requirements.txt` e `requirements-scraper.txt`.
- **Análise estática:** bandit em `app/` e `scraper/`.
- **Checklist OWASP Top 10:** injeção, autenticação, controle de acesso, XSS, CSRF e exposição de dados.
- **Acesso indevido:** edição e exclusão da avaliação de outro usuário, e páginas protegidas sem login, conferidas no código e nos testes automatizados.

## O que está bem

- A chave de serviço não está escrita no código, nunca foi commitada (o `.env` está no `.gitignore` e não aparece no histórico) e não chega ao navegador.
- Os dois arquivos de dependências estão sem vulnerabilidades conhecidas (pip-audit).
- O bandit não encontrou problemas de severidade média ou alta.
- As 5 tabelas do banco têm RLS ligado. Sem nenhuma política criada, a chave pública não lê nem grava nada.
- Os cookies de sessão usam `HttpOnly`, `Secure` (configurável para desenvolvimento local) e `SameSite=Lax`.
- Todos os formulários POST têm token CSRF.
- Não há uso de `|safe`, `autoescape` desligado nem consulta montada por texto. O Jinja escapa os valores do usuário.
- Editar e excluir uma avaliação conferem o dono pela sessão (`usuario_id`), no controller e no repositório. Quem não é o dono recebe 404. Existem testes para esses casos.
- `/perfil` e `/avaliar` exigem login, com testes.

## Achados

| # | Achado | Prioridade | Issue |
|---|---|---|---|
| 1 | O script em `docs/migrations/` não liga o RLS. Um banco criado só com ele nasce aberto à chave pública. Hoje também não existe nenhuma política criada | Alta | #123 |
| 2 | O site usa a chave de serviço, que ignora o RLS. A autorização depende só do código | Média | #124 |
| 3 | O cadastro marca o e-mail como confirmado (`email_confirm: True`) sem verificar | Média | #125 |
| 4 | O logout pode não revogar a sessão quando o token de acesso já expirou (o refresh token continua válido) | Média | #126 |
| 5 | O CSRFProtect é iniciado duas vezes e o token vale 1 hora em vez de 12 h | Baixa | #127 |
| 6 | O limite de login por username permite travar a conta de outra pessoa; o contador é por worker e `PROXY_HOPS` vale 0 | Baixa | #127 |
| 7 | Enumeração de usuário por tempo de resposta e pela mensagem do cadastro | Baixa | #127 |
| 8 | `select('*')` em `avaliacoes` traz mais campos do que o necessário | Baixa | #127 |
| 9 | `@limitar_avaliacao` fica antes de `@login_required` e gera carga em requisição anônima | Baixa | #127 |
| 10 | `nome` e senha sem limite de tamanho | Baixa | #127 |
| 11 | `FLASK_DEBUG` ligado em produção expõe o depurador | Baixa | #127 |
| 12 | 6 blocos `except: pass` no scraper (bandit B110) e `print` da URL do Supabase | Baixa | #127 |

Também não existe teste de `/avaliacoes/<id>/editar` e `/excluir` sem login. Está listado na #127.

## Limites desta auditoria

- Foi uma revisão do código, dos testes e da configuração do banco. Não foi feito teste de invasão.
- Não foram lidos linha a linha `app/supabase_db.py`, `app/models.py`, `app/utils.py`, os arquivos em `static/` e os templates `comparacao.html`, `ranking.html` e `perfil_professor.html`. Neles foi procurado apenas `|safe` e formulários POST.
- Mudanças feitas depois de 02/11/2026, como o PR de navegação de retorno (#122), não foram cobertas e precisam de revisão própria.

## Próximos passos

As correções ficam nas issues #123 a #127, na Sprint 8.
Consulte o [resumo de cibersegurança](CIBERSEGURANCA.md) para o acompanhamento
das correções, o [modelo de dados](Modelo%20de%20Dados.md) para o SQL versionado
e o [pipeline](pipeline.md) para os checks atuais.
