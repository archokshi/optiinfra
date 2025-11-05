"""
Performance Agent - Main Application

FastAPI application for the Performance Agent.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from prometheus_client import make_asgi_app
import logging

from src.api import health, metrics, analysis, optimization, workflows, config
from src.api import performance_routes_v2  # Phase 6.5
from src.api.error_handlers import (
    validation_exception_handler,
    general_exception_handler,
    http_exception_handler
)
from src.config import settings
from src.core.registration import orchestrator_client

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="OptiInfra Performance Agent API",
    description="""
    # OptiInfra Performance Agent API
    
    The Performance Agent optimizes latency and throughput for LLM infrastructure.
    
    ## Features
    - **Performance Monitoring**: Collect metrics from vLLM/TGI/SGLang
    - **Bottleneck Detection**: Identify performance bottlenecks
    - **KV Cache Optimization**: Optimize key-value cache configuration
    - **Quantization**: FP16 → FP8 → INT8 optimization
    - **Batch Size Tuning**: Optimize batch processing
    
    ## Capabilities
    - Performance monitoring
    - Bottleneck detection
    - KV cache optimization
    - Quantization optimization
    - Batch size tuning
    
    ## Support
    - Documentation: https://docs.optiinfra.com
    - Support: support@optiinfra.com
    """,
    version="0.1.0",
    contact={
        "name": "OptiInfra Support",
        "email": "support@optiinfra.com",
        "url": "https://optiinfra.com"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://optiinfra.com/license"
    }
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
from fastapi import HTTPException
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])
app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])
app.include_router(optimization.router, prefix="/api/v1", tags=["optimization"])
app.include_router(workflows.router, prefix="/api/v1", tags=["workflows"])
app.include_router(config.router, prefix="/api/v1", tags=["config"])

# V2 Routes (Phase 6.5 - ClickHouse Readers)
app.include_router(performance_routes_v2.router, tags=["performance-v2"])

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Performance Agent...")
    
    # Register with orchestrator
    try:
        await orchestrator_client.start()
        logger.info("Orchestrator registration initiated")
    except Exception as e:
        logger.error(f"Failed to start orchestrator client: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Performance Agent...")
    
    # Stop orchestrator client
    try:
        await orchestrator_client.stop()
        logger.info("Orchestrator client stopped")
    except Exception as e:
        logger.error(f"Error stopping orchestrator client: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )
