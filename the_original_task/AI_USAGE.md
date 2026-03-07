# AI Coding Assistance Disclosure

This assignment requires transparency about AI tool usage during development.

## Instructions
Please complete the sections below honestly. Using AI tools is **acceptable and expected**. We want to understand **how** you used them.


## 1. AI Tools Used
Claude Opus 4.6
Claude Haiku 4.5


## 2. Components Assisted
Check which parts received AI assistance:

- [ ] Data extraction logic (Excel parsing, MASTER sheet)
- [ ] Data modeling design (ERD, table schemas, SCD Type 2)
- [ ] ETL pipeline implementation
- [ ] Data validation framework
- [ ] API endpoint development (FastAPI)
- [ ] Docker/Docker Compose configuration
- [ ] SQL queries and migrations
- [ ] Testing (unit/integration tests)
- [ ] Documentation (README, comments)
- [ ] Debugging specific issues
- [ ] Other: ___________


## 3. Detailed Description
For each major component, describe how AI assisted.

1. Create file structure and add boilerplate.


## 4. Chat History / Logs
Attach or link to chat history logs showing AI interactions.

1. File structure and boilerplate: (following the request + readme.md upload in a different chat)
```
I want this folder structure for my project. Keep the original task
project/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
├── README.md
│
├── data/ # Mounted volume — interviewer drops Excel files here
│ ├── inbox/ # New/unprocessed files go here
│ └── processed/ # Files moved here after successful processing
│
├── src/
│ ├── init.py
│ ├── config.py # Settings via pydantic-settings (DB URL, intervals, paths)
│ │
│ ├── db/
│ │ ├── init.py
│ │ ├── session.py # Engine, SessionLocal factory
│ │ ├── init_db.py # Creates schemas + tables on startup
│ │ └── models/
│ │ ├── init.py
│ │ ├── raw.py # SQLAlchemy models for raw schema
│ │ ├── warehouse.py # Dims + facts (star schema)
│ │ └── pipeline_state.py # Tracks processed files, pipeline runs
│ │
│ ├── pipeline/
│ │ ├── init.py
│ │ ├── orchestrator.py # run_pipeline() — scans inbox, processes each file
│ │ ├── extract.py # Excel parsing → Python dicts
│ │ ├── validate.py # Quality checks → QualityReport objects
│ │ ├── load_raw.py # Dicts → raw schema tables
│ │ ├── transform.py # raw schema → warehouse schema (dimensional)
│ │ └── scheduler.py # asyncio loop (30s) + run_in_executor
│ │
│ ├── api/
│ │ ├── init.py
│ │ ├── app.py # FastAPI app, lifespan (starts scheduler)
│ │ ├── dependencies.py # get_db session, common query params
│ │ ├── routes/
│ │ │ ├── init.py
│ │ │ ├── properties.py # Property endpoints
│ │ │ ├── tenants.py # Tenant endpoints
│ │ │ ├── leases.py # Lease endpoints
│ │ │ ├── pipeline.py # POST /pipeline/trigger, GET /pipeline/status
│ │ │ └── quality.py # GET /quality-reports
│ │ └── schemas/
│ │ ├── init.py
│ │ └── responses.py # Pydantic response models (NOT DB models)
│ │
│ └── common/
│ ├── init.py
│ ├── hashing.py # File content hashing for dedup
│ └── logging.py # Logging config
│
└── tests/
├── conftest.py # Fixtures: test DB, test client, sample Excel files
├── test_extract.py # Unit: Excel parsing edge cases
├── test_validate.py # Unit: quality checks
├── test_transform.py # Unit: dimensional model correctness
├── test_pipeline.py # Integration: full pipeline run
└── test_api.py # Integration: API endpoints
```


```
Please make sure that my uv environemnt for docker is compliant with
https://docs.astral.sh/uv/guides/integration/docker/

My goal is to have the container rebuild on changes to source code. After file has been saved.
```

```
Make sure that python versions in docker envs are synced to whatever is specified in .python-version.

is there a way to control it from a single place? I only want to make a single change. So for instance, If i ever decide to bump my python version, i only need to do the uv command for that and the docker envs will be updated automatically. It would be nice if i could control ARG PYTHON_VERSION=3.10 not from the dockerfile
```

```
make sure that my home route for a fast api app returns something.

Deal with depreceated on_event in app.py

initialize db schemas on the first run
```

```
make sure that pipeline module is executed every 10 seconds.

propose a fool-proof starting point for parsing xlsm files in my pipeline. Make sure that the files are initially processed and all the infor present in the single file is stored in the raw schema

when pipeline runs every 10 seconds, it needs to process files under /data.

every file that's been processed needs to be persisted in the database. Store fname and all file metadata that you can get and file hash. Use the latest sha.
```

```
do a filesystem refactor, change names, delete uselsess things. Look at the README.md in /the_original_task folder for reference. Simplify the existing implementations afterwards
```

**Format:** PDF, Markdown, screenshots, or text files
**Location:** [Provide links or attach files here]

**Note:** You may redact personal information but maintain enough context to show the AI interaction.


## 5. Self-Assessment
Reflect on your AI usage:

**What did AI do well?**

**What did you need to correct or override?**

**What did you implement entirely on your own?**

**How did AI tools improve your development process?**

**Were there any limitations or challenges with AI assistance?**


## 6. Recommendations
Based on your experience, what advice would you give to others using AI tools for data engineering tasks?




Thank you for your transparency!
