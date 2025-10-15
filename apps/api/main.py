"""
BetterBros Props API - Main FastAPI Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from src.config import settings
from src.routers import (
    props,
    context,
    features,
    model,
    corr,
    optimize,
    eval_router,
    export,
    snapshots,
    experiments,
    keys,
    whatif,
    history,
    auth,
)
from src.db import check_db_connection, check_redis_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown"""
    # Startup
    logger.info("Starting BetterBros Props API")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Auth Provider: {settings.AUTH_PROVIDER}")

    # Verify connections on startup
    db_healthy = await check_db_connection()
    redis_healthy = await check_redis_connection()

    if not db_healthy:
        logger.warning("Database connection check failed on startup")
    if not redis_healthy:
        logger.warning("Redis connection check failed on startup")

    yield

    # Shutdown
    logger.info("Shutting down BetterBros Props API")


app = FastAPI(
    title="BetterBros Props API",
    description="AI-powered props betting optimization platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint that verifies service and dependency status
    """
    db_status = await check_db_connection()
    redis_status = await check_redis_connection()

    overall_healthy = db_status and redis_status

    health_data = {
        "status": "healthy" if overall_healthy else "degraded",
        "service": "betterbros-props-api",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "dependencies": {
            "database": "healthy" if db_status else "unhealthy",
            "redis": "healthy" if redis_status else "unhealthy",
        },
    }

    status_code = 200 if overall_healthy else 503
    return JSONResponse(content=health_data, status_code=status_code)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "service": "BetterBros Props API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# Mount all routers with appropriate prefixes and tags
app.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

app.include_router(
    props.router,
    prefix="/props",
    tags=["Props Markets"],
)

app.include_router(
    context.router,
    prefix="/context",
    tags=["Context Data"],
)

app.include_router(
    features.router,
    prefix="/features",
    tags=["Feature Engineering"],
)

app.include_router(
    model.router,
    prefix="/model",
    tags=["Model Predictions"],
)

app.include_router(
    corr.router,
    prefix="/correlations",
    tags=["Correlations"],
)

app.include_router(
    optimize.router,
    prefix="/optimize",
    tags=["Optimization"],
)

app.include_router(
    eval_router.router,
    prefix="/eval",
    tags=["Evaluation"],
)

app.include_router(
    export.router,
    prefix="/export",
    tags=["Export"],
)

app.include_router(
    snapshots.router,
    prefix="/snapshots",
    tags=["Snapshots"],
)

app.include_router(
    experiments.router,
    prefix="/experiments",
    tags=["Experiments"],
)

app.include_router(
    keys.router,
    prefix="/keys",
    tags=["API Keys"],
)

app.include_router(
    whatif.router,
    prefix="/whatif",
    tags=["What-If Analysis"],
)

app.include_router(
    history.router,
    prefix="/history",
    tags=["Historical Data"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.ENVIRONMENT == "development" else "An unexpected error occurred",
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level="info",
    )
