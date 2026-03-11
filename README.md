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
* Extra excel files for testing
* Handle `/companies/compare` differences instead of returning 2 dicts for both snapshots.

---

# Excelsior

Corporate credit rating data pipeline. Ingests `.xlsm` files dropped into `./data/`, stores raw rows in PostgreSQL, validates and transforms them into a star-schema warehouse, and exposes the data via a FastAPI REST API.

## Quick Start

```bash
docker compose up --build --watch
```

The container runs `pytest tests/ -v` before starting uvicorn. The API only comes up if all tests pass.

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
| GET | `/uploads/{id}/details` | Upload with linked snapshot info (data lineage: file -> company -> version) |
| GET | `/uploads/{id}/file` | Download original source file |

```bash
curl localhost:8000/uploads
curl localhost:8000/uploads/stats
curl localhost:8000/uploads/1/details
curl -o downloaded.xlsm localhost:8000/uploads/1/file
```

### Pipeline (`src/api/routes/pipeline.py`)
| Method | Path | Description |
|---|---|---|
| GET | `/pipeline/runs` | List recent pipeline runs with execution metrics |
| GET | `/pipeline/runs/latest` | Most recent pipeline run with full details |
| GET | `/pipeline/runs/{id}` | Specific pipeline run with quality report |
| GET | `/pipeline/quality-report` | Data quality report from the latest run |

```bash
curl localhost:8000/pipeline/runs
curl localhost:8000/pipeline/runs/latest
curl localhost:8000/pipeline/quality-report
```

---

## Database Schema

| Schema | Table | Description |
|---|---|---|
| `file_uploads` | `file_metadata` | One row per ingested file (name, ctime, SHA3-256 hash) |
| `raw` | `sheet` | One row per file — raw JSON blobs (`assessment`, `timeseries`) |
| `warehouse` | `dim_entity` | Company dimension with metadata change history (SCD Type 2) |
| `warehouse` | `fact_snapshot` | One row per rating assessment — all rating profiles, methodologies (JSON), industry risks (JSON), version number |
| `warehouse` | `fact_timeseries` | One row per metric x year x snapshot — financial time-series data |
| `pipeline` | `pipeline_run` | One row per pipeline execution — metrics, errors, quality report |

All models share a single `Base` (`src/db/models/base.py`). Schemas and tables are created at app startup via `init_db(engine)` (`src/db/init_db.py`).

### Data flow

```
Excel file  ->  file_uploads.file_metadata + raw.sheet  (raw layer)
                         |
                 RawToWarehouseTransformer
                 (validates via ValidatedAssessment + ValidatedTimeseries)
                         |
                warehouse.dim_entity            (rated company — metadata versioned)
                warehouse.fact_snapshot          (versioned rating assessment)
                warehouse.fact_timeseries        (one row per metric x year)
                         |
                pipeline.pipeline_run            (execution metrics + quality report)
```

### Validation (Pydantic)

`ValidatedAssessment` (`src/pipeline/transform.py`) parses and validates the key-value section of each Excel sheet.
`ValidatedTimeseries` parses the timeseries section into flat metric x year rows.

Rules enforced:
- Required fields: `entity_name` must be non-empty
- Rating scores validated against standard scale (AAA through D)
- Industry risk weights must be in [0, 1] and sum to 1.0 across all industries
- Liquidity adjustment must match `[+-]N notch(es)` format
- Timeseries: "No data" values stored as NULL; year keys ending in `E` flagged as estimates

---

## Pipeline

The ETL scheduler runs every `PIPELINE_INTERVAL` seconds (default: 10s).

**Stages:** scan `./data/*.xlsm` -> hash (SHA3-256) -> skip if already ingested -> extract MASTER sheet -> load to `raw` schema -> validate via Pydantic -> transform to `warehouse` schema -> record pipeline run.

Deduplication is content-based: renaming or moving a file does not cause re-ingestion.

### Retry logic

Each file extraction and metadata step is wrapped in exponential backoff (base=2s, max 3 attempts). Transient I/O failures are retried automatically; permanent failures are logged and reported in the quality report.

### Pipeline metrics and quality reports

Every pipeline run records:
- Files scanned, ingested, and skipped (duplicates)
- Transform success/failure counts and success rate
- Timeseries points loaded
- Validation errors with file IDs
- Total duration

Reports are persisted in `pipeline.pipeline_run` and accessible via `/pipeline/quality-report`.

### `extract_sheet_data(filepath)`

Reads an `.xlsm` file into a single `dtype=object` DataFrame, drops all-`None` rows and columns, then splits on the first row containing the exact string `[Scope Credit Metrics]`.

```python
raw_excel = extract_sheet_data(Path("data/corporates_A_1.xlsm"))
# raw_excel.key_values — key-value rows before marker (company metadata)
# raw_excel.timeseries — timeseries rows from marker onward (temporal metrics)
```

Before persisting, the timeseries DataFrame drops its last column if all non-null values in that column are `Locked`.

Both sections are written to `data/debug/<stem>_kv.xlsx` and `data/debug/<stem>_ts.xlsx` on the first run; subsequent runs skip files that already exist.

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

---

## Tech Stack

- **FastAPI** — REST API, OpenAPI/Swagger docs
- **PostgreSQL 15** — data warehouse
- **SQLAlchemy 2** — ORM + schema management
- **Pydantic** — request/response validation + data quality checks
- **openpyxl** — `.xlsm`/`.xlsx` parsing
- **uv** — Python packaging and version management
- **pytest** — unit and integration testing

---

## Tests

Tests live in `tests/` and use pytest with an in-memory SQLite database (no PostgreSQL required). They also run automatically at container startup before uvicorn launches.

```bash
uv run pytest tests/ -v
```

### Structure

| File | Scope | What it covers |
|---|---|---|
| `conftest.py` | Shared fixtures | In-memory DB engine, session, sample data factories, FastAPI test client |
| `test_transform.py` | Unit | Pydantic validators (`ValidatedAssessment`, `ValidatedTimeseries`, `IndustryRisk`), `validate_raw_data()`, rating validation, liquidity format |
| `test_extract_file_metadata.py` | Unit | SHA3-256 hashing, `get_metadata()` return types |
| `test_process_sheet.py` | Unit | `split_dfs()`, `get_split_marker_row_index()`, `handle_industry_risk_nesting()` |
| `test_src_dtypes.py` | Unit | `SrcFileMetadata.to_orm()`, `SrcRawExcel.to_orm()`, frozen dataclass enforcement |
| `test_api.py` | Integration | All REST endpoints (`/companies`, `/snapshots`, `/uploads`) — CRUD, filtering, 404s, point-in-time compare |
| `test_transformer_integration.py` | Integration | `RawToWarehouseTransformer` — full transform, SCD Type 2 entity upserts, version incrementing, validation failures |

---

## Sample Outputs

See [`sample_outputs.md`](sample_outputs.md) for 14 API call examples with responses, a data quality report example, and a pipeline execution log example.

---

## What I Would Change

Break the FastAPI monolith into separate concerns. Proposed architecture: **Airflow -> DWH -> FastAPI**.
- Airflow: watches `./data/`, launches DAGs per new file, manages ETL and data layer transitions.
- FastAPI: read-only data access + response caching only.
