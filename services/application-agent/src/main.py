"""
Application Agent - Main FastAPI Application

Monitors LLM output quality, detects regressions, and validates optimization changes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.core.config import settings
from src.core.logger import logger
from src.core.registration import orchestrator_client
from src.api import (
    health,
    quality,
    regression,
    validation,
    workflow,
    llm,
    configuration,
    bulk,
    analytics,
    admin,
)
from src.api import application_routes_v2  # Phase 6.5


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.agent_name} v{settings.version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Port: {settings.port}")
    
    # Register with orchestrator
    if settings.registration_enabled:
        success = await orchestrator_client.register()
        if success:
            await orchestrator_client.start_heartbeat()
        else:
            logger.warning("Failed to register with orchestrator, continuing anyway")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Application Agent")
    if settings.registration_enabled:
        await orchestrator_client.deregister()


# Create FastAPI app
app = FastAPI(
    title="Application Agent",
    description="Quality monitoring and regression detection for LLM applications",
    version=settings.version,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(quality.router)
app.include_router(regression.router)
app.include_router(validation.router)
app.include_router(workflow.router)
app.include_router(llm.router)
app.include_router(configuration.router)
app.include_router(bulk.router)
app.include_router(analytics.router)
app.include_router(admin.router)

# V2 Routes (Phase 6.5 - ClickHouse Readers)
app.include_router(application_routes_v2.router, tags=["applications-v2"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "agent": settings.agent_name,
        "version": settings.version,
        "status": "active",
        "agent_id": settings.agent_id
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development"
    )
