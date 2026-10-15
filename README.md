# WordPress DB Explorer

[![CI](https://github.com/kinged007/wordpress-db-explorer/actions/workflows/ci.yml/badge.svg)](https://github.com/kinged007/wordpress-db-explorer/actions/workflows/ci.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](pyproject.toml)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Maintenance note:** This project is no longer actively maintained. It remains available as a reference implementation for WordPress database exploration and safe search-replace. Issues and PRs are welcome but may not be reviewed promptly.

A CLI for exploring, searching, and safely search-replacing across WordPress/MySQL databases — serialized-data and WooCommerce aware. Handles PHP serialized arrays, JSON, and WordPress-specific content with dry-run, preview, and undo safety.

## Features

- **Connection testing** with friendly error messages and URL-encoded credentials
- **Multi-table search** across WordPress core tables and custom post types
- **Search modes**: users, posts, pages, WooCommerce orders/coupons, custom post types, general cross-table search
- **Search & Replace**: multi-table find/replace with highlighted preview, full-width tables, dry-run, selective row/table replacement, automatic backup and undo, and safe handling of PHP serialized data and JSON
- **Export**: JSON/CSV, batch processing, filtered exports, optional metadata, timestamped files in `exports/`
- **UX**: Rich colourised output, progress indicators, Inquirer menus, full terminal-width tables

Supported data: WordPress users (with metadata), posts/pages, WooCommerce orders/coupons, custom post types, any WordPress table.

## Prerequisites

- Python 3.8+ and pip
- MySQL/MariaDB credentials for the target WordPress database
- macOS, Linux, or Windows

## Install

### Quick start (macOS/Linux)

```bash
git clone https://github.com/kinged007/wordpress-db-explorer.git
cd wordpress-db-explorer
cp sample.env .env   # then edit .env with DB credentials
chmod +x run.sh
./run.sh
```

`run.sh` creates a venv, installs dependencies, and launches the app.

### Manual setup (all platforms)

```bash
git clone https://github.com/kinged007/wordpress-db-explorer.git
cd wordpress-db-explorer
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp sample.env .env        # edit with DB credentials
python main.py
```

### Environment

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `3306` |
| `DB_USER` | Database user | `wp_user` |
| `DB_PASSWORD` | Database password | `your_password` |
| `DB_NAME` | WordPress database | `wordpress_db` |
| `TABLE_PREFIX` | Table prefix | `wp_` |

Do not commit `.env` — it is gitignored. See `sample.env` for the template.

## Usage

Launch and pick from the main menu:

```
Select an option:
  1. Test DB Connection
  2. Search
  3. Search & Replace
  4. Export
  Exit
```

- **Test DB Connection** — verify credentials before other operations.
- **Search** — `Search Users` / `Orders` / `Coupons` / `Posts` / `Pages` / `Custom Post Type` / `General Search`. Each supports field-level filtering and metadata search.
- **Search & Replace** — guided workflow: configure search term, select tables, find matches, preview with highlighted terms, configure row selection, set replacement text, dry-run, execute (with backup), and undo. See [SEARCH_REPLACE_README.md](SEARCH_REPLACE_README.md).
- **Export** — Users, WooCommerce Orders/Coupons, Posts, Pages, or any Custom Post Type to `exports/` as JSON or CSV.

## How it is tested

Pytest suite (21 tests) covering serialized-data handling, JSON replacement, length fixing, session management, backup creation, dry-run safety, and error handling. Run via:

```bash
./run_tests.sh              # all tests
./run_tests.sh --coverage   # with HTML + terminal coverage
./run_tests.sh --unit       # unit only
pytest tests/ -v            # direct

# Lint and type checks (as in CI)
ruff check src/ tests/
mypy src/ --ignore-missing-imports
```

CI runs on every push and PR to `main` via [ci.yml](.github/workflows/ci.yml): `pytest`, `ruff`, and `mypy`.

## Project structure

```
wordpress-db-explorer/
├── main.py              # entry point
├── run.sh               # setup + launch (macOS/Linux)
├── run_tests.sh         # test runner
├── pyproject.toml       # pytest / coverage config
├── requirements.txt
├── sample.env           # env template
├── src/
│   ├── db_utils.py
│   ├── search_utils.py
│   ├── search_replace.py
│   ├── export_menu.py
│   └── export_utils.py
├── tests/               # pytest suite
└── venv/                # auto-created
```

## Troubleshooting

- **Database connection failed** — verify `.env` credentials, that MySQL is running, and the user has permissions.
- **Python/pip not found** — install Python 3.8+ from python.org and ensure it is on PATH.
- **Permission denied on run.sh** — `chmod +x run.sh`.
- **Venv issues** — delete `venv/` and re-run setup.

## License

MIT — see [LICENSE](LICENSE). Copyright 2026 kinged007 / Joshua Barnard.

## Contributing

Issues and PRs welcome. Please open PRs against `main` from a feature branch; do not push directly to the default branch.
