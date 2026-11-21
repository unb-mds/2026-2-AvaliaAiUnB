# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

AvaliaUnB — a Flask + Supabase (PostgreSQL) web app for students to search, rate and compare UnB professors and courses (academic project for MDS/UnB). Code, identifiers, comments and user-facing strings are in **Portuguese**; keep new code consistent with that. `docs/DOCUMENTO_DE_VISAO.md` is the source of truth for requirements (MVP vs. post-MVP features, rating criteria: didática, clareza, organização, disponibilidade, dificuldade). Project constraints: Python + Flask backend, Supabase (PostgreSQL) for persistence, LGPD compliance.

## Commands

```bash
pip install -r requirements.txt
python run.py                                    # dev server at localhost:5000 (debug off by default)
pytest                                           # run all tests (no network: they use tests/fake_supabase.py)
python -m unittest discover -s tests -t .        # alternative unittest runner
python -m unittest tests.test_login_google.TestLoginGoogle.test_primeiro_acesso_cria_perfil_e_sessao   # single test
python -m mkdocs build --strict                  # build documentation site strictly
```

The app needs `SECRET_KEY`, `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in the environment or root `.env` (git-ignored; see `.env.example`). `SECRET_KEY` is mandatory for signed Flask sessions and CSRF. Tests inject a test-only `SECRET_KEY` and `SUPABASE_CLIENT` via `create_app(config)` without real credentials. `FLASK_DEBUG` defaults to off; enable it only for local development. All POST forms require a CSRF token and the matching Flask session cookie, including tests. Run everything from the repo root.

## Architecture

Layered: routes → controllers → repositories → Supabase (PostgreSQL).

- `run.py` — entry point; calls `app.create_app()`. Named `run.py` (not `app.py`) on purpose to avoid clashing with the `app/` package.
- `app/__init__.py` — app factory: builds repositories (`configurar_repositorios`), initializes security (`seguranca.py`), registers the session after-request hook and blueprints.
- `app/supabase_db.py` — lazy Supabase client from the `.env` service key (`get_supabase()`; `novo_cliente()` gives a throwaway client for the Google code exchange and token refresh). Server-side only.
- `app/repositorio.py` — `UsuarioRepository` (Supabase Auth + `perfis`), `ProfessorRepository` (professores + view `vw_professor_disciplina`, 5-min catalog cache, ordered by number of avaliações), `AvaliacaoRepository` (médias, optionally per semestre; one avaliação per user/professor/disciplina/semestre cursado — the user picks the turma in the form, issue #252), `ComentarioRepository`, `DenunciaRepository`, `FavoritoRepository` (personal list of favorite professors). `repositorios()` returns the instances from `current_app.extensions`.
- `app/models.py` — plain data classes mirroring the tables. `app/validacoes.py` — input validation (`CRITERIOS`, notas das avaliações). `app/utils.py` — `normalizar_busca`. `app/grafico.py` — coordinates for the server-side SVG chart of grades per semester on the professor profile (issue #224; no JS, no inline style because of the CSP; data from `AvaliacaoRepository.medias_por_semestre`).
- `app/seguranca.py` — CSRF protection (`Flask-WTF`), rate limiting (`Flask-Limiter`), CSP/security headers, and internal URL validation (`is_safe_url`).
- `app/verificacao_email.py` — institutional UnB e-mail verification via SMTP and SHA-256 hash stored in `emails_verificados`.
- `app/routes/` — thin blueprints (`main_bp`, `auth_bp`, `professor_bp`; endpoints like `auth.login`). Browsers (HTML) get redirects/templates; API clients get JSON.
- `app/controllers/` — `auth_controller` (login com Google), `professor_controller` (perfil, médias, registrar/editar/excluir avaliação, ranking, comparação), `session_controller` (below).
- Auth: **only Google sign-in** (Supabase Auth Google provider, PKCE). `/login/google` stores the PKCE verifier in the Flask session and redirects to Supabase; `/login/google/retorno` exchanges the code (`exchange_code_for_session`). On first login `UsuarioRepository._garantir_perfil` creates the `perfis` row (name from Google, unique lowercase `username` derived from the e-mail) and syncs `nome`/`username` into `user_metadata`. Old password accounts with the same e-mail are linked by Supabase to the same user id. There is no password signup, login or reset anymore; `/cadastro` redirects to `/login`. `avaliacoes.usuario_id` is a FK to `perfis`. Tests log in with `tests/fake_supabase.py` helpers `entrar_pela_web` / `sessao_google`.
- `session_controller` stores the Supabase access token and refresh token in httponly, `secure=True`, `SameSite=Lax` cookies (`avaliaai_session`, `avaliaai_refresh`). `obter_usuario_atual()` validates the token with Supabase (cached in `flask.g`), refreshes it when expired, and returns a dict (`id, nome, email, username`). `@login_required` returns 401 JSON for API clients or redirects to `auth.login`. `encerrar_sessao` revokes the session on Supabase.

## Database Migrations (`docs/migrations/`)

- `001_initial_schema.sql` — initial PostgreSQL schema (`perfis`, `professores`, `disciplinas`, `turmas`, `avaliacoes`, view `vw_professor_disciplina`, and RLS policies).
- `002_comentarios.sql` — dedicated `comentarios` table (FKs to `perfis`, `professores`, `disciplinas`; text length 2–1000 chars; soft-hide via `ocultado_em`; trigger `set_atualizado_em`; RLS policies restricting public reads to non-hidden rows and writes to the author for disciplines taught by that professor).
- `003_emails_verificados.sql` — `emails_verificados` table (`usuario_id` PK/FK to `perfis`, `endereco_sha256`, RLS restricted to `service_role`).
- `004_professores_unicos.sql` — merges professors duplicated across units (moves `turmas`, `avaliacoes`, `comentarios` to the kept row) and replaces `UNIQUE (nome, departamento)` with `UNIQUE (nome)` (issue #235).
- `007_avaliacao_por_semestre.sql` — replaces the `avaliacoes` unique key with `(usuario_id, professor_id, disciplina_id, ano, periodo)` (one avaliação per turma cursada) and adds `idx_avaliacoes_professor_semestre` (issue #252). `006` is the favoritos migration from the #223 branch.
- `005_denuncias_comentarios.sql` — private `denuncias_comentarios` table (motivo CHECK, optional explicação ≤ 500, `resolvida_em`; partial unique index = one active report per user/comment; RLS with no grants to `anon`/`authenticated`) (issue #215).
- `006_favoritos.sql` — `favoritos` table (PK `(usuario_id, professor_id)`, FKs to `perfis`/`professores`, `criado_em`; RLS: `authenticated` only selects/inserts/deletes own rows, nothing for `anon`) (issue #223). `FavoritoRepository`; route `POST /professores/<id>/favorito` (`acao=adicionar|remover`, optional internal `destino`); list shown in `/perfil`.

## Gotchas

- Comments are modeled in their own `comentarios` table (`docs/migrations/002_comentarios.sql`), **not** in `avaliacoes.comentario`.
- Session cookie names (`avaliaai_session`, `avaliaai_refresh`) intentionally keep the `avaliaai_` prefix for compatibility; do not rename them casually.
- `scraper/` is separate: it has its own `supabase_client.py` and populates `professores`, `disciplinas`, and `turmas`. A professor is unique by `nome` (upsert with `ignore_duplicates`, so `departamento` keeps the first unit seen). `scraper/manutencao_banco.py duplicatas|backup` reports duplicates and regenerates the CSVs in `docs/backup/`.
- Semester data refresh runs via `.github/workflows/atualizar-dados-sigaa.yml` (manual `workflow_dispatch`: `dry-run` without secrets, or `gravar` gated by the `producao` environment, which holds `SUPABASE_URL`/`SUPABASE_SERVICE_KEY` and opens a PR with `docs/backup`). `scraper-fumaca.yml` dry-runs unit 673 on PRs touching the scraper. `requirements-scraper.txt` needs `setuptools` because `undetected-chromedriver` still imports `distutils`. The scraper reads optional `CHROME_BINARY` / `CHROME_VERSION_MAIN` (`cli_sigaa.opcoes_chrome`); the workflows set them because the Actions runner also has Chromium, which `undetected-chromedriver` may launch instead of Google Chrome, causing a driver version mismatch.
- `docs/IMPLEMENTACAO_26_36_37.md` is an archived Release 1 historical record (from the initial SQLite prototype) and does not reflect the current Supabase/PostgreSQL architecture.