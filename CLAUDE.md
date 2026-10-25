# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

AvaliaAi UnB — a Flask + Supabase (PostgreSQL) web app for students to search, rate and compare UnB professors and courses (academic project for MDS/UnB). Code, identifiers, comments and user-facing strings are in **Portuguese**; keep new code consistent with that. `docs/DOCUMENTO_DE_VISAO.md` is the source of truth for requirements (MVP vs. post-MVP features, rating criteria: didática, clareza, organização, disponibilidade, dificuldade). Project constraints: Python + Flask backend, Supabase (PostgreSQL) for the MVP (PostgreSQL planned later), LGPD compliance.

## Commands

```bash
pip install -r requirements.txt
python run.py                                    # dev server at http://127.0.0.1:5000 (debug off by default)
python -m unittest discover -s tests -t .        # run all tests (no network: they use tests/fake_supabase.py)
python -m unittest tests.test_supabase.TestFluxoWeb.test_cadastro   # single test
```

The app needs `SECRET_KEY`, `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in the environment or root `.env` (git-ignored; see `.env.example`). `SECRET_KEY` is mandatory for signed Flask sessions and CSRF. Tests inject a test-only `SECRET_KEY` and `SUPABASE_CLIENT` via `create_app(config)` without real credentials. `FLASK_DEBUG` defaults to off; enable it only for local development. All POST forms require a CSRF token and the matching Flask session cookie, including tests. Run everything from the repo root.

## Architecture

Layered: routes → controllers → repositories → Supabase. There is no local database (Supabase (PostgreSQL)/`banco.db` was removed).

- `run.py` — entry point; calls `app.create_app()`. Named `run.py` (not `app.py`) on purpose to avoid clashing with the `app/` package.
- `app/__init__.py` — app factory: builds repositories (`configurar_repositorios`), registers the session after-request hook and blueprints.
- `app/supabase_db.py` — lazy Supabase client from the `.env` service key (`get_supabase()`; `novo_cliente()` gives a throwaway client for password checks). Server-side only.
- `app/repositorio.py` — `UsuarioRepository` (Supabase Auth + `perfis`), `ProfessorRepository` (professores + view `vw_professor_disciplina`, 5-min catalog cache, ordered by number of avaliações), `AvaliacaoRepository` (médias, one avaliação per user/professor/disciplina). `repositorios()` returns the instances from `current_app.extensions`.
- `app/models.py` — plain data classes mirroring the tables. `app/validacoes.py` — input validation (`CRITERIOS`, cadastro requires an `@gmail.com` address and a username). `app/utils.py` — `normalizar_busca`.
- `app/routes/` — thin blueprints (`main_bp`, `auth_bp`, `professor_bp`; endpoints like `auth.login`). Browsers (HTML) get redirects/templates; API clients get JSON.
- `app/controllers/` — `auth_controller` (cadastro/login), `professor_controller` (perfil, médias, registrar avaliação), `session_controller` (below).
- Auth: accounts live in Supabase Auth (`auth.users`); `perfis` holds the unique lowercase `username` used to log in (username → email → `sign_in_with_password`). `avaliacoes.usuario_id` is a FK to `auth.users`.
- `session_controller` stores the Supabase access token and refresh token in httponly, `secure=True`, `SameSite=Lax` cookies (`avaliaai_session`, `avaliaai_refresh`). `obter_usuario_atual()` validates the token with Supabase (cached in `flask.g`), refreshes it when expired, and returns a dict (`id, nome, email, username`). `@login_required` returns 401 JSON for API clients or redirects to `auth.login`. `encerrar_sessao` revokes the session on Supabase.

## Gotchas

- `avaliacoes.comentario` exists in Supabase but is intentionally unused (comments were removed from the feature).
- `scraper/` is separate: it has its own `supabase_client.py` and populates professores/disciplinas/turmas.
- `docs/IMPLEMENTACAO_26_36_37.md` and parts of the README describe the old Supabase (PostgreSQL) implementation.
