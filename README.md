# Excelsior

This is a solution for a technical round interview at Scope Group.

A FastApi application that combines a corporate credit rating data pipeline and a set of API endpoints to serve the processed data. Ingests `.xlsm` files dropped into `./data/`, parses the MASTER sheet, stores raw data in PostgreSQL, validates and transforms into a star-schema warehouse, and exposes everything via FastAPI.

The application utilises Data Layers concept transitioning data from raw -> warehouse schemas based on the validation logic in `/pipeline/transform.py`

Example responses can be found in [sample_outputs.md](/sample_outputs.md)

The original interview task can be found in [the_original_task/README.md](the_original_task/README.md).

AI Usage - [`the_original_task/AI_USAGE.md`](the_original_task/AI_USAGE.md).

## Quick Start

```bash
docker compose up --build --watch
```

The app will restart automatically with changes to `watch:` folders specified in `docker-compose.yml`

`uv run pytest tests/ -v` runs before uvicorn starts — the API only comes up if all tests pass.

- API: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

### Starting with clean volumes
``` bash
docker compose down -v && docker compose up --build --watch
```

### Clean Rebuild of everything

```bash
docker compose down -v && docker compose rm -f -v && docker compose down --rmi all && docker compose build --no-cache && docker compose up --watch
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
data/debug/               # Visualising DataFrames to debug raw ingestion
the_original_task/        # Original assignment brief + AI_USAGE.md
```

---

## API Endpoints

All endpoints return Pydantic-validated JSON. Schemas in `src/api/schemas.py`.

To make test requests use the `/docs` endpoint.

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

---

## Database Schema

| Schema | Table | Purpose |
|---|---|---|
| `file_uploads` | `file_metadata` | One row per ingested file (name, ctime, SHA3-256 hash) |
| `raw` | `sheet` | Raw JSON blobs per file (`assessment`, `timeseries`) |
| `warehouse` | `dim_entity` | Company dimension — SCD Type 2 for metadata changes |
| `warehouse` | `fact_snapshot` | Rating assessment per version — methodologies + industry risks as JSON |
| `warehouse` | `fact_timeseries` | One row per metric × year × snapshot |

All schemas and tables are created at app startup via `init_db()` in `src/db/init_db.py`.


#### Raw layer. Raw and file_uploads schemas

![alt text](</screenshots/raw_layer.png>)

#### Warehouse layer/schema

![alt text](</screenshots/warehouse_schema.png>)
---



### Data Flow

On application startup and every `Settings.pipeline_interval` seconds, run `/src/pipeline` module 

```
.xlsm file  →  file_uploads.file_metadata + raw.sheet -> write to raw layer
                         │
                 RawToWarehouseTransformer
                 (Pydantic: ValidatedAssessment + ValidatedTimeseries)
                         │
                warehouse.dim_entity                        (company dimension)
                warehouse.fact_snapshot                      (versioned rating)
                warehouse.fact_timeseries                    (metric × year)
```
### Abstraction into classes
For readability and data documentation purposes, data that is being stored in the raw layer is ingested as classes in `/src/pipeline/src_dtypes.py`

### Validation (Pydantic)
Validation happens when data is ready to be transitioned from raw into a warehouse schema. As well as on the api responses.

* Layer transitions are handled by `class RawToWarehouseTransformer:` in `pipeline/transform.py`
* Response validation is handled in `api/schemas.py`

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
