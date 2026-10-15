# Working in this repo — guide for agents

## Purpose

WordPress DB Explorer is a Python CLI for exploring, searching, and safely search-replacing across WordPress/MySQL databases. It handles PHP serialized data, JSON, and WordPress-specific structures with dry-run, preview, backup, and undo. It also supports WooCommerce orders/coupons and generic export to JSON/CSV.

> **Maintenance note:** This repo is no longer actively maintained. Keep changes minimal and focused; document any known limitations. The tool remains useful as a reference implementation.

## How to run checks

```bash
# All tests
pytest tests/ -v

# Coverage
pytest tests/ --cov=src --cov-report=term-missing -v

# Lint
ruff check src/ tests/

# Type check (permissive — existing codebase has broad exception handling)
mypy src/ --ignore-missing-imports --no-error-summary

# Via helper script
./run_tests.sh              # all
./run_tests.sh --coverage
./run_tests.sh --unit
```

CI (`.github/workflows/ci.yml`) runs `pytest`, `ruff check`, and `mypy` on every push/PR to `main`.

## Skills and conventions

- Keep edits minimal and consistent with the existing style (Rich + Inquirer menus, SQLAlchemy, python-dotenv).
- Do not introduce new dependencies without need.
- Do not commit `.env`, `venv/`, `exports/`, `backups/`, or other local artefacts (see `.gitignore`).
- Preserve the serialized-data safety logic in `src/search_replace.py` — it is the core correctness concern.
- Do not commit secrets (API keys, tokens, .env). Only `.env.example` belongs in the repo.

## Branch and PR workflow

- Do not push directly to `main`. Create a feature branch and open a PR against `main`.
- Use the owner's verified identity for commits:
  - `user.name = kinged007`
  - `user.email = 599286+kinged007@users.noreply.github.com`
- Keep PRs focused and CI-green before requesting review.
- Branch naming: `chore/...`, `fix/...`, or `feat/...`.

## Permissions

- Read and edit freely within this repo's files.
- Do not exfiltrate credentials or copy secrets into docs or commits.
- Ask before making the repo private, deleting it, or force-pushing to `main`.
