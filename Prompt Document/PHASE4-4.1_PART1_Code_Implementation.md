# PHASE4-4.1 PART1: Application Agent Skeleton - Code Implementation Plan

**Phase**: PHASE4-4.1  
**Agent**: Application Agent  
**Objective**: Create FastAPI skeleton and orchestrator registration  
**Estimated Time**: 25 minutes (15m skeleton + 10m registration)  
**Priority**: HIGH  
**Dependencies**: Orchestrator service (PHASE0.5, 0.6, 0.10)

---

## Overview

This phase creates the foundational FastAPI application for the Application Agent, which monitors LLM output quality, detects regressions, and validates optimization changes before production deployment.

---

## Application Agent Purpose

### **Primary Responsibilities**
1. **Quality Monitoring** - Track LLM output quality metrics
2. **Regression Detection** - Detect quality degradation
3. **Validation Engine** - A/B testing for optimization changes
4. **Approval/Rejection** - Auto-approve or reject based on quality impact
5. **Hallucination Detection** - Identify and flag hallucinated content

### **Key Metrics**
- Relevance score (0-100)
- Coherence score (0-100)
- Hallucination rate (%)
- Toxicity score (0-100)
- Response quality (0-100)

---

## Implementation Plan

### Step 1: Create Directory Structure (3 minutes)

```bash
services/application-agent/
├── src/
│   ├── api/              # FastAPI endpoints
│   │   └── health.py     # Health check endpoints
│   ├── core/             # Core utilities
│   │   ├── __init__.py
│   │   ├── config.py     # Configuration management
│   │   ├── logger.py     # Logging setup
│   │   └── registration.py  # Orchestrator registration
│   ├── models/           # Pydantic models
│   │   └── __init__.py
│   ├── __init__.py
│   └── main.py           # FastAPI application
├── tests/
│   ├── __init__.py
│   └── test_health.py    # Health endpoint tests
├── .env.example          # Environment variables template
├── .gitignore
├── pytest.ini            # Pytest configuration
├── README.md
└── requirements.txt      # Python dependencies
```

---

### Step 2: Create Configuration (src/core/config.py) (3 minutes)

```python
"""
Application Agent Configuration

Manages all configuration settings from environment variables.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application Agent settings."""
    
    # Agent Identity
    agent_id: str = "application-agent-001"
    agent_name: str = "Application Agent"
    agent_type: str = "application"
    version: str = "1.0.0"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8004
    environment: str = "development"
    
    # Orchestrator Configuration
    orchestrator_url: str = "http://localhost:8000"
    registration_enabled: bool = True
    heartbeat_interval: int = 30  # seconds
    
    # Quality Monitoring Configuration
    quality_threshold: float = 0.85  # 85% minimum quality score
    regression_threshold: float = 0.05  # 5% max quality drop
    hallucination_threshold: float = 0.10  # 10% max hallucination rate
    
    # LLM Configuration (for quality scoring)
    groq_api_key: Optional[str] = None
    groq_model: str = "gpt-oss-20b"
    llm_timeout: int = 30
    llm_max_retries: int = 3
    
    # Database Configuration (optional for now)
    database_url: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
```

**Key Features:**
- Agent identity and metadata
- Orchestrator connection settings
- Quality thresholds for validation
- LLM integration for quality scoring
- Environment-based configuration

---

### Step 3: Create Logger (src/core/logger.py) (2 minutes)

```python
"""
Logging Configuration

Provides structured logging for the Application Agent.
"""

import logging
import sys
from typing import Any
from .config import settings


def setup_logger(name: str = "application-agent") -> logging.Logger:
    """
    Set up structured logger.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Format
    if settings.log_format == "json":
        formatter = logging.Formatter(
            '{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","message":"%(message)s"}'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


# Global logger instance
logger = setup_logger()
```

---

### Step 4: Create Orchestrator Registration (src/core/registration.py) (5 minutes)

```python
"""
Orchestrator Registration Client

Handles registration, heartbeat, and deregistration with the orchestrator.
"""

import asyncio
import httpx
from typing import Dict, Any, Optional
from .config import settings
from .logger import logger


class OrchestratorClient:
    """Client for orchestrator communication."""
    
    def __init__(self):
        self.base_url = settings.orchestrator_url
        self.agent_id = settings.agent_id
        self.registered = False
        self.heartbeat_task: Optional[asyncio.Task] = None
    
    async def register(self) -> bool:
        """
        Register agent with orchestrator.
        
        Returns:
            True if registration successful
        """
        if not settings.registration_enabled:
            logger.info("Registration disabled, skipping")
            return True
        
        payload = {
            "agent_id": settings.agent_id,
            "agent_name": settings.agent_name,
            "agent_type": settings.agent_type,
            "version": settings.version,
            "host": settings.host,
            "port": settings.port,
            "capabilities": [
                "quality_monitoring",
                "regression_detection",
                "validation_engine",
                "hallucination_detection",
                "ab_testing"
            ],
            "status": "active"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/agents/register",
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    self.registered = True
                    logger.info(f"Successfully registered with orchestrator: {self.agent_id}")
                    return True
                else:
                    logger.error(f"Registration failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return False
    
    async def send_heartbeat(self) -> bool:
        """
        Send heartbeat to orchestrator.
        
        Returns:
            True if heartbeat successful
        """
        if not self.registered:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/agents/{self.agent_id}/heartbeat",
                    json={"status": "active"},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    logger.debug(f"Heartbeat sent successfully")
                    return True
                else:
                    logger.warning(f"Heartbeat failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.warning(f"Heartbeat error: {str(e)}")
            return False
    
    async def heartbeat_loop(self):
        """Continuous heartbeat loop."""
        while self.registered:
            await self.send_heartbeat()
            await asyncio.sleep(settings.heartbeat_interval)
    
    async def start_heartbeat(self):
        """Start heartbeat task."""
        if self.registered and not self.heartbeat_task:
            self.heartbeat_task = asyncio.create_task(self.heartbeat_loop())
            logger.info("Heartbeat task started")
    
    async def deregister(self) -> bool:
        """
        Deregister agent from orchestrator.
        
        Returns:
            True if deregistration successful
        """
        if not self.registered:
            return True
        
        # Stop heartbeat
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/api/v1/agents/{self.agent_id}",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    self.registered = False
                    logger.info(f"Successfully deregistered from orchestrator")
                    return True
                else:
                    logger.error(f"Deregistration failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Deregistration error: {str(e)}")
            return False


# Global orchestrator client
orchestrator_client = OrchestratorClient()
```

---

### Step 5: Create Health Endpoints (src/api/health.py) (3 minutes)

```python
"""
Health Check Endpoints

Provides health status and readiness checks for the Application Agent.
"""

from fastapi import APIRouter, status
from typing import Dict, Any
from datetime import datetime
from ..core.config import settings
from ..core.registration import orchestrator_client

router = APIRouter(tags=["health"])


@router.get("/", status_code=status.HTTP_200_OK)
async def root() -> Dict[str, Any]:
    """Root endpoint."""
    return {
        "agent": settings.agent_name,
        "version": settings.version,
        "status": "active",
        "agent_id": settings.agent_id
    }


@router.get("/health/", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "agent_id": settings.agent_id
    }


@router.get("/health/detailed", status_code=status.HTTP_200_OK)
async def detailed_health() -> Dict[str, Any]:
    """Detailed health check with component status."""
    components = {
        "orchestrator": "healthy" if orchestrator_client.registered else "disconnected",
        "api": "healthy"
    }
    
    overall_status = "healthy" if all(
        s == "healthy" for s in components.values()
    ) else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "agent_id": settings.agent_id,
        "version": settings.version,
        "components": components,
        "uptime_seconds": 0  # TODO: Track actual uptime
    }


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict[str, str]:
    """Kubernetes readiness probe."""
    return {"status": "ready"}


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, str]:
    """Kubernetes liveness probe."""
    return {"status": "alive"}
```

---

### Step 6: Create Main Application (src/main.py) (5 minutes)

```python
"""
Application Agent - Main FastAPI Application

Monitors LLM output quality, detects regressions, and validates optimization changes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .core.config import settings
from .core.logger import logger
from .core.registration import orchestrator_client
from .api import health


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
```

---

### Step 7: Create Dependencies (requirements.txt) (2 minutes)

```txt
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# HTTP Client
httpx==0.25.1

# Utilities
python-dotenv==1.0.0
```

---

### Step 8: Create Environment Template (.env.example) (2 minutes)

```bash
# Agent Configuration
AGENT_ID=application-agent-001
AGENT_NAME=Application Agent
AGENT_TYPE=application
VERSION=1.0.0

# Server Configuration
HOST=0.0.0.0
PORT=8004
ENVIRONMENT=development

# Orchestrator Configuration
ORCHESTRATOR_URL=http://localhost:8000
REGISTRATION_ENABLED=true
HEARTBEAT_INTERVAL=30

# Quality Thresholds
QUALITY_THRESHOLD=0.85
REGRESSION_THRESHOLD=0.05
HALLUCINATION_THRESHOLD=0.10

# LLM Configuration (Optional - for quality scoring)
GROQ_API_KEY=
GROQ_MODEL=gpt-oss-20b
LLM_TIMEOUT=30
LLM_MAX_RETRIES=3

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

### Step 9: Create Tests (tests/test_health.py) (2 minutes)

```python
"""
Tests for health endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["agent"] == "Application Agent"
    assert data["status"] == "active"


def test_health_check():
    """Test basic health check."""
    response = client.get("/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_detailed_health():
    """Test detailed health check."""
    response = client.get("/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "components" in data
    assert "api" in data["components"]


def test_readiness_check():
    """Test readiness probe."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_liveness_check():
    """Test liveness probe."""
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"
```

---

### Step 10: Create pytest.ini (1 minute)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

---

## Expected Outcomes

After completing this phase:

1. ✅ **FastAPI Application Running**
   - Accessible at `http://localhost:8004`
   - Health endpoints functional
   - API documentation at `/docs`

2. ✅ **Orchestrator Registration**
   - Agent registers on startup
   - Heartbeat sent every 30 seconds
   - Deregisters on shutdown

3. ✅ **Configuration Management**
   - Environment-based configuration
   - Sensible defaults
   - Easy to customize

4. ✅ **Logging**
   - Structured logging
   - Configurable log level
   - JSON or text format

5. ✅ **Tests**
   - Health endpoint tests
   - 100% coverage for skeleton

---

## Success Criteria

- [ ] FastAPI app starts successfully
- [ ] Health endpoints return 200 OK
- [ ] Orchestrator registration succeeds
- [ ] Heartbeat mechanism working
- [ ] All tests passing
- [ ] API documentation accessible
- [ ] Logs are structured and readable

---

## Next Steps

After PHASE4-4.1 is complete:

**PHASE4-4.2: Quality Monitoring**
- Relevance scoring
- Coherence detection
- Hallucination detection
- Quality metrics collection

---

**Application Agent skeleton ready for quality monitoring implementation!** 🎯
