# PHASE2-2.1 PART1: Performance Agent Skeleton - Code Implementation Plan

**Phase**: PHASE2-2.1  
**Agent**: Performance Agent  
**Objective**: Create FastAPI application skeleton and orchestrator registration  
**Estimated Time**: 15+10m (25 minutes total)  
**Priority**: HIGH  
**Dependencies**: PHASE1 (0.5, 0.6, 0.10)

---

## Overview

This phase establishes the foundational structure for the Performance Agent, which will optimize latency and throughput for LLM infrastructure (vLLM, TGI, SGLang). The skeleton includes the FastAPI application, basic endpoints, health checks, and orchestrator registration.

---

## Agent Purpose

### Performance Agent Mission
**Improve latency and throughput for LLM infrastructure**

### Key Responsibilities
1. **Metrics Collection**: Collect performance metrics from vLLM/TGI/SGLang
2. **Bottleneck Identification**: Identify performance bottlenecks
3. **Optimization Generation**: Generate optimizations (KV cache, quantization, batching)
4. **Testing & Rollout**: Test in staging, gradual rollout to production
5. **SLO Monitoring**: Monitor for SLO violations and auto-rollback

### Key Optimizations
- **KV Cache Tuning**: Optimize key-value cache configuration
- **Quantization**: FP16 → FP8 → INT8 optimization
- **Batch Size Optimization**: Optimize batch processing
- **Model Parallelism**: Distribute model across GPUs

### Expected Impact
- **3x Performance Improvement**: Reduce latency, increase throughput
- **Better Resource Utilization**: Maximize GPU efficiency
- **SLO Compliance**: Maintain quality while optimizing

---

## Project Structure

```
optiinfra/services/performance-agent/
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── api/
│   │   ├── __init__.py
│   │   ├── health.py           # Health check endpoints
│   │   └── metrics.py          # Metrics endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── logger.py           # Logging configuration
│   │   └── registration.py     # Orchestrator registration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── health.py           # Health check models
│   │   └── metrics.py          # Metrics models
│   └── middleware/
│       ├── __init__.py
│       └── logging.py          # Request logging middleware
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_health.py
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## Implementation Plan

### Step 1: Project Setup (5 minutes)

#### 1.1 Create Directory Structure

```bash
mkdir -p optiinfra/services/performance-agent/{src/{api,core,models,middleware},tests}
cd optiinfra/services/performance-agent
```

#### 1.2 Create requirements.txt

```txt
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# HTTP Client
httpx==0.25.2
aiohttp==3.9.1

# Database
sqlalchemy==2.0.23
asyncpg==0.29.0
psycopg2-binary==2.9.9

# Monitoring
prometheus-client==0.19.0

# Utilities
python-dotenv==1.0.0
python-multipart==0.0.6

# Development
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
black==23.12.0
flake8==6.1.0
mypy==1.7.1
```

#### 1.3 Create .env.example

```bash
# Application
PORT=8002
ENVIRONMENT=development
LOG_LEVEL=INFO
AGENT_ID=performance-agent-001
AGENT_TYPE=performance

# Orchestrator
ORCHESTRATOR_URL=http://localhost:8080
ORCHESTRATOR_REGISTER_ENDPOINT=/api/v1/agents/register
ORCHESTRATOR_HEARTBEAT_INTERVAL=30

# Database
DATABASE_URL=postgresql://perf_user:perf_password@localhost:5432/performance_agent

# Redis
REDIS_URL=redis://localhost:6379/1

# Prometheus
PROMETHEUS_PORT=9092
```

---

### Step 2: Core Configuration (3 minutes)

#### 2.1 Create src/config.py

```python
"""
Performance Agent Configuration

Manages all configuration settings using Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    port: int = Field(default=8002, env="PORT")
    environment: str = Field(default="development", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    agent_id: str = Field(default="performance-agent-001", env="AGENT_ID")
    agent_type: str = Field(default="performance", env="AGENT_TYPE")
    
    # Orchestrator
    orchestrator_url: str = Field(
        default="http://localhost:8080",
        env="ORCHESTRATOR_URL"
    )
    orchestrator_register_endpoint: str = Field(
        default="/api/v1/agents/register",
        env="ORCHESTRATOR_REGISTER_ENDPOINT"
    )
    orchestrator_heartbeat_interval: int = Field(
        default=30,
        env="ORCHESTRATOR_HEARTBEAT_INTERVAL"
    )
    
    # Database
    database_url: str = Field(
        default="postgresql://perf_user:perf_password@localhost:5432/performance_agent",
        env="DATABASE_URL"
    )
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/1",
        env="REDIS_URL"
    )
    
    # Prometheus
    prometheus_port: int = Field(default=9092, env="PROMETHEUS_PORT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
```

---

### Step 3: Logging Setup (2 minutes)

#### 3.1 Create src/core/logger.py

```python
"""
Logging Configuration

Structured JSON logging for the Performance Agent.
"""

import logging
import sys
from typing import Any, Dict
import json
from datetime import datetime

from src.config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "agent_id": settings.agent_id,
            "agent_type": settings.agent_type,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        return json.dumps(log_data)


def setup_logging() -> None:
    """Configure application logging."""
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    root_logger.addHandler(handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)
```

---

### Step 4: Health Check Models (2 minutes)

#### 4.1 Create src/models/health.py

```python
"""
Health Check Models

Pydantic models for health check responses.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class HealthResponse(BaseModel):
    """Basic health check response."""
    
    status: str = Field(..., description="Health status (healthy/unhealthy)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="0.1.0")
    agent_id: str
    agent_type: str
    uptime_seconds: float = Field(..., description="Uptime in seconds")


class DetailedHealthResponse(BaseModel):
    """Detailed health check response with component status."""
    
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="0.1.0")
    agent_id: str
    agent_type: str
    uptime_seconds: float
    components: dict = Field(
        default_factory=dict,
        description="Status of individual components"
    )


class ServiceInfo(BaseModel):
    """Service information response."""
    
    service: str = Field(default="OptiInfra Performance Agent")
    version: str = Field(default="0.1.0")
    status: str = Field(default="running")
    capabilities: list[str] = Field(
        default_factory=lambda: [
            "performance_monitoring",
            "bottleneck_detection",
            "kv_cache_optimization",
            "quantization_optimization",
            "batch_size_tuning"
        ]
    )
```

---

### Step 5: Health Check Endpoints (3 minutes)

#### 5.1 Create src/api/health.py

```python
"""
Health Check Endpoints

Provides health check and service information endpoints.
"""

from fastapi import APIRouter, status
from datetime import datetime
import time

from src.models.health import (
    HealthResponse,
    DetailedHealthResponse,
    ServiceInfo
)
from src.config import settings

router = APIRouter()

# Track startup time
_startup_time = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["health"]
)
async def health_check() -> HealthResponse:
    """
    Basic health check endpoint.
    
    Returns:
        HealthResponse: Current health status
    """
    return HealthResponse(
        status="healthy",
        agent_id=settings.agent_id,
        agent_type=settings.agent_type,
        uptime_seconds=time.time() - _startup_time
    )


@router.get(
    "/health/detailed",
    response_model=DetailedHealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["health"]
)
async def detailed_health_check() -> DetailedHealthResponse:
    """
    Detailed health check with component status.
    
    Returns:
        DetailedHealthResponse: Detailed health status
    """
    # TODO: Add actual component health checks
    components = {
        "database": {"status": "healthy", "latency_ms": 5.2},
        "cache": {"status": "healthy", "latency_ms": 1.1},
        "orchestrator": {"status": "healthy", "latency_ms": 10.5}
    }
    
    return DetailedHealthResponse(
        status="healthy",
        agent_id=settings.agent_id,
        agent_type=settings.agent_type,
        uptime_seconds=time.time() - _startup_time,
        components=components
    )


@router.get(
    "/",
    response_model=ServiceInfo,
    status_code=status.HTTP_200_OK,
    tags=["info"]
)
async def service_info() -> ServiceInfo:
    """
    Service information endpoint.
    
    Returns:
        ServiceInfo: Service details and capabilities
    """
    return ServiceInfo()
```

---

### Step 6: Orchestrator Registration (5 minutes)

#### 6.1 Create src/core/registration.py

```python
"""
Orchestrator Registration

Handles registration and heartbeat with the orchestrator.
"""

import asyncio
import logging
from typing import Optional
import httpx
from datetime import datetime

from src.config import settings

logger = logging.getLogger(__name__)


class OrchestratorClient:
    """Client for orchestrator communication."""
    
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self.registered = False
        self.heartbeat_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start orchestrator client."""
        self.client = httpx.AsyncClient(timeout=10.0)
        await self.register()
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    async def stop(self):
        """Stop orchestrator client."""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if self.client:
            await self.client.aclose()
    
    async def register(self) -> bool:
        """
        Register agent with orchestrator.
        
        Returns:
            bool: True if registration successful
        """
        if not self.client:
            logger.error("HTTP client not initialized")
            return False
        
        registration_url = (
            f"{settings.orchestrator_url}"
            f"{settings.orchestrator_register_endpoint}"
        )
        
        payload = {
            "agent_id": settings.agent_id,
            "agent_type": settings.agent_type,
            "capabilities": [
                "performance_monitoring",
                "bottleneck_detection",
                "kv_cache_optimization",
                "quantization_optimization",
                "batch_size_tuning"
            ],
            "endpoint": f"http://localhost:{settings.port}",
            "health_check_endpoint": "/api/v1/health",
            "version": "0.1.0",
            "metadata": {
                "environment": settings.environment,
                "log_level": settings.log_level
            }
        }
        
        try:
            response = await self.client.post(
                registration_url,
                json=payload
            )
            
            if response.status_code == 200:
                self.registered = True
                logger.info(
                    f"Successfully registered with orchestrator",
                    extra={
                        "agent_id": settings.agent_id,
                        "orchestrator_url": settings.orchestrator_url
                    }
                )
                return True
            else:
                logger.error(
                    f"Failed to register with orchestrator: {response.status_code}",
                    extra={"response": response.text}
                )
                return False
        
        except Exception as e:
            logger.error(
                f"Error registering with orchestrator: {e}",
                exc_info=True
            )
            return False
    
    async def send_heartbeat(self) -> bool:
        """
        Send heartbeat to orchestrator.
        
        Returns:
            bool: True if heartbeat successful
        """
        if not self.client or not self.registered:
            return False
        
        heartbeat_url = f"{settings.orchestrator_url}/api/v1/agents/heartbeat"
        
        payload = {
            "agent_id": settings.agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy"
        }
        
        try:
            response = await self.client.post(
                heartbeat_url,
                json=payload
            )
            
            if response.status_code == 200:
                logger.debug(f"Heartbeat sent successfully")
                return True
            else:
                logger.warning(
                    f"Heartbeat failed: {response.status_code}",
                    extra={"response": response.text}
                )
                return False
        
        except Exception as e:
            logger.warning(f"Error sending heartbeat: {e}")
            return False
    
    async def _heartbeat_loop(self):
        """Background task for sending periodic heartbeats."""
        while True:
            try:
                await asyncio.sleep(settings.orchestrator_heartbeat_interval)
                await self.send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}", exc_info=True)


# Global orchestrator client instance
orchestrator_client = OrchestratorClient()
```

---

### Step 7: Main Application (5 minutes)

#### 7.1 Create src/main.py

```python
"""
Performance Agent - Main Application

FastAPI application for the Performance Agent.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
import logging

from src.api import health
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

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])

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
```

---

### Step 8: Docker Support (3 minutes)

#### 8.1 Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8002

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

#### 8.2 Create docker-compose.yml

```yaml
version: '3.8'

services:
  performance-agent:
    build: .
    ports:
      - "8002:8002"
      - "9092:9092"
    environment:
      - PORT=8002
      - ENVIRONMENT=development
      - LOG_LEVEL=INFO
      - ORCHESTRATOR_URL=http://orchestrator:8080
      - DATABASE_URL=postgresql://perf_user:perf_password@postgres:5432/performance_agent
      - REDIS_URL=redis://redis:6379/1
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=performance_agent
      - POSTGRES_USER=perf_user
      - POSTGRES_PASSWORD=perf_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5433:5432"
    restart: unless-stopped

  redis:
    image: redis:6
    ports:
      - "6380:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

---

### Step 9: Testing Setup (2 minutes)

#### 9.1 Create pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
    --cov=src
    --cov-report=html
    --cov-report=term-missing
markers =
    unit: Unit tests
    integration: Integration tests
    asyncio_mode = auto
```

#### 9.2 Create tests/conftest.py

```python
"""
Test Configuration

Shared fixtures for tests.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_orchestrator_url():
    """Mock orchestrator URL."""
    return "http://mock-orchestrator:8080"
```

#### 9.3 Create tests/test_health.py

```python
"""
Health Check Tests

Tests for health check endpoints.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_health_check(client: TestClient):
    """Test basic health check endpoint."""
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "agent_id" in data
    assert "uptime_seconds" in data


@pytest.mark.unit
def test_detailed_health_check(client: TestClient):
    """Test detailed health check endpoint."""
    response = client.get("/api/v1/health/detailed")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "components" in data
    assert isinstance(data["components"], dict)


@pytest.mark.unit
def test_service_info(client: TestClient):
    """Test service info endpoint."""
    response = client.get("/api/v1/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "OptiInfra Performance Agent"
    assert "capabilities" in data
    assert len(data["capabilities"]) > 0
```

---

### Step 10: README (2 minutes)

#### 10.1 Create README.md

```markdown
# OptiInfra Performance Agent

Python FastAPI-based agent for LLM performance optimization.

## Features

- Performance monitoring for vLLM/TGI/SGLang
- Bottleneck detection
- KV cache optimization
- Quantization optimization (FP16 → FP8 → INT8)
- Batch size tuning
- Orchestrator integration

## Quick Start

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run
python src/main.py

# Or with uvicorn
uvicorn src.main:app --reload --port 8002
```

### Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f performance-agent
```

## API Endpoints

- `GET /api/v1/health` - Health check
- `GET /api/v1/health/detailed` - Detailed health check
- `GET /api/v1/` - Service information
- `GET /metrics` - Prometheus metrics

## Configuration

See `.env.example` for configuration options.

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=src --cov-report=html
```

## Project Status

**PHASE2-2.1 Complete** ✅
- FastAPI skeleton implemented
- Health check endpoints
- Orchestrator registration
- Docker support

## Next Steps

- Implement metrics collection
- Add performance analysis
- Implement optimization recommendations
```

---

## Success Criteria

### Functional Requirements
- ✅ FastAPI application runs successfully
- ✅ Health check endpoints respond correctly
- ✅ Orchestrator registration works
- ✅ Logging is structured and JSON-formatted
- ✅ Configuration is managed via environment variables

### Non-Functional Requirements
- ✅ Code follows Python best practices
- ✅ Type hints throughout
- ✅ Comprehensive docstrings
- ✅ Tests pass with >80% coverage
- ✅ Docker containerization works

---

## Dependencies

### From PHASE1
- **0.5**: Shared database connections
- **0.6**: Shared utilities (Prometheus metrics)
- **0.10**: Orchestrator API contracts

---

## Next Phase

**PHASE2-2.2**: Metrics Collection - Implement performance metrics collection from vLLM/TGI/SGLang

---

**Status**: Ready for implementation  
**Estimated Completion**: 25 minutes  
**Dependencies**: PHASE1 (0.5, 0.6, 0.10)
