# TODOs
* Can't parse some field from a xls. Notify + store.
* CI/CD:
    - pre-commit hooks
    - ruff + unused imports
    - tests
    - deploy
    - git revert
* Imitate data initialization by loading files in order into a folder at compose up to solve duplicate/latest problem.
* Excel MACROs - do I need to deal with this?
* `/data` lifecycle.
* pipeline notificaion
* `docker-compose up` start-up.
* delete all containers and start from scratch for testing
* check for redundancies at the end
* `.venv` handling
* delete useless ai comments
* Test `Dockerfile`
* uv env separation. `dev` for ruff and tests.
* pgpool for connections
* redundancies in dependencies
* swagger docs
* `compose watch:` feature documentation and how-to
* `/tests` for xlsm processing module
* multiprocessing for `pipeline`; import concurrent.futures and import asincio?
* GET /favicon.ico HTTP/1.1" 404 Not Found
* The correct way to declare all tables at start-up using sqlalch orm. Basemodel.
* `docker-compose down -v && docker-compose rm -f -v && docker compose down --rmi all && docker-compose build --no-cache && docker-compose up -d`
* `fs` abstraction when working with xlsm files


---

# Excelsior

Corporate credit rating data pipeline. Ingests `.xlsm` files dropped into `./data/`, stores raw rows in PostgreSQL, and exposes the data via a FastAPI REST API.

## Quick Start

```bash
docker compose up --build --watch
```

API at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

---

## API Endpoints

### Companies
| Method | Path | Description |
|---|---|---|
| GET | `/companies` | List all companies (latest metadata) |
| GET | `/companies/{id}` | Company details (latest version) |
| GET | `/companies/{id}/versions` | All versions for a company |
| GET | `/companies/{id}/history` | Time-series data |
| GET | `/companies/compare?company_ids=&as_of_date=` | Point-in-time comparison |

### Snapshots
| Method | Path | Description |
|---|---|---|
| GET | `/snapshots` | List snapshots — filterable by `company_id`, `from_date`, `to_date`, `sector`, `country`, `currency` |
| GET | `/snapshots/latest` | Latest snapshot per company |
| GET | `/snapshots/{id}` | Specific snapshot |

### Uploads
| Method | Path | Description |
|---|---|---|
| GET | `/uploads` | All ingested files with metadata |
| GET | `/uploads/stats` | Upload count |
| GET | `/uploads/{id}` | Specific upload details |

### Pipeline
| Method | Path | Description |
|---|---|---|
| POST | `/pipeline/trigger` | Trigger a pipeline run (async, returns 202) |
| GET | `/pipeline/status` | Processed file count |

---

## Database Schema

| Schema | Table | Description |
|---|---|---|
| `raw` | `file_uploads` | One row per ingested file |
| `raw` | `sheet_rows` | One row per spreadsheet row (JSONB `data` column) |
| `pipeline_state` | `processed_files` | Deduplication log — keyed by SHA3-256 content hash |

Schemas and tables are created at app startup (`src/db/init_db.py`).

---

## Pipeline

The ETL scheduler runs every `pipeline_interval` seconds (default: 10s).

**Stages:** scan `./data/*.xlsm` → hash (SHA3-256) → skip if already in `processed_files` → extract all sheets → load to `raw` schema → record in `processed_files`.

Deduplication is content-based: renaming or moving a file does not cause re-ingestion.

---

## Configuration (`.env`)

```
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=excelsior
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/excelsior
LOG_LEVEL=INFO
```

Add `PIPELINE_INTERVAL=<seconds>` to override the 10s default.

---

## DevOps

### Python version sync
The Python version is the single source of truth in `.python-version` (managed by `uv`). To bump:

```bash
uv python pin 3.12      # updates .python-version
uv sync                 # regenerates uv.lock
docker compose up --build
```

Both `Dockerfile` and `Dockerfile.dev` read `.python-version` at build time — no hardcoded version anywhere. The running Python version is logged at FastAPI startup.

### Hot reload (development)
`docker compose up` uses `Dockerfile.dev` with uvicorn `--reload` and `compose watch` for live sync of `./src` into the container.

### Logging
Log level is set by the LOG_LEVEL env var. #TODO: address log level in config.py + docker-compose set up.

---

## Tech Stack

- **FastAPI** — REST API, OpenAPI/Swagger docs
- **PostgreSQL 15** — data warehouse
- **SQLAlchemy 2** — ORM + schema management
- **openpyxl** — `.xlsm`/`.xlsx` parsing
- **uv** — Python packaging and version management

---

## What I Would Change

Break the FastAPI monolith into separate concerns. Proposed architecture: **Airflow → DWH → FastAPI**.
- Airflow: watches `./data/`, launches DAGs per new file, manages ETL and data layer transitions.
- FastAPI: read-only data access + response caching only.