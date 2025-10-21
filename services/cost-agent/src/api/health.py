"""
Health check endpoint for Cost Agent.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import logging

from shared.utils.database import (
    get_postgres_connection,
    get_clickhouse_connection,
    get_qdrant_client,
    get_redis_connection
)

router = APIRouter()
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str
    database: dict
    

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    
    database_status = {
        "postgres": "unknown",
        "clickhouse": "unknown",
        "qdrant": "unknown",
        "redis": "unknown"
    }
    
    # Check PostgreSQL
    try:
        conn = get_postgres_connection()
        conn.close()
        database_status["postgres"] = "healthy"
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        database_status["postgres"] = "unhealthy"
    
    # Check ClickHouse
    try:
        client = get_clickhouse_connection()
        client.command("SELECT 1")
        database_status["clickhouse"] = "healthy"
    except Exception as e:
        logger.error(f"ClickHouse health check failed: {e}")
        database_status["clickhouse"] = "unhealthy"
    
    # Check Qdrant
    try:
        client = get_qdrant_client()
        client.get_collections()
        database_status["qdrant"] = "healthy"
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        database_status["qdrant"] = "unhealthy"
    
    # Check Redis
    try:
        redis = get_redis_connection()
        redis.ping()
        database_status["redis"] = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        database_status["redis"] = "unhealthy"
    
    # Overall status
    all_healthy = all(status == "healthy" for status in database_status.values())
    overall_status = "healthy" if all_healthy else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version="1.0.0",
        database=database_status
    )


@router.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe."""
    try:
        conn = get_postgres_connection()
        conn.close()
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe."""
    return {"status": "alive"}
