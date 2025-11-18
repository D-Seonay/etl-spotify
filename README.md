
# etl-spotify

Lightweight ETL and import tools for Spotify streaming history into a PostgreSQL database.

This repository contains SQLAlchemy entities, Alembic migrations, an ETL runner, and an API router to import Spotify streaming history JSON files exported from the Spotify app.

**What you'll find**
- `entity/` — SQLAlchemy models for `user`, `track`, `artist`, `album`, `history`, etc.
- `migrations/` & `alembic.ini` — Alembic configuration and migration scripts.
- `data/` — sample Spotify streaming history JSON files used for imports.
- `api/` — FastAPI routers (e.g. import endpoint) and security helpers.
- `etl.py` — small runner to import/process files (see usage).
- `main.py` — FastAPI application entrypoint.
- `scripts/create_db.py` — helper to create tables directly from models (development only).
- `docker-compose.yml` — optional PostgreSQL service for local development.

## Quick Start (development)

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

2. Configure environment variables

- Copy `.env.example` to `.env` (or create `.env`) and set your DB connection values. The app looks for `DATABASE_URL` or the `DB_*` variables.

3. Start a local Postgres (optional)

```bash
docker compose up -d
```

4. Apply database migrations

```bash
# from repo root
alembic upgrade head
```

Alternatively (development only) you can create tables from models:

```bash
python scripts/create_db.py
```

## Importing Spotify History

There are two ways to import the Spotify JSON streaming history:

- Using the ETL runner:

```bash
# imports files listed or entire data/ folder depending on implementation
python etl.py --dir data/ 
```

- Using the API router (FastAPI):

1. Run the API server:

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

2. Use the import endpoint under `/api/v1/...` (see `api/v1/router/import_spotify_history_data.py`) to POST files or trigger an import job.

Notes:
- The `data/` directory in the repository contains example files named like `Streaming_History_Audio_2021-2024_0.json`.
- Import routines will typically parse timestamped play events and insert or upsert related `track`, `artist`, `album`, and `history` rows.

## Running the ETL locally

Typical steps for a one-off import:

```bash
source .venv/bin/activate
export DATABASE_URL="postgresql://user:pass@localhost:5432/yourdb"
python etl.py --files data/Streaming_History_Audio_2024-2025_1.json
```

Adjust the command-line flags to match the runner's implementation (check `etl.py` for options).

## Development notes

- Alembic loads metadata from `entity.base` and will use `DATABASE_URL` if set, otherwise builds the URL from `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`.
- To create a new migration after model changes:

```bash
alembic revision --autogenerate -m "describe changes"
alembic upgrade head
```

- Use `scripts/create_db.py` only for quick local experiments — prefer Alembic for reproducible schema changes.

## Troubleshooting

- If Alembic cannot import the models, run commands from the repository root so the `entity` package is on `PYTHONPATH`.
- If `psycopg2` build fails, use `psycopg2-binary` in development or install system libs (`libpq-dev`) for production builds.

## CI / Production recommendations

- Keep secrets out of the repo. Use `.env` for local development and a secrets manager for production.
- Run migrations as part of your deploy pipeline.

## Contributing

Feel free to open issues or PRs. When adding or changing models, include an Alembic migration and update the tests (if present).

## Useful commands

- Start Postgres: `docker compose up -d`
- Install deps: `pip install -r requirements.txt`
- Run migrations: `alembic upgrade head`
- Run API: `uvicorn main:app --reload`
- Run ETL: `python etl.py --help`

---

If you'd like, I can also:
- Add example `.env.example` contents to the README.
- Add a small usage example of the FastAPI import endpoint (curl or HTTPie commands).

