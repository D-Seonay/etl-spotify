# etl-spotify — Database setup and migrations

This repository contains SQLAlchemy entities under `entity/`. This README explains how to create the database, run migrations with Alembic and use Docker Compose for a PostgreSQL instance.

## Quick start (development)

1. Create and activate a virtualenv, then install dependencies:

```bash
python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

2. Configure DB connection using `.env` (example `.env.example` present). For development you can keep the example values.

3. Start PostgreSQL using Docker Compose (optional — you can use SQLite fallback):

```bash
docker compose up -d
```

The compose file loads credentials from `.env`.

4. Run Alembic migrations to create the schema:

```bash
# ensure your env contains DATABASE_URL or DB_* values from .env
alembic upgrade head
```

Alternatively, you can run the included script to create tables directly from SQLAlchemy metadata (not recommended for production):

```bash
python scripts/create_db.py
```

## Alembic notes
- Alembic is configured to load `entity.base.Base` metadata from the project, and will read the DB URL from `DATABASE_URL` env var or construct it from `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`.
- To generate a new migration after changing models:

```bash
alembic revision --autogenerate -m "describe changes"
```

- Then review the generated migration file under `alembic/versions/` and apply it:

```bash
alembic upgrade head
```

## Security and best practices
- Do NOT commit secrets in `.env`. Keep a `.env.example` with placeholder values and add `.env` to `.gitignore`.
- For production, prefer using a secrets manager or Docker secrets instead of env vars in files.
- Use Alembic migrations (not `Base.metadata.create_all`) to manage schema changes.

## Troubleshooting
- If `alembic` cannot import `entity.base`, ensure you run commands from the repo root so `entity` package is on `PYTHONPATH`.
- If installing `psycopg2` fails during pip install, prefer `psycopg2-binary` for local development (already in `requirements.txt`). For production, install `libpq-dev` and system build tools before building `psycopg2`.

If you want, I can:
- Create an initial migration file (already added) and run it against a running Postgres container here (requires Docker running and dependencies installed).
- Add a small CI job example that runs Alembic migrations.
