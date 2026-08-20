# AGENTS.md

## Commands

- Fast backend gate: `python -m ruff check src tests && python -m pytest -m "unit or api" -q --maxfail=1`
- All backend tests: `python -m pytest -q --maxfail=1`
- Integration tests: `pytest -m integration -q` (needs MySQL + Redis running)
- External tests: `pytest -m external -q` (needs Weibo cookie / remote NLP)
- Format/lint: `pre-commit run --all-files` or `black src/ tests/ && isort src/ tests/ && ruff check src/ tests/`
- Windows dev start: `scripts\start.bat` (Flask 5000 + Vite 3000). Stop with `scripts\start.bat stop`
- Full quality gate: `pwsh -NoProfile -File scripts/verify_project.ps1`
- Frontend: `cd frontend && npm ci && npm run lint && npm run test:run && npm run build`

## Architecture

- Two-service app: Flask backend (`src/`) + Vue frontend (`frontend/`). No shared root package.
- Backend entrypoint: `run.py`. It inserts `src/` onto `sys.path`; imports inside `src/` rely on this.
- App object is also exposed as `run:app` for Gunicorn (`gunicorn -w 2 -b 0.0.0.0:5000 run:app`).
- Blueprint routes live under `src/views/`. API paths: `/api/*`, `/getAllData/*`, `/user/*`.

## Testing

- `pytest.ini` adds `src` to `pythonpath` and defaults to `testpaths = tests`.
- `tests/conftest.py` auto-sets `TEST_DATABASE_URL=sqlite:///:memory:` and monkeypatches Celery to `memory://` backend with `task_always_eager=True` for every test session.
- Temp files are redirected to `.pytest_tmp/temp` to avoid polluting system temp.
- Do not assume Redis/MySQL is available in unit/api tests; they must pass without external services.

## Env / Config

- `src/config/settings.py` auto-loads `.env` via `python-dotenv`. `.env.example` is the source of truth for supported vars.
- Production requires `SECRET_KEY`, `JWT_SECRET_KEY`, `ALLOWED_ORIGINS`, `ADMIN_USERS` set; `Config.validate()` raises at startup otherwise.
- Database URL defaults to MySQL via `Config.get_database_url()`. Override with `TEST_DATABASE_URL` for tests.

## Docker

- `docker compose up -d --build` spins up MySQL, Redis, backend, frontend, spider-api/worker, nlp-api/worker.
- Local Windows dev does not need Docker; `scripts\start.bat` runs Flask + Vite directly without Redis/Celery.
- Spider/NLP services are optional locally. Enable with `SPIDER_SERVICE_ENABLED=True` and `NLP_SERVICE_ENABLED=True` in `.env` if running containers.

## Style / Tooling

- Python: Black (line-length 88), isort (profile=black), Ruff (`E,W,F,I,B,C4,UP`; ignores `E501,B008,B905`).
- Frontend: ESLint + Prettier + Vitest.
- Pre-commit hooks are defined in `.pre-commit-config.yaml`; install with `pre-commit install`.

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default canonical labels (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout (`CONTEXT.md` at repo root + `docs/adr/`). See `docs/agents/domain.md`.
