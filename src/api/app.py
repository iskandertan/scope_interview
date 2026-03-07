"""FastAPI application with lifespan management."""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import settings
from src.db.init_db import init_db_schemas
from src.db.session import init_engine

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Python %s", sys.version)
    engine = init_engine(settings.database_url)
    init_db_schemas(engine)
    logger.info("Database schemas initialized")
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"name": "scope-interview", "status": "ok"}
