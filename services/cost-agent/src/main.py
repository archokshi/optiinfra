"""
OptiInfra Cost Agent - Main Application

This is the Cost Agent that optimizes cloud spending through:
- Spot instance migrations
- Reserved instance recommendations
- Instance right-sizing
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
import logging
from starlette.middleware.base import BaseHTTPMiddleware

from src.api import health, analyze
from src.api import aws_costs, gcp_costs, azure_costs
from src.api import (
    recommendation_routes,
    execution_routes,
    learning_routes,
    auth_routes,
    dashboard_routes,
)
from src.api import bulk_routes, webhook_routes, notification_routes
from src.api import cost_routes_v2  # Phase 6.3: New routes using ClickHouse readers
from src.config import settings
from src.metrics import cost_metrics
from shared.database.connections import initialize_all_databases, get_postgres_connection
from shared.utils.prometheus_metrics import FastAPIMetricsMiddleware

# Initialize FastAPI app
app = FastAPI(
    title="OptiInfra Cost Agent API",
    description="""
    # OptiInfra Cost Agent API
    
    The Cost Agent API provides comprehensive cost optimization capabilities for cloud infrastructure.
    
    ## Features
    - **Cost Collection**: Collect costs from AWS, GCP, and Azure
    - **Analysis**: Detect anomalies, trends, and forecasts
    - **Recommendations**: Generate intelligent cost-saving recommendations
    - **Execution**: Execute optimizations with approval workflows
    - **Learning**: Continuous learning from execution outcomes
    
    ## Authentication
    All protected endpoints require authentication via:
    - **API Key**: Include `X-API-Key` header
    - **JWT Token**: Include `Authorization: Bearer <token>` header
    
    ## Getting Started
    1. Create an API key: `POST /api/v1/auth/api-key/create`
    2. Use the key in `X-API-Key` header for all requests
    3. Explore endpoints in the interactive documentation below
    
    ## Support
    - Documentation: https://docs.optiinfra.com
    - Support: support@optiinfra.com
    """,
    version="1.0.0",
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

# Add Prometheus metrics middleware
app.add_middleware(FastAPIMetricsMiddleware, metrics=cost_metrics)


# Rate limiting middleware
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to apply rate limiting to all requests."""
    
    async def dispatch(self, request: Request, call_next):
        from src.middleware.rate_limit import rate_limiter
        from src.auth.api_key import APIKeyManager
        from src.auth.jwt_handler import JWTHandler
        
        # Skip rate limiting for health and auth endpoints
        if request.url.path in ["/api/v1/health", "/api/v1/health/detailed", "/metrics"] or \
           request.url.path.startswith("/api/v1/auth/"):
            response = await call_next(request)
            return response
        
        # Extract customer ID from authentication
        customer_id = "anonymous"
        
        # Try API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            key_record = await APIKeyManager.validate_key(api_key)
            if key_record:
                customer_id = key_record.customer_id
        
        # Try JWT token
        if customer_id == "anonymous":
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                payload = JWTHandler.decode_token(token)
                if payload:
                    customer_id = payload.get("customer_id", "anonymous")
        
        # Check rate limit
        endpoint = request.url.path
        try:
            await rate_limiter.check_rate_limit(customer_id, endpoint)
        except Exception as e:
            # If rate limit check fails, let it through (fail open)
            logger.warning(f"Rate limit check failed: {e}")
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        try:
            headers = rate_limiter.get_rate_limit_headers(customer_id, endpoint)
            for key, value in headers.items():
                response.headers[key] = value
        except:
            pass
        
        return response


# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(auth_routes.router, tags=["authentication"])
app.include_router(analyze.router, prefix="/api/v1", tags=["analysis"])

# Phase 6.3: New V2 routes using ClickHouse readers (replaces direct cloud API calls)
app.include_router(cost_routes_v2.router, tags=["costs-v2-clickhouse"])

# Legacy routes (will be deprecated in favor of V2)
app.include_router(aws_costs.router, prefix="/api/v1/aws", tags=["aws-costs-legacy"])
app.include_router(gcp_costs.router, prefix="/api/v1", tags=["gcp-costs-legacy"])
app.include_router(azure_costs.router, tags=["azure-costs-legacy"])

app.include_router(recommendation_routes.router, tags=["recommendations"])
app.include_router(dashboard_routes.router, tags=["dashboard"])
app.include_router(execution_routes.router, tags=["execution"])
app.include_router(learning_routes.router, tags=["learning"])
app.include_router(bulk_routes.router, tags=["bulk-operations"])
app.include_router(webhook_routes.router, tags=["webhooks"])
app.include_router(notification_routes.router, tags=["notifications"])

# Metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# Custom OpenAPI schema with security schemes
def custom_openapi():
    """Custom OpenAPI schema with security definitions."""
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "APIKey": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for authentication. Create one at POST /api/v1/auth/api-key/create"
        },
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token for authentication. Get one at POST /api/v1/auth/token"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


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
