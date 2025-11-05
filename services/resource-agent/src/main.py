"""
Resource Agent - Main Application

FastAPI application for GPU/CPU/memory resource optimization.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from src.config import settings
from src.core.logger import logger
from src.core.registration import orchestrator_client
from src.api import health, gpu, system, analysis, lmcache, optimize
from src.api import resource_routes_v2  # Phase 6.5


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info(f"Starting Resource Agent: {settings.agent_id}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Port: {settings.port}")
    
    # Register with orchestrator
    await orchestrator_client.register()
    
    # Start heartbeat task
    heartbeat_task = asyncio.create_task(orchestrator_client.start_heartbeat())
    
    yield
    
    # Shutdown
    logger.info("Shutting down Resource Agent")
    
    # Cancel heartbeat task
    heartbeat_task.cancel()
    try:
        await heartbeat_task
    except asyncio.CancelledError:
        pass
    
    # Deregister from orchestrator
    await orchestrator_client.deregister()


# Create FastAPI app
app = FastAPI(
    title="Resource Agent",
    description="AI-powered GPU/CPU/memory resource optimization agent",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(gpu.router)
app.include_router(system.router)
app.include_router(analysis.router)
app.include_router(lmcache.router)
app.include_router(optimize.router)

# V2 Routes (Phase 6.5 - ClickHouse Readers)
app.include_router(resource_routes_v2.router, tags=["resources-v2"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "agent": "Resource Agent",
        "version": "1.0.0",
        "status": "active",
        "agent_id": settings.agent_id
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True if settings.environment == "development" else False
    )
