"""
OptiInfra Cost Agent - Main Application

This is the Cost Agent that optimizes cloud spending through:
- Spot instance migrations
- Reserved instance recommendations
- Instance right-sizing
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import health
from src.config import settings
from src.core.logger import setup_logging
from src.core.registration import register_with_orchestrator

# Setup logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for the FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting OptiInfra Cost Agent")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Port: {settings.port}")

    # Register with orchestrator
    if settings.orchestrator_url:
        try:
            await register_with_orchestrator()
            logger.info("Successfully registered with orchestrator")
        except Exception as e:
            logger.error(f"Failed to register with orchestrator: {e}")
            # Don't fail startup if registration fails

    yield

    # Shutdown
    logger.info("Shutting down Cost Agent")


# Create FastAPI app
app = FastAPI(
    title="OptiInfra Cost Agent",
    description="AI-powered cost optimization agent",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - service information"""
    return {
        "service": "OptiInfra Cost Agent",
        "version": "0.1.0",
        "status": "running",
        "capabilities": [
            "spot_migration",
            "reserved_instances",
            "right_sizing",
        ],
    }


# Run with uvicorn when executed directly
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )
