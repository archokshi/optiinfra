# Resource Agent 🔧

**AI-powered GPU/CPU/memory resource optimization agent for LLM infrastructure**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-52%20passing-brightgreen.svg)](./tests/)
[![Coverage](https://img.shields.io/badge/coverage-66%25-yellow.svg)](./htmlcov/)

---

## 📋 Overview

The Resource Agent is a production-ready microservice that maximizes GPU/CPU/memory utilization through intelligent monitoring, analysis, and optimization. It provides real-time resource metrics, bottleneck detection, and AI-powered optimization recommendations.

### Key Features

- 🎮 **GPU Monitoring** - NVIDIA GPU metrics via nvidia-smi/pynvml
- 💻 **System Monitoring** - CPU, memory, disk, and network metrics
- 📊 **Resource Analysis** - Bottleneck detection and efficiency scoring
- 🚀 **LMCache Integration** - KV cache optimization for LLM inference
- 🤖 **AI-Powered Insights** - LLM-generated optimization recommendations via Groq
- 🔄 **Optimization Workflows** - Automated resource optimization orchestration
- 📈 **21 REST APIs** - Comprehensive API for metrics and analysis
- ✅ **Production-Ready** - 52 tests, 66% coverage, load tested

---

## 🏗️ Architecture

```
resource-agent/
├── src/
│   ├── api/              # FastAPI REST endpoints (21 endpoints)
│   │   ├── health.py     # Health checks
│   │   ├── gpu.py        # GPU metrics
│   │   ├── system.py     # System metrics
│   │   ├── analysis.py   # Resource analysis
│   │   ├── lmcache.py    # LMCache management
│   │   └── optimize.py   # Optimization workflows
│   ├── collectors/       # Metrics collectors
│   │   ├── gpu_collector.py      # GPU metrics (pynvml)
│   │   └── system_collector.py   # System metrics (psutil)
│   ├── analysis/         # Analysis engine
│   │   └── analyzer.py   # Bottleneck detection, efficiency scoring
│   ├── lmcache/          # LMCache integration
│   │   └── client.py     # LMCache client wrapper
│   ├── workflow/         # Optimization workflows
│   │   └── optimizer.py  # Workflow orchestrator
│   ├── llm/              # LLM integration
│   │   ├── llm_client.py         # Groq API client
│   │   └── prompt_templates.py   # Prompt templates
│   ├── models/           # Pydantic models
│   ├── core/             # Core utilities
│   └── main.py           # FastAPI application
├── tests/                # Comprehensive tests (52 tests)
│   ├── load/             # Locust load tests
│   ├── fixtures.py       # Test fixtures
│   └── helpers.py        # Test utilities
├── docs/                 # Documentation
│   ├── API_EXAMPLES.md   # API usage examples
│   ├── LOAD_TESTING.md   # Load testing guide
│   ├── ARCHITECTURE.md   # Architecture details
│   └── DEPLOYMENT.md     # Deployment guide
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- (Optional) NVIDIA GPU with drivers
- (Optional) Groq API key for LLM insights

### Installation

```bash
# Clone repository
cd services/resource-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings (optional)
```

### Run Locally

```bash
# Start the agent
python -m uvicorn src.main:app --port 8003 --reload

# Agent will be available at http://localhost:8003
```

### Verify Installation

```bash
# Health check
curl http://localhost:8003/health/

# Get system metrics
curl http://localhost:8003/system/metrics

# Run analysis
curl http://localhost:8003/analysis/
```

---

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost:8003/docs
- **ReDoc**: http://localhost:8003/redoc

### API Endpoints (21 Total)

#### Health (5 endpoints)
- `GET /` - Root endpoint
- `GET /health/` - Basic health check
- `GET /health/detailed` - Detailed health status
- `GET /health/ready` - Readiness probe
- `GET /health/live` - Liveness probe

#### GPU (3 endpoints)
- `GET /gpu/info` - GPU availability and info
- `GET /gpu/metrics` - All GPU metrics
- `GET /gpu/metrics/{id}` - Single GPU metrics

#### System (5 endpoints)
- `GET /system/metrics` - All system metrics
- `GET /system/metrics/cpu` - CPU metrics only
- `GET /system/metrics/memory` - Memory metrics only
- `GET /system/metrics/disk` - Disk metrics only
- `GET /system/metrics/network` - Network metrics only

#### Analysis (2 endpoints)
- `GET /analysis/` - Complete resource analysis
- `GET /analysis/health-score` - Health score only

#### LMCache (5 endpoints)
- `GET /lmcache/status` - Cache status and metrics
- `GET /lmcache/config` - Get cache configuration
- `POST /lmcache/config` - Update cache configuration
- `POST /lmcache/optimize` - Optimize cache
- `DELETE /lmcache/clear` - Clear cache

#### Optimization (1 endpoint)
- `POST /optimize/run` - Run optimization workflow

### Example Usage

See [API Examples](./docs/API_EXAMPLES.md) for detailed examples.

```bash
# Get system health score
curl http://localhost:8003/analysis/health-score

# Run optimization workflow
curl -X POST http://localhost:8003/optimize/run
```

---

## 🧪 Testing

### Run All Tests

```bash
# Run all tests with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Expected: 52 tests passing, 66% coverage
```

### Run Specific Tests

```bash
# Unit tests only
pytest tests/test_analyzer.py -v

# Integration tests
pytest tests/test_integration.py -v

# Performance tests
pytest tests/test_performance.py -v
```

### Load Testing

```bash
# Install Locust
pip install locust

# Run load test
cd tests/load
locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 3m --host http://localhost:8003
```

See [Load Testing Guide](./docs/LOAD_TESTING.md) for details.

---

## ⚙️ Configuration

### Environment Variables

```bash
# Agent Configuration
AGENT_ID=resource-agent-001
AGENT_NAME=Resource Agent
ENVIRONMENT=development
PORT=8003

# Orchestrator
ORCHESTRATOR_URL=http://localhost:8000

# LLM Configuration (Optional)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=gpt-oss-20b

# Logging
LOG_LEVEL=INFO
```

See [Configuration Guide](./docs/CONFIGURATION.md) for all options.

---

## 🐳 Docker Deployment

### Build and Run

```bash
# Build image
docker build -t resource-agent:latest .

# Run container
docker run -p 8003:8003 --env-file .env resource-agent:latest

# Or use Docker Compose
docker-compose up -d
```

### Production Deployment

See [Deployment Guide](./docs/DEPLOYMENT.md) for production setup.

---

## 🔧 Development

### Setup Development Environment

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests in watch mode
pytest-watch tests/

# Format code
black src/ tests/

# Lint code
flake8 src/ tests/
```

### Contributing

See [Development Guide](./docs/DEVELOPMENT.md) for contribution guidelines.

---

## 📊 Performance

### Response Times (P95)

| Endpoint | Target | Actual |
|----------|--------|--------|
| `/health/` | < 50ms | ~20ms |
| `/system/metrics` | < 500ms | ~200ms |
| `/analysis/` | < 2000ms | ~1200ms |
| `/optimize/run` | < 5000ms | ~1500ms |

### Load Test Results

- **Light Load** (10 users): 10+ RPS, < 0.1% errors
- **Medium Load** (50 users): 40+ RPS, < 0.5% errors
- **Heavy Load** (100 users): 80+ RPS, < 1% errors

---

## 🛠️ Technology Stack

- **Framework**: FastAPI 0.104+
- **Metrics Collection**: psutil, pynvml
- **LLM Integration**: Groq API (gpt-oss-20b)
- **Data Validation**: Pydantic 2.0+
- **Testing**: pytest, Locust
- **Async**: asyncio, httpx
- **Monitoring**: Prometheus-compatible

---

## 📖 Documentation

- [API Examples](./docs/API_EXAMPLES.md) - Complete API usage examples
- [Load Testing](./docs/LOAD_TESTING.md) - Load testing guide
- [Architecture](./docs/ARCHITECTURE.md) - System architecture
- [Deployment](./docs/DEPLOYMENT.md) - Deployment guide
- [Configuration](./docs/CONFIGURATION.md) - Configuration options
- [Troubleshooting](./docs/TROUBLESHOOTING.md) - Common issues
- [Development](./docs/DEVELOPMENT.md) - Development guide

---

## 🎯 Roadmap

- [x] GPU/CPU/Memory monitoring
- [x] Resource analysis engine
- [x] LMCache integration
- [x] LLM-powered insights
- [x] Optimization workflows
- [x] Comprehensive testing
- [x] Load testing
- [x] Complete documentation
- [ ] Kubernetes deployment
- [ ] Prometheus metrics export
- [ ] Grafana dashboards

---

## 📄 License

Part of OptiInfra v1.0 - AI-powered LLM infrastructure optimization platform.

---

## 🤝 Support

For issues, questions, or contributions:
- Check [Troubleshooting Guide](./docs/TROUBLESHOOTING.md)
- Review [Documentation](./docs/)
- Open an issue on GitHub

---

**Resource Agent v1.0.0** - Production Ready 🚀
