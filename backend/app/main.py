from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.router import api_router
from app.core.config import settings
from app.db.mongodb import close_mongo_connection, connect_to_mongo, mongo_manager
from app.services.vector_db_service import VectorDbService

# Configure structured logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("carboniq.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application lifecycle: connects to MongoDB and initializes vector DB on boot."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} [{settings.ENVIRONMENT}]")
    await connect_to_mongo()
    # Initialize Qdrant client connection pool non-blockingly
    try:
        VectorDbService.get_client()
    except Exception as qdrant_err:
        logger.warning(f"Qdrant vector database startup note: {qdrant_err}")

    yield

    logger.info("Shutting down CarbonIQ API service...")
    await close_mongo_connection()
    try:
        VectorDbService.close()
    except Exception:
        pass


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for CarbonIQ — AI-powered Sustainability Management Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS configuration strictly restricted to configured frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
async def health_check() -> JSONResponse:
    """
    Health check endpoint returning application status, database connectivity, and vector DB status.
    """
    db_status = "connected" if mongo_manager.is_connected else "disconnected"
    vdb_status = "available" if VectorDbService.is_available() else "unavailable"
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "database": db_status,
            "vector_database": vdb_status,
        },
    )


# Register all domain APIs under /api
app.include_router(api_router)
