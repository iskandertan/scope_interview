"""FastAPI application with lifespan management."""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import settings
from src.db.init_db import init_db_schemas
from src.db.session import init_engine
from src.pipeline.scheduler import start_scheduler

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Python %s", sys.version)
    engine = init_engine(settings.database_url)
    init_db_schemas(engine)
    logger.info("Database schemas initialized")
    scheduler_task = asyncio.create_task(start_scheduler())
    yield
    scheduler_task.cancel()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"name": "scope-interview", "status": "ok"}
