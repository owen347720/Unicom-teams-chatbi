# backend/app/main.py

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.database import init_db
from app.routers import (
    ask_router,
    datasource_router,
    settings_router,
    training_router,
)


def setup_logging():
    """Configure logging"""
    logger.remove()
    logger.add(
        "/app/logs/app.log",
        rotation="10 MB",
        retention="30 days",
        level=settings.log_level,
    )
    logger.add(
        lambda msg: print(msg, end=""),
        level=settings.log_level,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    setup_logging()
    logger.info("Starting Text2SQL Backend API...")
    await asyncio.to_thread(init_db)
    logger.info("Database tables initialized")
    yield
    # Shutdown
    logger.info("Shutting down Text2SQL Backend API...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(datasource_router, prefix="/api/v1")
app.include_router(training_router, prefix="/api/v1")
app.include_router(ask_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "backend_api": "healthy",
            "vanna_service": "checking...",
            "postgres": "checking...",
        },
    }


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }
