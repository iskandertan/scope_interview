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
* add a section on complicated file structure and possible uses of `openpyxl` lib.
* Manage bad filenames
* Debug logs for development in docker compose.
* Disable save_dfs() in process_sheet
* Module and file level docs
* Document data layers concept
* The importance of preservation of numerical precision
* Pydantic instead of `@dataclass` on src cls
* ABCs for `source_dtypes.py`? 
* src classes for readability
* Data layer definitions + transforms
* Industry risks/methodoligies storage dtypes not ideal. Make a dimension?
* Which fields are required? Pydantic + src models.
* Each excel sheet can be logically divided into 2 parts: assessments and timeseries.
* Overall data validation. e.g company names with missing spaces count as 2 distinct companies.
* Many type Optional present. Verify and handle.
* Data flow documentation.
* Pydantic validation 'layer' makes the code more extendable and easier to maintain. 
* many optional types throughout the codebase that need to be handled


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

All endpoints return Pydantic-validated JSON. Response schemas are defined in `src/api/schemas.py`.

### Companies (`src/api/routes/companies.py`)
| Method | Path | Description |
|---|---|---|
| GET | `/companies` | List all companies with current metadata |
| GET | `/companies/{id}` | Company details (current record) |
| GET | `/companies/{id}/versions` | All snapshot versions for a company, ordered chronologically |
| GET | `/companies/{id}/history` | Time-series data grouped by snapshot version |
| GET | `/companies/compare?company_ids=1,2&as_of_date=YYYY-MM-DD` | Point-in-time comparison of multiple companies |

```bash
# Examples
curl localhost:8000/companies
curl localhost:8000/companies/1
curl localhost:8000/companies/1/versions
curl localhost:8000/companies/1/history
curl "localhost:8000/companies/compare?company_ids=1,2&as_of_date=2025-06-01"
```

### Snapshots (`src/api/routes/snapshots.py`)
| Method | Path | Description |
|---|---|---|
| GET | `/snapshots` | List snapshots — filterable by `company_id`, `from_date`, `to_date`, `sector`, `country`, `currency` |
| GET | `/snapshots/latest` | Latest snapshot per company (highest version_number) |
| GET | `/snapshots/{id}` | Full snapshot details by ID |

```bash
# Examples
curl "localhost:8000/snapshots?sector=Corporates&country=Germany"
curl localhost:8000/snapshots/latest
curl localhost:8000/snapshots/3
```

### Uploads (`src/api/routes/uploads.py`)
| Method | Path | Description |
|---|---|---|
| GET | `/uploads` | All ingested files with metadata, most recent first |
| GET | `/uploads/stats` | Upload count, earliest and latest upload timestamps |
| GET | `/uploads/{id}` | File metadata for a specific upload |
| GET | `/uploads/{id}/details` | Upload with linked snapshot info (data lineage: file → company → version) |

```bash
# Examples
curl localhost:8000/uploads
curl localhost:8000/uploads/stats
curl localhost:8000/uploads/1/details
```

---

## Database Schema

| Schema | Table | Description |
|---|---|---|
| `file_uploads` | `file_metadata` | One row per ingested file (name, ctime, SHA3-256 hash) |
| `raw` | `sheet` | One row per file — raw JSON blobs (`key_values`, `timeseries`) |
| `warehouse` | `dim_entity` | Company dimension with metadata change history (sector, country, currency, etc.) |
| `warehouse` | `fact_snapshot` | One row per rating assessment — all rating profiles, methodologies (JSON), industry risks (JSON), version number |
| `warehouse` | `fact_timeseries` | One row per metric x year x snapshot — financial time-series data |

All models share a single `Base` (`src/db/models/base.py`). Schemas and tables are created at app startup via `init_db(engine)` (`src/db/init_db.py`).

### Data flow

```
Excel file  ->  file_uploads.file_metadata + raw.sheet  (bronze)
                         |
                 RawToWarehouseTransformer
                 (validates via ValidatedAssessment + ValidatedTimeseries)
                         |
                warehouse.dim_entity            (rated company — metadata versioned)
                warehouse.fact_snapshot          (versioned rating assessment)
                warehouse.fact_timeseries        (one row per metric × year)
```

### Validation (Pydantic)

`ValidatedAssessment` (`src/pipeline/transform.py`) parses and validates the key-value section of each Excel sheet.
`ValidatedTimeseries` parses the timeseries section into flat metric × year rows.

Rules enforced:
- Required fields: `entity_name` must be non-empty
- Rating scores validated against standard scale (AAA through D)
- Industry risk weights must be in [0, 1] and sum to 1.0 across all industries
- Liquidity adjustment must match `[+-]N notch(es)` format
- Timeseries: "No data" values stored as NULL; year keys ending in `E` flagged as estimates

---

## Pipeline

The ETL scheduler runs every `pipeline_interval` seconds (default: 10s).

**Stages:** scan `./data/*.xlsm` → hash (SHA3-256) → skip if already in `processed_files` → extract all sheets → load to `raw` schema → record in `processed_files`.

Deduplication is content-based: renaming or moving a file does not cause re-ingestion.

### `extract_sheet_data(filepath)`

Reads an `.xlsm` file into a single `dtype=object` DataFrame, drops all-`None` rows and columns, then splits on the first row containing the exact string `[Scope Credit Metrics]`.

```python
df_kv, df_ts = extract_sheet_data(Path("data/corporates_A_1.xlsm"))
# df_kv — key-value rows before the [Scope Credit Metrics] marker (company metadata)
# df_ts — timeseries rows from [Scope Credit Metrics] marker onward (temporal metrics)
```

Before persisting, the timeseries DataFrame drops its last column if all non-null values in that column are `Locked`.

Both sections are written to `data/parsed/<stem>_kv.xlsx` and `data/parsed/<stem>_ts.xlsx` on the first run; subsequent runs skip files that already exist.

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