"""
Data Collector Service - FastAPI Application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from datetime import datetime
import uuid

import psycopg2
from psycopg2.extras import RealDictCursor

from .config import config
from .collectors import AWSCostCollector, GCPCostCollector, AzureCostCollector
from .collectors.generic_collector import GenericCollector
from .storage import ClickHouseWriter, PostgresWriter, RedisPublisher
from .tasks import collect_data_task, health_check_task
from .api import credentials_router
from .api import dashboard
from .credential_manager import CredentialManager
from .provider_config import (
    build_generic_collector_config,
    get_provider_metadata,
    get_supported_providers,
    is_generic_provider,
    provider_enabled,
    provider_requirements,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="OptiInfra Data Collector Service",
    description="Unified data collection service for all cloud providers",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(credentials_router)
app.include_router(dashboard.router)


# Helper constants / utilities
DEFAULT_CUSTOMER_ID = getattr(
    config,
    "DEFAULT_CUSTOMER_ID",
    "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",  # matches credentials API default
)


def _get_postgres_connection():
    """Create a new PostgreSQL connection using service configuration."""
    return psycopg2.connect(
        host=config.POSTGRES_HOST,
        port=config.POSTGRES_PORT,
        database=config.POSTGRES_DB,
        user=config.POSTGRES_USER,
        password=config.POSTGRES_PASSWORD,
    )


def get_last_collection(
    provider: str,
    customer_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Fetch the most recent collection history entry for a provider."""
    conn = None
    try:
        conn = _get_postgres_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if customer_id:
                cur.execute(
                    """
                    SELECT
                        status,
                        started_at,
                        completed_at,
                        metrics_collected,
                        error_message
                    FROM collection_history
                    WHERE provider = %s
                      AND customer_id = %s
                    ORDER BY completed_at DESC NULLS LAST,
                             started_at DESC
                    LIMIT 1
                    """,
                    (provider, customer_id),
                )
            else:
                cur.execute(
                    """
                    SELECT
                        status,
                        customer_id,
                        started_at,
                        completed_at,
                        metrics_collected,
                        error_message
                    FROM collection_history
                    WHERE provider = %s
                    ORDER BY completed_at DESC NULLS LAST,
                             started_at DESC
                    LIMIT 1
                    """,
                    (provider,),
                )
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as exc:
        logger.error(
            f"Failed to fetch last collection for provider {provider}: {exc}",
            exc_info=True,
        )
        return None
    finally:
        if conn:
            conn.close()


def summarize_credentials(customer_id: Optional[str]) -> Dict[str, Dict[str, int]]:
    """Return credential counts grouped by provider for the customer."""
    if not customer_id:
        return {}

    summary: Dict[str, Dict[str, int]] = {}
    try:
        manager = CredentialManager()
        credentials = manager.list_credentials(customer_id)
    except Exception as exc:
        logger.error(f"Failed to list credentials for status summary: {exc}", exc_info=True)
        return summary

    for cred in credentials:
        provider = cred.get("provider")
        if not provider:
            continue
        provider_summary = summary.setdefault(
            provider,
            {"total": 0, "active": 0, "verified": 0},
        )
        provider_summary["total"] += 1
        if cred.get("is_active"):
            provider_summary["active"] += 1
        if cred.get("is_verified"):
            provider_summary["verified"] += 1

    return summary


# Request/Response Models
class CollectionRequest(BaseModel):
    customer_id: str
    provider: str  # vultr, aws, gcp, azure
    data_types: Optional[list[str]] = ["cost"]  # cost, performance, resource, application
    async_mode: Optional[bool] = True  # Use Celery for async execution


class CollectionResponse(BaseModel):
    task_id: str
    status: str
    message: str
    started_at: datetime
    async_mode: Optional[bool] = False


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime
    dependencies: Dict[str, str]


# Health Check Endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="data-collector",
        version="0.1.0",
        timestamp=datetime.now(),
        dependencies={
            "clickhouse": "connected",
            "postgres": "connected",
            "redis": "connected"
        }
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "OptiInfra Data Collector",
        "version": "0.1.0",
        "status": "running",
        "port": config.SERVICE_PORT,
        "endpoints": {
            "health": "/health",
            "collect": "/api/v1/collect/trigger",
            "status": "/api/v1/collect/status/{task_id}",
            "history": "/api/v1/collect/history"
        }
    }


# Collection Endpoints
@app.post("/api/v1/collect/trigger", response_model=CollectionResponse)
async def trigger_collection(request: CollectionRequest):
    """
    Manually trigger data collection for a customer
    
    This is the UNIFIED COLLECTION ENDPOINT that:
    1. Instantiates the appropriate cloud collector
    2. Collects data from the cloud provider
    3. Writes to ClickHouse (metrics)
    4. Writes to PostgreSQL (history)
    5. Publishes to Redis (real-time events)
    
    Args:
        request: Collection request with customer_id, provider, and data_types
    
    Returns:
        CollectionResponse with task_id and status
    """
    task_id = str(uuid.uuid4())
    started_at = datetime.now()
    
    logger.info(f"[{task_id}] Collection triggered for customer: {request.customer_id}, provider: {request.provider}, data_types: {request.data_types}, async_mode: {request.async_mode}")
    
    # If async mode, use Celery task
    if request.async_mode:
        try:
            celery_task = collect_data_task.delay(
                customer_id=request.customer_id,
                provider=request.provider,
                data_types=request.data_types
            )
            
            logger.info(f"[{celery_task.id}] Async collection task queued")
            
            return CollectionResponse(
                task_id=celery_task.id,
                status="queued",
                message=f"Collection task queued for {request.provider}",
                started_at=started_at,
                async_mode=True
            )
        except Exception as e:
            logger.error(f"Failed to queue async task: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}")
    
    # Synchronous mode (original implementation)
    try:
        # Initialize storage writers
        clickhouse_writer = ClickHouseWriter()
        postgres_writer = PostgresWriter()
        redis_publisher = RedisPublisher()
        credential_manager = CredentialManager()
        
        # Process each data type
        for data_type in request.data_types:
            if data_type == "cost":
                # Check if provider should use Generic Collector
                if is_generic_provider(request.provider):
                    logger.info(f"[{task_id}] Using Generic Collector for {request.provider}")
                    
                    # Load customer-specific credentials (if available)
                    credentials = None
                    try:
                        credentials = credential_manager.get_credential(
                            request.customer_id,
                            request.provider,
                        )
                    except Exception as cred_error:
                        logger.warning(
                            f"[{task_id}] Failed to retrieve credentials for {request.provider}: {cred_error}"
                        )
                    
                    # Build Generic Collector configuration
                    try:
                        generic_config = build_generic_collector_config(
                            provider=request.provider,
                            customer_id=request.customer_id,
                            credentials=credentials,
                        )
                    except ValueError as config_error:
                        raise HTTPException(
                            status_code=400,
                            detail=str(config_error)
                        )
                    
                    # Create Generic Collector
                    collector = GenericCollector(generic_config)
                    
                    # Collect all metrics (performance, resource, application, GPU)
                    logger.info(f"[{task_id}] Collecting all metrics from {request.provider}")
                    result = collector.collect()
                    
                    # Write to ClickHouse (handled by collector)
                    if result.success:
                        logger.info(f"[{task_id}] Successfully collected {result.records_collected} metrics")
                    
                    # Write to PostgreSQL (collection history)
                    postgres_writer.write_collection_history(
                        customer_id=request.customer_id,
                        provider=request.provider,
                        task_id=task_id,
                        status="success" if result.success else "failed",
                        started_at=started_at,
                        completed_at=datetime.now(),
                        metrics_collected=result.records_collected,
                        error_message=result.error_message
                    )
                    
                    # Publish to Redis
                    if result.success:
                        redis_publisher.publish_data_updated(
                            customer_id=request.customer_id,
                            provider=request.provider,
                            data_type="all",
                            records_count=result.records_collected
                        )
                    
                    redis_publisher.publish_collection_status(
                        task_id=task_id,
                        status="completed" if result.success else "failed",
                        message=result.error_message
                    )
                    
                    # Skip to next data type
                    continue
                
                # Dedicated collectors for Big 3 only
                collector = None
                
                if request.provider == "aws":
                    if not config.AWS_ACCESS_KEY_ID or not config.AWS_SECRET_ACCESS_KEY:
                        raise HTTPException(status_code=400, detail="AWS credentials not configured")
                    collector = AWSCostCollector(
                        access_key_id=config.AWS_ACCESS_KEY_ID,
                        secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                        customer_id=request.customer_id
                    )
                
                elif request.provider == "gcp":
                    if not config.GCP_SERVICE_ACCOUNT_JSON:
                        raise HTTPException(status_code=400, detail="GCP credentials not configured")
                    collector = GCPCostCollector(
                        service_account_json=config.GCP_SERVICE_ACCOUNT_JSON,
                        customer_id=request.customer_id
                    )
                
                elif request.provider == "azure":
                    if not config.AZURE_SUBSCRIPTION_ID:
                        raise HTTPException(status_code=400, detail="Azure credentials not configured")
                    collector = AzureCostCollector(
                        subscription_id=config.AZURE_SUBSCRIPTION_ID,
                        tenant_id=config.AZURE_TENANT_ID,
                        client_id=config.AZURE_CLIENT_ID,
                        client_secret=config.AZURE_CLIENT_SECRET,
                        customer_id=request.customer_id
                    )
                
                else:
                    raise HTTPException(status_code=400, detail=f"Unsupported provider: {request.provider}")
                
                # Collect data from cloud provider
                logger.info(f"[{task_id}] Collecting {data_type} data from {request.provider}")
                result = collector.collect()
                
                # Write to ClickHouse
                if result.success and hasattr(collector, 'get_collected_metrics'):
                    metrics = collector.get_collected_metrics()
                    if metrics:
                        records_written = clickhouse_writer.write_cost_metrics(metrics)
                        logger.info(f"[{task_id}] Wrote {records_written} cost metrics to ClickHouse")
                
                # Write to PostgreSQL (collection history)
                postgres_writer.write_collection_history(
                    customer_id=request.customer_id,
                    provider=request.provider,
                    task_id=task_id,
                    status="success" if result.success else "failed",
                    started_at=started_at,
                    completed_at=datetime.now(),
                    metrics_collected=result.records_collected,
                    error_message=result.error_message
                )
                
                # Publish to Redis
                if result.success:
                    redis_publisher.publish_data_updated(
                        customer_id=request.customer_id,
                        provider=request.provider,
                        data_type=data_type,
                        records_count=result.records_collected
                    )
                
                redis_publisher.publish_collection_status(
                    task_id=task_id,
                    status="completed" if result.success else "failed",
                    message=result.error_message
                )
            
            elif data_type in ["performance", "resource", "application"]:
                # Use Generic Collector for these data types if provider is generic
                if is_generic_provider(request.provider):
                    logger.info(f"[{task_id}] Using Generic Collector for {request.provider} {data_type}")
                    
                    # Load customer-specific credentials
                    credentials = None
                    try:
                        credentials = credential_manager.get_credential(
                            request.customer_id,
                            request.provider,
                        )
                    except Exception as cred_error:
                        logger.warning(
                            f"[{task_id}] Failed to retrieve credentials for {request.provider}: {cred_error}"
                        )
                    
                    # Build Generic Collector configuration
                    try:
                        generic_config = build_generic_collector_config(
                            provider=request.provider,
                            customer_id=request.customer_id,
                            credentials=credentials,
                        )
                    except ValueError as config_error:
                        raise HTTPException(
                            status_code=400,
                            detail=str(config_error)
                        )
                    
                    # Create Generic Collector
                    collector = GenericCollector(generic_config)
                    
                    # Collect all metrics
                    logger.info(f"[{task_id}] Collecting all metrics from {request.provider}")
                    result = collector.collect()
                    
                    # Write to ClickHouse (handled by collector)
                    if result.success:
                        logger.info(f"[{task_id}] Successfully collected {result.records_collected} metrics")
                    
                    # Write to PostgreSQL (collection history)
                    postgres_writer.write_collection_history(
                        customer_id=request.customer_id,
                        provider=request.provider,
                        task_id=task_id,
                        status="success" if result.success else "failed",
                        started_at=started_at,
                        completed_at=datetime.now(),
                        metrics_collected=result.records_collected,
                        error_message=result.error_message
                    )
                    
                    # Publish to Redis
                    if result.success:
                        redis_publisher.publish_data_updated(
                            customer_id=request.customer_id,
                            provider=request.provider,
                            data_type=data_type,
                            records_count=result.records_collected
                        )
                    
                    redis_publisher.publish_collection_status(
                        task_id=task_id,
                        status="completed" if result.success else "failed",
                        message=result.error_message
                    )
                else:
                    logger.warning(f"[{task_id}] Data type '{data_type}' not yet implemented for {request.provider}")
            
            else:
                # Unknown data type
                logger.warning(f"[{task_id}] Unknown data type '{data_type}'")
        
        # Close connections
        clickhouse_writer.close()
        postgres_writer.close()
        redis_publisher.close()
        
        return CollectionResponse(
            task_id=task_id,
            status="completed",
            message=f"Collection completed for {request.provider}",
            started_at=started_at
        )
    
    except Exception as e:
        logger.error(f"[{task_id}] Collection failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Collection failed: {str(e)}")


@app.get("/api/v1/collect/status/{task_id}")
async def get_collection_status(task_id: str):
    """
    Get status of a collection task
    
    Args:
        task_id: Task ID returned from trigger_collection
    
    Returns:
        Task status and details
    """
    logger.info(f"Status check for task: {task_id}")
    
    # TODO: Implement actual status check
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "Task status check not yet implemented"
    }


@app.get("/api/v1/collect/history")
async def get_collection_history(
    customer_id: str,
    limit: int = 100
):
    """
    Get collection history for a customer
    
    Args:
        customer_id: Customer ID
        limit: Maximum number of records to return
    
    Returns:
        List of collection history records
    """
    logger.info(f"History requested for customer: {customer_id}, limit: {limit}")
    
    # TODO: Implement actual history retrieval
    return {
        "customer_id": customer_id,
        "collections": [],
        "message": "Collection history not yet implemented"
    }


@app.get("/api/v1/collectors/status")
async def get_collectors_status(customer_id: Optional[str] = None):
    """Get status of all supported collectors."""
    active_customer_id = customer_id or DEFAULT_CUSTOMER_ID

    credential_stats = summarize_credentials(active_customer_id)

    providers_response = []
    now_iso = datetime.now().isoformat()

    for slug, meta in get_supported_providers().items():
        slug_normalized = slug.lower()
        enabled = provider_enabled(slug_normalized)
        provider_type = meta.get("type", "generic")

        stats = credential_stats.get(slug_normalized, {"total": 0, "active": 0, "verified": 0})

        # Determine configuration sources
        env_configured = False
        if provider_type == "generic":
            config_keys = meta.get("config_keys", {})
            prometheus_attr = config_keys.get("prometheus_url")
            env_prometheus = getattr(config, prometheus_attr, None) if prometheus_attr else None
            env_configured = bool(env_prometheus)
        else:
            env_keys = meta.get("env_keys", [])
            if env_keys:
                env_configured = all(getattr(config, key, None) for key in env_keys)

        configured = stats.get("active", 0) > 0 or (enabled and env_configured)

        last_collection = get_last_collection(slug_normalized, active_customer_id)
        last_status = None
        last_sync = None
        if last_collection:
            last_status = last_collection.get("status")
            completed_at = last_collection.get("completed_at") or last_collection.get("started_at")
            if completed_at:
                last_sync = completed_at.isoformat()

        status = "not_configured"
        if configured:
            if last_status and last_status.lower() in {"success", "completed"}:
                status = "connected"
            elif last_status and last_status.lower() == "failed":
                status = "error"
            else:
                status = "configured"

        providers_response.append(
            {
                "provider": slug_normalized,
                "display_name": meta.get("display_name", slug_normalized.title()),
                "type": provider_type,
                "category": meta.get("category", "Other"),
                "enabled": enabled,
                "configured": configured,
                "status": status,
                "last_status": last_status,
                "last_sync": last_sync,
                "credential_count": stats.get("active", 0),
                "requirements": provider_requirements(slug_normalized),
            }
        )

    summary = {
        "total_supported": len(providers_response),
        "configured": sum(1 for provider in providers_response if provider["configured"]),
        "connected": sum(1 for provider in providers_response if provider["status"] == "connected"),
        "generic_supported": sum(1 for provider in providers_response if provider["type"] == "generic"),
        "dedicated_supported": sum(1 for provider in providers_response if provider["type"] == "dedicated"),
    }

    return {
        "customer_id": active_customer_id,
        "generated_at": now_iso,
        "providers": providers_response,
        "summary": summary,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.SERVICE_PORT,
        reload=True
    )
