"""Scheduler using asyncio loop (10 s interval)."""

import asyncio
import logging

from src.config import settings
from src.pipeline.orchestrator import run_pipeline

logger = logging.getLogger(__name__)


async def start_etl_scheduler() -> None:
    """Run the pipeline every ``settings.pipeline_interval`` seconds forever."""
    logger.info("Pipeline scheduler started (interval=%ds)", settings.pipeline_interval)
    while True:
        try:
            await run_pipeline()
        except Exception:
            logger.exception("Unhandled error during pipeline execution")
        await asyncio.sleep(settings.pipeline_interval)
