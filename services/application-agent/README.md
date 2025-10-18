# Application Agent

**AI-powered quality monitoring agent for LLM infrastructure**

## Overview

The Application Agent ensures quality and prevents regressions through:
- LLM output quality monitoring
- Hallucination detection
- Toxic content detection
- Quality baseline establishment
- A/B testing validation
- Auto-rollback on quality degradation

## Architecture

```
application-agent/
├── src/
│   ├── api/             # FastAPI endpoints
│   ├── workflows/       # LangGraph workflows
│   ├── collectors/      # Quality metrics collectors
│   ├── analyzers/       # Quality analysis logic
│   └── validators/      # Change validation
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
- **Quality Scoring**: Custom models + LLM-as-judge
- **Database**: SQLAlchemy (PostgreSQL)
- **LLM**: OpenAI/Anthropic
- **Testing**: pytest

## Development

### Prerequisites
- Python 3.11+
- Docker (for local testing)

### Setup
```bash
cd services/application-agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run locally
```bash
uvicorn src.main:app --reload --port 8004
```

### Run tests
```bash
pytest tests/ -v --cov=src
```

## API Endpoints

### Health Check
```
GET /health
```

### Quality Analysis
```
POST /api/v1/analyze
```

### Baselines
```
GET  /api/v1/baselines
POST /api/v1/baselines
```

### Validations
```
POST /api/v1/validate
```

## Configuration

Environment variables:
- `APPLICATION_AGENT_PORT` - HTTP server port (default: 8004)
- `DATABASE_URL` - PostgreSQL connection string
- `OPENAI_API_KEY` - OpenAI API key

## Deployment

See [Deployment Guide](../../docs/DEPLOYMENT.md) for production deployment instructions.
