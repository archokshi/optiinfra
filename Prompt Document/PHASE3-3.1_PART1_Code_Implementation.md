# PHASE3-3.1 PART1: Resource Agent Skeleton - Code Implementation Plan

**Phase**: PHASE3-3.1  
**Agent**: Resource Agent  
**Objective**: Create FastAPI application skeleton and orchestrator registration  
**Estimated Time**: 15+10m (25 minutes total)  
**Priority**: HIGH  
**Dependencies**: PHASE1 (0.5, 0.6, 0.10), PHASE2 (2.1)

---

## Overview

This phase establishes the foundational structure for the Resource Agent, which will maximize GPU/CPU/memory utilization for LLM infrastructure. The skeleton includes the FastAPI application, basic endpoints, health checks, and orchestrator registration.

---

## Agent Purpose

### Resource Agent Mission
**Maximize GPU/CPU/memory utilization and optimize resource allocation**

### Key Responsibilities
1. **GPU Metrics Collection**: Collect GPU metrics using nvidia-smi
2. **CPU/Memory Metrics**: Collect CPU/memory metrics using psutil
3. **Utilization Analysis**: Identify underutilized resources
4. **Scaling Recommendations**: Recommend auto-scaling or consolidation
5. **KVOptkit Integration**: Integrate with KVOptkit for KV cache optimization

### Key Workflows
- **Auto-Scaling**: Predictive scaling based on utilization patterns
- **Resource Consolidation**: Consolidate workloads to reduce waste
- **KV Cache Optimization**: Optimize KV cache for memory efficiency

### Expected Impact
- **50% Better Utilization**: Reduce idle GPU/CPU time
- **30% Cost Savings**: Through consolidation and right-sizing
- **Improved Performance**: Better resource allocation

---

## Project Structure

```
optiinfra/services/resource-agent/
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── api/
│   │   ├── __init__.py
│   │   ├── health.py           # Health check endpoints
│   │   ├── metrics.py          # Metrics endpoints
│   │   └── config.py           # Configuration endpoints
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
mkdir -p optiinfra/services/resource-agent/{src/{api,core,models,middleware},tests}
cd optiinfra/services/resource-agent
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
requests==2.31.0

# Database
sqlalchemy==2.0.23
asyncpg==0.29.0
psycopg2-binary==2.9.9

# Redis
redis==5.0.1

# Monitoring
prometheus-client==0.19.0

# Resource Monitoring
nvidia-ml-py==12.535.133  # nvidia-smi Python bindings
psutil==5.9.6              # CPU/Memory metrics
GPUtil==1.4.0              # GPU utilities

# Utilities
python-dotenv==1.0.0
python-multipart==0.0.6

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2
```

#### 1.3 Create .env.example

```bash
# Application
PORT=8003
ENVIRONMENT=development
LOG_LEVEL=INFO
AGENT_ID=resource-agent-001
AGENT_TYPE=resource

# Orchestrator
ORCHESTRATOR_URL=http://localhost:8080
ORCHESTRATOR_REGISTER_ENDPOINT=/api/v1/agents/register
ORCHESTRATOR_HEARTBEAT_INTERVAL=30

# Database
DATABASE_URL=postgresql://resource_user:resource_password@localhost:5432/resource_agent

# Redis
REDIS_URL=redis://localhost:6379/2

# Prometheus
PROMETHEUS_PORT=9093
```

---

### Step 2: Core Configuration (5 minutes)

#### 2.1 Create src/config.py

```python
"""
Resource Agent Configuration

Manages all configuration settings using Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    port: int = Field(default=8003, env="PORT")
    environment: str = Field(default="development", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    agent_id: str = Field(default="resource-agent-001", env="AGENT_ID")
    agent_type: str = Field(default="resource", env="AGENT_TYPE")
    
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
        default="postgresql://resource_user:resource_password@localhost:5432/resource_agent",
        env="DATABASE_URL"
    )
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/2",
        env="REDIS_URL"
    )
    
    # Prometheus
    prometheus_port: int = Field(default=9093, env="PROMETHEUS_PORT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
```

---

### Step 3: Logging Setup (3 minutes)

#### 3.1 Create src/core/logger.py

```python
"""
Logging Configuration

Centralized logging setup for the Resource Agent.
"""

import logging
import sys
from src.config import settings


def setup_logging():
    """Configure logging for the application."""
    
    # Create logger
    logger = logging.getLogger("resource_agent")
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger


# Global logger instance
logger = setup_logging()
```

---

### Step 4: Pydantic Models (5 minutes)

#### 4.1 Create src/models/health.py

```python
"""
Health Check Models

Pydantic models for health check endpoints.
"""

from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime


class HealthStatus(BaseModel):
    """Health status response."""
    
    status: str = Field(..., description="Health status (healthy/unhealthy)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_id: str = Field(..., description="Agent identifier")
    agent_type: str = Field(..., description="Agent type")
    version: str = Field(default="1.0.0", description="Agent version")
    uptime_seconds: float = Field(..., description="Uptime in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-10-24T12:00:00Z",
                "agent_id": "resource-agent-001",
                "agent_type": "resource",
                "version": "1.0.0",
                "uptime_seconds": 3600.0
            }
        }


class DetailedHealthStatus(HealthStatus):
    """Detailed health status with component checks."""
    
    components: Dict[str, str] = Field(
        default_factory=dict,
        description="Component health status"
    )
    metrics: Optional[Dict[str, float]] = Field(
        default=None,
        description="Health metrics"
    )
```

#### 4.2 Create src/models/metrics.py

```python
"""
Metrics Models

Pydantic models for metrics endpoints.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime


class GPUMetrics(BaseModel):
    """GPU metrics model."""
    
    gpu_id: int = Field(..., description="GPU identifier")
    gpu_name: str = Field(..., description="GPU name")
    utilization_percent: float = Field(..., ge=0, le=100, description="GPU utilization %")
    memory_used_mb: float = Field(..., ge=0, description="Memory used (MB)")
    memory_total_mb: float = Field(..., ge=0, description="Total memory (MB)")
    memory_utilization_percent: float = Field(..., ge=0, le=100, description="Memory utilization %")
    temperature_celsius: float = Field(..., description="GPU temperature (°C)")
    power_draw_watts: float = Field(..., description="Power draw (W)")


class CPUMetrics(BaseModel):
    """CPU metrics model."""
    
    cpu_count: int = Field(..., description="Number of CPUs")
    cpu_utilization_percent: float = Field(..., ge=0, le=100, description="CPU utilization %")
    cpu_frequency_mhz: float = Field(..., description="CPU frequency (MHz)")
    load_average_1m: float = Field(..., description="1-minute load average")
    load_average_5m: float = Field(..., description="5-minute load average")
    load_average_15m: float = Field(..., description="15-minute load average")


class MemoryMetrics(BaseModel):
    """Memory metrics model."""
    
    total_mb: float = Field(..., ge=0, description="Total memory (MB)")
    available_mb: float = Field(..., ge=0, description="Available memory (MB)")
    used_mb: float = Field(..., ge=0, description="Used memory (MB)")
    utilization_percent: float = Field(..., ge=0, le=100, description="Memory utilization %")
    swap_total_mb: float = Field(..., ge=0, description="Total swap (MB)")
    swap_used_mb: float = Field(..., ge=0, description="Used swap (MB)")


class ResourceMetrics(BaseModel):
    """Combined resource metrics."""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    instance_id: str = Field(..., description="Instance identifier")
    gpus: List[GPUMetrics] = Field(default_factory=list, description="GPU metrics")
    cpu: CPUMetrics = Field(..., description="CPU metrics")
    memory: MemoryMetrics = Field(..., description="Memory metrics")
```

---

### Step 5: Health Check API (5 minutes)

#### 5.1 Create src/api/health.py

```python
"""
Health Check Endpoints

Provides health check and readiness endpoints for the Resource Agent.
"""

from fastapi import APIRouter, status
from src.models.health import HealthStatus, DetailedHealthStatus
from src.config import settings
from datetime import datetime
import time

router = APIRouter(prefix="/health", tags=["health"])

# Track startup time
startup_time = time.time()


@router.get(
    "/",
    response_model=HealthStatus,
    status_code=status.HTTP_200_OK,
    summary="Basic health check"
)
async def health_check() -> HealthStatus:
    """
    Basic health check endpoint.
    
    Returns:
        HealthStatus: Current health status
    """
    uptime = time.time() - startup_time
    
    return HealthStatus(
        status="healthy",
        agent_id=settings.agent_id,
        agent_type=settings.agent_type,
        uptime_seconds=uptime
    )


@router.get(
    "/detailed",
    response_model=DetailedHealthStatus,
    status_code=status.HTTP_200_OK,
    summary="Detailed health check"
)
async def detailed_health_check() -> DetailedHealthStatus:
    """
    Detailed health check with component status.
    
    Returns:
        DetailedHealthStatus: Detailed health information
    """
    uptime = time.time() - startup_time
    
    # Check components (placeholder - will be implemented later)
    components = {
        "database": "healthy",
        "redis": "healthy",
        "nvidia_smi": "healthy",
        "orchestrator": "healthy"
    }
    
    metrics = {
        "uptime_seconds": uptime,
        "memory_usage_mb": 0.0,  # Placeholder
        "cpu_usage_percent": 0.0  # Placeholder
    }
    
    return DetailedHealthStatus(
        status="healthy",
        agent_id=settings.agent_id,
        agent_type=settings.agent_type,
        uptime_seconds=uptime,
        components=components,
        metrics=metrics
    )


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness check"
)
async def readiness_check() -> dict:
    """
    Kubernetes readiness probe endpoint.
    
    Returns:
        dict: Readiness status
    """
    return {"ready": True}


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness check"
)
async def liveness_check() -> dict:
    """
    Kubernetes liveness probe endpoint.
    
    Returns:
        dict: Liveness status
    """
    return {"alive": True}
```

---

### Step 6: Orchestrator Registration (7 minutes)

#### 6.1 Create src/core/registration.py

```python
"""
Orchestrator Registration

Handles registration and heartbeat with the orchestrator.
"""

import httpx
import asyncio
import logging
from typing import Optional
from datetime import datetime
from src.config import settings

logger = logging.getLogger("resource_agent.registration")


class OrchestratorClient:
    """Client for orchestrator communication."""
    
    def __init__(self):
        """Initialize orchestrator client."""
        self.base_url = settings.orchestrator_url
        self.register_endpoint = settings.orchestrator_register_endpoint
        self.heartbeat_interval = settings.orchestrator_heartbeat_interval
        self.registered = False
        self.heartbeat_task: Optional[asyncio.Task] = None
    
    async def register(self) -> bool:
        """
        Register agent with orchestrator.
        
        Returns:
            bool: True if registration successful
        """
        registration_data = {
            "agent_id": settings.agent_id,
            "agent_type": settings.agent_type,
            "capabilities": [
                "gpu_metrics_collection",
                "cpu_metrics_collection",
                "memory_metrics_collection",
                "utilization_analysis",
                "scaling_recommendations",
                "kvoptkit_integration"
            ],
            "endpoint": f"http://localhost:{settings.port}",
            "health_check_endpoint": f"http://localhost:{settings.port}/health",
            "version": "1.0.0",
            "status": "active"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}{self.register_endpoint}",
                    json=registration_data,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    self.registered = True
                    logger.info(f"Successfully registered with orchestrator: {settings.agent_id}")
                    return True
                else:
                    logger.error(f"Registration failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to register with orchestrator: {e}")
            return False
    
    async def send_heartbeat(self) -> bool:
        """
        Send heartbeat to orchestrator.
        
        Returns:
            bool: True if heartbeat successful
        """
        heartbeat_data = {
            "agent_id": settings.agent_id,
            "status": "active",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "requests_processed": 0,  # Placeholder
                "avg_response_time_ms": 0.0  # Placeholder
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/agents/heartbeat",
                    json=heartbeat_data,
                    timeout=5.0
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")
            return False
    
    async def start_heartbeat(self):
        """Start periodic heartbeat task."""
        while True:
            if self.registered:
                await self.send_heartbeat()
            await asyncio.sleep(self.heartbeat_interval)
    
    async def deregister(self):
        """Deregister agent from orchestrator."""
        try:
            async with httpx.AsyncClient() as client:
                await client.delete(
                    f"{self.base_url}/api/v1/agents/{settings.agent_id}",
                    timeout=5.0
                )
                logger.info(f"Deregistered from orchestrator: {settings.agent_id}")
        except Exception as e:
            logger.error(f"Failed to deregister: {e}")


# Global orchestrator client
orchestrator_client = OrchestratorClient()
```

---

### Step 7: Main Application (5 minutes)

#### 7.1 Create src/main.py

```python
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
from src.api import health


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
```

---

### Step 8: Testing Setup (5 minutes)

#### 8.1 Create tests/conftest.py

```python
"""
Pytest Configuration

Shared fixtures and configuration for tests.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    return {
        "agent_id": "resource-agent-test",
        "agent_type": "resource",
        "environment": "test",
        "port": 8003
    }
```

#### 8.2 Create tests/test_health.py

```python
"""
Health Check Tests

Tests for health check endpoints.
"""

import pytest
from fastapi import status


def test_health_check(client):
    """Test basic health check endpoint."""
    response = client.get("/health/")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "agent_id" in data
    assert "uptime_seconds" in data


def test_detailed_health_check(client):
    """Test detailed health check endpoint."""
    response = client.get("/health/detailed")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "components" in data
    assert "metrics" in data


def test_readiness_check(client):
    """Test readiness probe endpoint."""
    response = client.get("/health/ready")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["ready"] is True


def test_liveness_check(client):
    """Test liveness probe endpoint."""
    response = client.get("/health/live")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["alive"] is True


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["agent"] == "Resource Agent"
    assert "version" in data
```

---

### Step 9: Docker Configuration (3 minutes)

#### 9.1 Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for nvidia-smi
RUN apt-get update && apt-get install -y \
    nvidia-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY tests/ ./tests/

# Expose port
EXPOSE 8003

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003"]
```

#### 9.2 Create docker-compose.yml

```yaml
version: '3.8'

services:
  resource-agent:
    build: .
    ports:
      - "8003:8003"
      - "9093:9093"  # Prometheus metrics
    environment:
      - PORT=8003
      - ENVIRONMENT=development
      - LOG_LEVEL=INFO
      - AGENT_ID=resource-agent-001
      - ORCHESTRATOR_URL=http://orchestrator:8080
      - DATABASE_URL=postgresql://resource_user:resource_password@postgres:5432/resource_agent
      - REDIS_URL=redis://redis:6379/2
    depends_on:
      - postgres
      - redis
    volumes:
      - ./src:/app/src
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=resource_user
      - POSTGRES_PASSWORD=resource_password
      - POSTGRES_DB=resource_agent
    ports:
      - "5434:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6381:6379"

volumes:
  postgres_data:
```

---

### Step 10: Documentation (2 minutes)

#### 10.1 Create README.md

```markdown
# Resource Agent

AI-powered GPU/CPU/memory resource optimization agent for LLM infrastructure.

## Purpose

The Resource Agent maximizes GPU/CPU/memory utilization and optimizes resource allocation for LLM serving platforms (vLLM, TGI, SGLang).

## Features

- **GPU Metrics Collection**: Real-time GPU monitoring via nvidia-smi
- **CPU/Memory Metrics**: System resource monitoring via psutil
- **Utilization Analysis**: Identify underutilized resources
- **Scaling Recommendations**: Auto-scaling and consolidation
- **KVOptkit Integration**: KV cache optimization

## Quick Start

### Prerequisites

- Python 3.11+
- NVIDIA GPU (for GPU metrics)
- Docker & Docker Compose

### Installation

1. Clone the repository
2. Copy `.env.example` to `.env`
3. Install dependencies:

```bash
pip install -r requirements.txt
```

### Running Locally

```bash
uvicorn src.main:app --reload --port 8003
```

### Running with Docker

```bash
docker-compose up --build
```

## API Endpoints

### Health Checks

- `GET /health/` - Basic health check
- `GET /health/detailed` - Detailed health with components
- `GET /health/ready` - Readiness probe
- `GET /health/live` - Liveness probe

### Documentation

- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc

## Testing

```bash
pytest tests/ -v --cov=src
```

## Architecture

The Resource Agent is built with:

- **FastAPI**: High-performance web framework
- **Pydantic**: Data validation
- **nvidia-ml-py**: GPU metrics
- **psutil**: CPU/Memory metrics
- **PostgreSQL**: Primary database
- **Redis**: Caching and pub/sub

## Configuration

See `.env.example` for all configuration options.

## License

Proprietary
```

---

## Expected Outcomes

After completing this phase:

1. ✅ **Working FastAPI Application**
   - Health check endpoints functional
   - Orchestrator registration working
   - Basic structure in place

2. ✅ **Test Coverage**
   - Health check tests passing
   - 80%+ code coverage

3. ✅ **Docker Support**
   - Dockerfile ready
   - docker-compose.yml configured
   - GPU support enabled

4. ✅ **Documentation**
   - README with setup instructions
   - API documentation auto-generated

---

## Next Steps

After skeleton is complete:

- **PHASE3-3.2**: GPU Collector (nvidia-smi integration)
- **PHASE3-3.3**: CPU/Memory Collector (psutil integration)
- **PHASE3-3.4**: Analysis Engine (utilization analysis)
- **PHASE3-3.5**: KVOptkit Integration
- **PHASE3-3.6**: LangGraph Workflow
- **PHASE3-3.7**: API & Tests

---

## Success Criteria

- [ ] FastAPI app starts successfully
- [ ] Health endpoints return 200 OK
- [ ] Orchestrator registration succeeds
- [ ] All tests pass
- [ ] Docker container builds and runs
- [ ] Documentation is complete

---

**Ready to build the Resource Agent skeleton!** 🚀
