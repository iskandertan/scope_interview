# Excelsior

A FastApi application that combines a corporate credit rating data pipeline and a set of API endpoints to serve the processed data . Ingests `.xlsm` files dropped into `./data/`, parses the MASTER sheet, stores raw data in PostgreSQL, validates and transforms into a star-schema warehouse, and exposes everything via FastAPI.

The application utilises Data Layers concept transitioning data from raw -> warehouse schemas based on the validation logic in `/pipeline/transform.py`

Example responses can be found in [sample_outputs.md](/sample_outputs.md)

The original interview task can be found in [the_original_task/README.md](the_original_task/README.md).

## Quick Start

```bash
docker compose up --build --watch
```

The app will restart automatically with changes to `watch:` folders in `docker-compose.yml`

`uv run pytest tests/ -v` runs before uvicorn starts — the API only comes up if all tests pass.

- API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

### Clean Rebuild

```bash
docker compose down -v && docker compose rm -f -v && docker compose down --rmi all && docker compose build --no-cache && docker compose up -d
```

### Run Tests Locally

```bash
uv run pytest tests/ -v
```

Tests use in-memory SQLite — no PostgreSQL required.

---
## Project Structure

```
src/
├── api/                  # FastAPI app, routes, Pydantic response schemas
│   └── routes/           # companies, snapshots, uploads, pipeline
├── db/                   # SQLAlchemy engine, session, init, ORM models
│   └── models/           # base, raw_layer, warehouse_layer, schema definitions
└── pipeline/             # ETL: extract, transform, orchestrate, schedule

tests/                    # pytest — unit + integration (SQLite-backed)
data/                     # Drop .xlsm files here; pipeline picks them up
data/debug/               # Parsed Excel sheets dumped here on first run
the_original_task/        # Original assignment brief + AI_USAGE.md
```

---

## API Endpoints

All endpoints return Pydantic-validated JSON. Schemas in `src/api/schemas.py`.

### Companies (`src/api/routes/companies.py`)
| Method | Path | Description |
|---|---|---|
| GET | `/companies` | All companies with current metadata |
| GET | `/companies/{id}` | Company details (current record) |
| GET | `/companies/{id}/versions` | All snapshot versions, chronological |
| GET | `/companies/{id}/history` | Time-series data grouped by snapshot version |
| GET | `/companies/compare?company_ids=1,2&as_of_date=YYYY-MM-DD` | Point-in-time comparison |

### Snapshots (`src/api/routes/snapshots.py`)
| Method | Path | Description |
|---|---|---|
| GET | `/snapshots` | Filterable by `company_id`, `from_date`, `to_date`, `sector`, `country`, `currency` |
| GET | `/snapshots/latest` | Latest snapshot per company |
| GET | `/snapshots/{id}` | Full snapshot details |

### Uploads (`src/api/routes/uploads.py`)
| Method | Path | Description |
|---|---|---|
| GET | `/uploads` | All ingested files, most recent first |
| GET | `/uploads/stats` | Upload count + timestamp range |
| GET | `/uploads/{id}` | File metadata for a specific upload |
| GET | `/uploads/{id}/details` | Upload with linked snapshot info (data lineage) |
| GET | `/uploads/{id}/file` | Download original source file |

### Pipeline (`src/api/routes/pipeline.py`)
| Method | Path | Description |
|---|---|---|
| GET | `/pipeline/runs` | Recent pipeline runs with execution metrics |
| GET | `/pipeline/runs/latest` | Most recent run with full details |
| GET | `/pipeline/runs/{id}` | Specific run with quality report |
| GET | `/pipeline/quality-report` | Data quality report from latest run |

```bash
# Example calls
curl localhost:8000/companies
curl localhost:8000/companies/1/history
curl "localhost:8000/companies/compare?company_ids=1,2&as_of_date=2025-06-01"
curl "localhost:8000/snapshots?sector=Corporates&country=Germany"
curl localhost:8000/uploads/1/details
curl localhost:8000/pipeline/quality-report
```

---

## Database Schema

| Schema | Table | Purpose |
|---|---|---|
| `file_uploads` | `file_metadata` | One row per ingested file (name, ctime, SHA3-256 hash) |
| `raw` | `sheet` | Raw JSON blobs per file (`assessment`, `timeseries`) |
| `warehouse` | `dim_entity` | Company dimension — SCD Type 2 for metadata changes |
| `warehouse` | `fact_snapshot` | Rating assessment per version — methodologies + industry risks as JSON |
| `warehouse` | `fact_timeseries` | One row per metric × year × snapshot |
| `pipeline` | `pipeline_run` | Execution metrics, errors, quality report per run |

All schemas and tables are created at app startup via `init_db()` in `src/db/init_db.py`.


#### Raw layer. Raw and file_uploads schemas

![alt text](</screenshots/raw_layer.png>)

#### Warehouse layer/schema

![alt text](</screenshots/warehouse_schema.png>)
---



### Data Flow

```
.xlsm file  →  file_uploads.file_metadata + raw.sheet     (raw layer)
                         │
                 RawToWarehouseTransformer
                 (Pydantic: ValidatedAssessment + ValidatedTimeseries)
                         │
                warehouse.dim_entity                        (company dimension)
                warehouse.fact_snapshot                      (versioned rating)
                warehouse.fact_timeseries                    (metric × year)
                         │
                pipeline.pipeline_run                        (execution report)
```

### Validation (Pydantic)

`ValidatedAssessment` and `ValidatedTimeseries` in `src/pipeline/transform.py` enforce:

- `entity_name` must be non-empty
- Rating scores validated against standard scale (AAA–D)
- Industry risk weights must be in [0, 1] and sum to 1.0
- Liquidity adjustment must match `[+-]N notch(es)` format
- "No data" timeseries values stored as NULL; year keys ending in `E` flagged as estimates

---

## Pipeline

The ETL scheduler runs every `PIPELINE_INTERVAL` seconds (default: 10s).

**Stages:** scan `./data/*.xlsm` → SHA3-256 hash → skip if already ingested → extract MASTER sheet → load to `raw` schema → validate via Pydantic → transform to `warehouse` schema → record pipeline run.

Deduplication is content-based (SHA3-256). Renaming a file does not cause re-ingestion.

**Retry:** exponential backoff (base=2s, max 3 attempts) per file. Permanent failures are logged in the quality report.

**Metrics per run:** files scanned/ingested/skipped, transform success/failure counts, timeseries points loaded, validation errors, total duration. Accessible via `/pipeline/quality-report`.

### Excel Parsing (`extract_sheet_data`)

Reads `.xlsm` into a single `dtype=object` DataFrame, drops all-None rows/columns, splits on the row containing `[Scope Credit Metrics]`. The part above the marker is key-value company metadata; below is timeseries. A trailing column of all `Locked` values is dropped.

Debug output is written to `data/debug/<stem>_kv.xlsx` and `data/debug/<stem>_ts.xlsx` on first run.

---

## Configuration (`.env`)

```
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=excelsior
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/excelsior
LOG_LEVEL=INFO
PIPELINE_INTERVAL=10    # seconds, optional
```

---

## DevOps

**Python version sync:** `.python-version` is the single source of truth. Both Dockerfiles read it at build time.

Upgrading python version is possible by simply running
```bash
uv python pin 3.12 && uv sync && docker compose up --build
```

**Hot reload:** `docker compose up` uses `Dockerfile.dev` with uvicorn `--reload` and `compose watch` for live sync of `./src`.

**Log levels:** configurable via `LOG_LEVEL` in `.env` (DEBUG, INFO, WARNING, ERROR).

---

## Tests

| File | Scope | Covers |
|---|---|---|
| `conftest.py` | Fixtures | In-memory DB, session, data factories, test client |
| `test_transform.py` | Unit | Pydantic validators, rating validation, liquidity format |
| `test_extract_file_metadata.py` | Unit | SHA3-256 hashing, `get_metadata()` |
| `test_process_sheet.py` | Unit | `split_dfs()`, split marker detection, industry risk nesting |
| `test_src_dtypes.py` | Unit | `SrcFileMetadata.to_orm()`, `SrcRawExcel.to_orm()`, frozen dataclass |
| `test_api.py` | Integration | All REST endpoints — CRUD, filtering, 404s, compare |
| `test_transformer_integration.py` | Integration | Full transform, SCD Type 2 upserts, version incrementing |

---

## Tech Stack

FastAPI, PostgreSQL 15, SQLAlchemy 2, Pydantic, pandas, uv, pytest, Docker.

---

## AI Usage

See [`the_original_task/AI_USAGE.md`](the_original_task/AI_USAGE.md). Tools used: Claude Opus 4.6, Claude Haiku 4.5.

---

## What I Would Change
Following the requirements given in the original task, I understood that I must commit to a monolith application. 

Another obvious thing that is missing is response caching. Responses for HTTP requests need to be cached based on timer or LRU logic minimizing network communication.

**Architecture:** Break the FastAPI monolith. The pipeline and httpresponse endpoints are two distinct components that should be separated into two different software components. Something like Airflow would fit well here for running the pipeline and managing layer transitions. It would also provide observability, robustness and a GUI. 
- **Airflow:** watches `./data/`, launches DAGs per new file, manages ETL and data layer transitions.
- **FastAPI:** read-only data access + response caching only.


**Error handling:** Remove any code that raises unrecoverable exceptions, since it blocks the entire app. Pipeline failures should be captured and reported, never crash the server. There are a bunch of `raise` statements in this codebase. Put here for development and debugging purposes. All of these statements need to be handled before the application is prod ready. 

**CI/CD:** Add pre-commit hooks for linting, formatting, testing etc. `ruff` is a good starting point.

**Dependency management:** Separate `dev` dependencies (ruff, pytest) from production via uv extras. There's no need to have a 'heavy' .venv with things that are not needed for prod runtime. 

**Prod Dockerfile:** There's a Dockerfile that is supposed to be used for production runs. It's a good starting point but far from being optimal. The app runs with `Dockerfile.dev`

**Database:** Add connection pooling (pgpool or SQLAlchemy pool tuning) for production workloads.

**Pipeline:** Add multiprocessing/async concurrency for parallel file processing. In the case where monolith is a requirement. There definitely needs to be a way to process files without blocking the main event loop and we would also need the ability to handle concurrency in the case of increased file loads. 

**Data model:**
- Reduce overly-broad `Optional` fields in Pydantic models and ORM — define which fields are truly required.
