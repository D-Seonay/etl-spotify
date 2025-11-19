
# etl-spotify

Lightweight ETL and import tools for Spotify streaming history into a PostgreSQL database.

This repository contains SQLAlchemy entities, Alembic migrations, an ETL runner, and an API router to import Spotify streaming history JSON files exported from the Spotify app. **Now with Spotify Web API integration** to enrich data with real IDs, popularity scores, genres, and cover images.

**What you'll find**
- `entity/` — SQLAlchemy models for `user`, `track`, `artist`, `album`, `history`, etc.
- `migrations/` & `alembic.ini` — Alembic configuration and migration scripts.
- `data/` — sample Spotify streaming history JSON files used for imports.
- `modules/` — Import modules with Spotify API enrichment
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
- **IMPORTANT**: Configure your Spotify API credentials (see [Spotify API Setup](#spotify-api-setup))

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

## Spotify API Setup

🔑 **Required for data enrichment**

The import system uses the Spotify Web API to enrich your listening history with:
- ✅ Real Spotify IDs (no more hash-generated IDs)
- ✅ Track popularity, duration, and cover images
- ✅ Artist popularity, genres, and profile pictures
- ✅ Album release dates, total tracks, and cover images

### Get your Spotify API credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Copy your **Client ID** and **Client Secret**
4. Add them to your `.env` file:

```bash
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

📖 See [SPOTIFY_API_SETUP.md](SPOTIFY_API_SETUP.md) for detailed instructions.

### Test your API connection

```bash
python test_spotify_api.py
```

This will verify your credentials and test the enrichment process.

## Importing Spotify History

### 📋 Three import methods available:

#### 1. Via CLI Script (Recommended for testing)

```bash
python test_import.py data/Streaming_History_Audio_2021-2024_0.json
```

#### 2. Via FastAPI (Recommended for production)

Start the API server:
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Then import via HTTP request:
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/import-data" \
  -H "Authorization: Bearer your_api_key" \
  -F "file=@data/Streaming_History_Audio_2021-2024_0.json" \
  -F "user_id=your_user_id"
```

Or test with the provided script:
```bash
python test_api_endpoint.py
```

📖 See [API_USAGE.md](API_USAGE.md) for complete API documentation.

#### 3. Via ETL runner

```bash
python etl.py --dir data/
```

### 📊 What happens during import:

1. **Parse JSON** - Extract listening history entries
2. **Enrich with Spotify API** - Get real IDs, popularity, genres, images, etc. (batch processing, ~50 tracks at a time)
3. **Insert to database** - Store enriched data with duplicate handling

### ⏱️ Expected time:

- 500 tracks: ~2-3 minutes
- 2000 tracks: ~5-10 minutes

Notes:
- The `data/` directory contains example files like `Streaming_History_Audio_2021-2024_0.json`.
- Import routines parse timestamped play events and enrich them with Spotify API data.
- Duplicates are automatically handled with `ON CONFLICT DO NOTHING` clauses.
- Progress is displayed in real-time during enrichment.

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

