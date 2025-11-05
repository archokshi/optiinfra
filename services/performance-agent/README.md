# Performance Agent

**AI-powered performance optimization agent for LLM infrastructure**

## Overview

The Performance Agent improves latency and throughput through:
- KV cache tuning
- Quantization optimization (FP16 → FP8 → INT8)
- Batch size optimization
- Model parallelism configuration
- Performance anomaly detection

## Architecture

```
performance-agent/
├── src/
│   ├── api/             # FastAPI endpoints
│   ├── workflows/       # LangGraph workflows
│   ├── collectors/      # Performance metrics collectors
│   ├── analyzers/       # Performance analysis logic
│   └── executors/       # Optimization executors
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── requirements.txt
├── Dockerfile
└── README.md
```

## Technology Stack

- **Framework**: FastAPI
- **Workflows**: LangGraph
- **Metrics**: Prometheus client
- **Database**: SQLAlchemy (PostgreSQL)
- **LLM**: OpenAI/Anthropic
- **Testing**: pytest

## Development

### Prerequisites
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

### Health Check
```
GET /health
```

### Performance Analysis
```
POST /api/v1/analyze
```

### Recommendations
```
GET  /api/v1/recommendations
POST /api/v1/recommendations/:id/approve
```

### Optimizations
```
GET  /api/v1/optimizations
POST /api/v1/optimizations
```

## Configuration

Environment variables:
- `PERFORMANCE_AGENT_PORT` - HTTP server port (default: 8002)
- `DATABASE_URL` - PostgreSQL connection string
- `OPENAI_API_KEY` - OpenAI API key

## Deployment

See [Deployment Guide](../../docs/DEPLOYMENT.md) for production deployment instructions.
