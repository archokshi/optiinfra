"""
OptiInfra Cost Agent - Main Application

This is the Cost Agent that optimizes cloud spending through:
- Spot instance migrations
- Reserved instance recommendations
- Instance right-sizing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
import logging

from src.api import health, analyze
from src.api import aws_costs
from src.config import settings
from src.metrics import cost_metrics
from shared.database.connections import initialize_all_databases, get_postgres_connection
from shared.utils.prometheus_metrics import FastAPIMetricsMiddleware

# Initialize FastAPI app
app = FastAPI(
    title="OptiInfra Cost Agent",
    description="AI-powered cost optimization agent",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics middleware
app.add_middleware(FastAPIMetricsMiddleware, metrics=cost_metrics)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(analyze.router, prefix="/api/v1", tags=["analysis"])
app.include_router(aws_costs.router, prefix="/api/v1/aws", tags=["aws-costs"])

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup."""
    logger = logging.getLogger(__name__)
    logger.info("Starting Cost Agent...")
    
    # Initialize all database connections
    try:
        initialize_all_databases()
        logger.info("All database connections initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger = logging.getLogger(__name__)
    logger.info("Shutting down Cost Agent...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
