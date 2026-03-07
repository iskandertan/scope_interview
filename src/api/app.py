import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes import companies, pipeline, snapshots, uploads
from src.db.init_db import init_db_schemas
from src.db.session import engine
from src.pipeline.scheduler import start_etl_scheduler

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Init database and start pipeline scheduler on app startup."""
    logger.info("Python %s", sys.version)
    init_db_schemas(engine)
    logger.info("Database schemas initialized")
    scheduler_task = asyncio.create_task(start_etl_scheduler())
    yield
    scheduler_task.cancel()


app = FastAPI(lifespan=lifespan)

app.include_router(companies.router)
app.include_router(snapshots.router)
app.include_router(uploads.router)
app.include_router(pipeline.router)


@app.get("/")
async def root():
    return {"name": "excelsior", "status": "ok"}
