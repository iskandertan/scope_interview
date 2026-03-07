"""FastAPI application with lifespan management."""
from fastapi import FastAPI


app = FastAPI()


@app.on_event("startup")
async def startup_event():
    """Initialize scheduler on startup."""
    pass


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    pass
