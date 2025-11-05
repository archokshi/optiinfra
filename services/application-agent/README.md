# Application Agent

**AI-powered quality monitoring and validation agent for LLM applications**

## Overview

The Application Agent monitors LLM application quality, detects regressions, validates changes, and provides AI-powered quality scoring using Groq's gpt-oss-20b model.

### Key Features

- **Quality Monitoring**: Track relevance, coherence, and hallucination metrics
- **Regression Detection**: Baseline tracking and anomaly detection with severity levels
- **Validation Engine**: A/B testing, approval workflows, and statistical analysis
- **LangGraph Workflow**: Automated quality validation pipeline
- **LLM Integration**: AI-powered quality scoring with Groq (gpt-oss-20b)
- **Configuration Monitoring**: Parameter tracking and optimization recommendations
- **Performance Testing**: Load testing with Locust
- **Comprehensive APIs**: 44 REST endpoints for complete control

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
