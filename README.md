# TODOs
* Can't parse some field from a xls. Notify + store.
* CI/CD:
    - pre-commit hooks
    - ruff
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


# Requirements Detailed
* Extract only MASTER sheet
    - Fields: 
        - Company metadata (entity name, sector, country, currency)
        - Rating methodology information
        - Industry risk scores and weights
        - Accounting principles and business year-end data
    - Field k:v Errors: TODO (The MASTER sheet has a non-standard structure (key-value pairs with "Unnamed" column headers) that requires custom parsing.)
    - Sheet naming Errors: lower case MASTER, many master_n, master not found

# Open questions:
* Cache during data load. Always go through cache.

----
# DevOps Features

## Python version sync
The Python version is controlled from a single source of truth: `.python-version` (managed by `uv`).

To bump the Python version across all environments:
Update `pyproject.toml` file with `requires-python = "==3.12.*"`, then run:

```bash
uv python pin 3.12   # updates .python-version
uv lock              # regenerates uv.lock for the new version
docker compose up --build --watch
```

Both `Dockerfile` and `Dockerfile.dev` read `.python-version` at build time via `uv python install`, so no version is hardcoded in any Dockerfile. The running Python version is logged at FastAPI startup.

----
# Tech Stack

## DWH - PostgreSQL 15
Data storage.

## Excelcior - FastApi
Monolith 

# What I would change
Break down fastapi monolith. To have a better separation of concerns and remove a single point of failure for the entire data platform. My proposed architecture: Airflow -> DWH -> FastApi. 
* Airflow would continuously watch the data source location. Launch DAGs whenver there's a new file. DAGs would be responsible for loading data into a DWH and transitioning it through Data Layers.
* FastApi app would only be responsible for returning the data and doing the response caching.