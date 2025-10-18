# Shared Python Utilities

**Common utilities and models shared across all Python agents**

## Overview

This package provides shared functionality for all OptiInfra agents:
- Database models and connections
- Common API clients
- Shared utilities (logging, metrics, etc.)
- Configuration management
- Error handling

## Architecture

```
shared/
├── optiinfra_common/
│   ├── __init__.py
│   ├── database/        # Database connections and models
│   ├── clients/         # API clients (Redis, ClickHouse, etc.)
│   ├── models/          # Shared Pydantic models
│   ├── utils/           # Utility functions
│   └── config/          # Configuration management
├── setup.py
└── README.md
```

## Installation

### For development (editable mode)
```bash
cd services/shared
pip install -e .
```

### For production
```bash
pip install ./services/shared
```

## Usage

```python
from optiinfra_common.database import get_db_session
from optiinfra_common.clients import RedisClient
from optiinfra_common.models import AgentRequest
from optiinfra_common.utils import setup_logging

# Setup logging
logger = setup_logging("my-agent")

# Get database session
async with get_db_session() as session:
    # Use session
    pass

# Use Redis client
redis_client = RedisClient()
await redis_client.set("key", "value")
```

## Development

### Run tests
```bash
pytest tests/ -v
```

### Build package
```bash
python setup.py sdist bdist_wheel
```

## Components

### Database
- PostgreSQL connection pooling
- SQLAlchemy models
- Migration utilities

### Clients
- Redis client with connection pooling
- ClickHouse client
- Qdrant client

### Models
- Shared Pydantic models
- Request/Response schemas
- Event schemas

### Utils
- Logging configuration
- Metrics collection
- Error handling
- Retry logic
