# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

AvaliaAi UnB — a Flask + SQLite web app for students to search, rate and compare UnB professors and courses (academic project for MDS/UnB). Code, identifiers, comments and user-facing strings are in **Portuguese**; keep new code consistent with that. `docs/DOCUMENTO_DE_VISAO.md` is the source of truth for requirements (MVP vs. post-MVP features, rating criteria: didática, clareza, organização, disponibilidade, dificuldade). Project constraints: Python + Flask backend, SQLite for the MVP (PostgreSQL planned later), LGPD compliance.

## Commands

There is no `requirements.txt`; the only dependency is Flask (Werkzeug comes with it).

```bash
pip install flask
python run.py                      # dev server at http://127.0.0.1:5000 (debug=True)
python -m app.database             # create banco.db tables without starting the server
python -m unittest app.test_avaliacoes                                          # run tests
python -m unittest app.test_avaliacoes.TestAvaliacoes.test_inserir_e_buscar_avaliacao  # single test
```

Flask must be installed even for the tests, since importing any `app.*` module runs `app/__init__.py` (which imports Flask). Run everything from the repo root: `app/database.py` uses the relative path `banco.db`, so the DB file is created in the current working directory. No linter/formatter is configured.

## Architecture

Layered, following the README diagram: routes/controllers → repositories → SQLite.

- `run.py` — entry point; calls `app.create_app()`. Named `run.py` (not `app.py`) on purpose to avoid clashing with the `app/` package.
- `app/__init__.py` — app factory: registers blueprints and calls `inicializar_banco()` on startup (schema is created with `CREATE TABLE IF NOT EXISTS`; there are no migrations, so schema changes to existing tables require deleting/altering `banco.db`).
- `app/database.py` — schema (`usuarios`, `avaliacoes`, `sessoes`) and `get_db_connection()`, which returns a connection with `row_factory = sqlite3.Row` and `PRAGMA foreign_keys = ON`. Always use this helper rather than `sqlite3.connect` directly. No ORM — raw parameterized SQL, one connection opened and closed per operation.
- `app/models.py` — plain classes (`Usuario`, `Avaliacao`) with `to_dict()`; `Usuario.to_dict()` deliberately omits `senha`.
- `app/repositorio.py` — repository classes (currently `UsuarioRepository`) that map rows to models; `criar_usuario` returns a `(sucesso, mensagem)` tuple and turns `IntegrityError` (duplicate email) into a failure message.
- `app/routes/` — Flask blueprints (`auth_bp`, endpoint names like `auth.login`). Routes serve Jinja templates on GET and return JSON on POST.
- `app/controllers/session_controller.py` — server-side session management, used instead of Flask's signed-cookie session:
  - `criar_sessao(usuario_id, response)` generates a random token, stores only its **SHA-256 hash** in `sessoes` (12h expiry), and sets the raw token in the httponly, `secure=True`, `SameSite=Lax` cookie `avaliaai_session`.
  - `obter_usuario_atual()` resolves the user from the cookie (cached in `flask.g`, deletes expired sessions lazily) and returns a `sqlite3.Row` (`id, nome, email`), not a `Usuario` model.
  - `@login_required` returns 401 JSON for API clients or redirects to `auth.login` for browsers, based on the `Accept` header.
  - `encerrar_sessao(response)` deletes the DB row and the cookie (real server-side revocation).
- Passwords: the `usuarios.senha` column stores the Werkzeug `generate_password_hash` output, verified with `check_password_hash`. Login errors are intentionally generic.

## Gotchas

- `app/app.py` is a stale leftover (imports a nonexistent `init_db` and uses non-package imports); it is not used by `run.py`.
- `app/test_avaliacoes.py` builds its own in-memory schema rather than using `app/database.py`, so it does not catch drift from the real schema.
- `avaliacoes.professor_id` has no foreign key yet — there is no professors table (being modeled on branch `issue-29-modelar-professores`).
- There is no `.gitignore`; `__pycache__/` and `banco.db` are committed, so avoid staging accidental changes to them.
