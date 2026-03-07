"""FastAPI application with lifespan management."""

import logging
import sys

from fastapi import FastAPI

logger = logging.getLogger("uvicorn.error")

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    """Initialize scheduler on startup."""
    logger.info("Python version %s", sys.version)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    pass
