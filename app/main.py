import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.core.config import settings
from app.core.logging import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle context manager.
    Used for global setup (startup) and teardown (shutdown).
    """
    setup_logging()
    logger.info(f"Application starting with ENV: {settings.ENV}")
    # Initialization is now handled by FastAPI's Dependency Injection system
    # using functions like get_data_service(), get_backtest_engine(), etc.
    # check app/api/dependencies.py file.
    yield
    # Clean up on shutdown (e.g., closing database connections, cleaning temporary files)
    logger.info("Application shutting down")


app = FastAPI(
    lifespan=lifespan,
    title="BITA Backtesting API",
    description="A high-performance financial backtesting API with NLP integration.",
    version="0.1.0",
)
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "BITA Backtest API",
        "version": "0.1.0",
        "status": "running",
        "docs": "https://backtest-api-taj7.onrender.com/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "env": settings.ENV}
