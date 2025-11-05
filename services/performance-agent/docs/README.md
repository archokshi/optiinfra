# Performance Agent Documentation

Welcome to the Performance Agent documentation! This guide will help you understand, deploy, and use the Performance Agent.

## 📚 Documentation Index

### Getting Started
- **[Quick Start Guide](user-guide/README.md#quick-start)** - Get up and running in 5 minutes
- **[Installation Guide](deployment/README.md)** - Detailed installation instructions

### API Reference
- **[REST API Documentation](api/README.md)** - Complete API reference
- **[OpenAPI/Swagger](http://localhost:8002/docs)** - Interactive API documentation
- **[ReDoc](http://localhost:8002/redoc)** - Alternative API documentation

### Guides
- **[User Guide](user-guide/README.md)** - How to use the Performance Agent
- **[Deployment Guide](deployment/README.md)** - Deploy to various environments
- **[Architecture Guide](architecture/README.md)** - System design and architecture
- **[Development Guide](development/README.md)** - Contributing and development

## 🚀 Quick Links

### For Users
- [Collecting Metrics](user-guide/README.md#use-case-1-monitor-vllm-instance)
- [Detecting Bottlenecks](user-guide/README.md#use-case-2-detect-bottlenecks)
- [Getting Recommendations](user-guide/README.md#use-case-3-get-optimization-recommendations)
- [Running Workflows](user-guide/README.md#use-case-4-run-optimization-workflow)

### For Operators
- [Docker Deployment](deployment/README.md#docker-deployment)
- [Kubernetes Deployment](deployment/README.md#kubernetes-deployment)
- [Configuration Options](deployment/README.md#configuration)
- [Monitoring Setup](deployment/README.md#monitoring)

### For Developers
- [Development Setup](development/README.md#development-setup)
- [Running Tests](development/README.md#running-tests)
- [Code Structure](development/README.md#project-structure)
- [Contributing](development/README.md#contributing)

## 📖 What is Performance Agent?

The Performance Agent is a FastAPI-based service that:
- **Monitors** LLM inference instances (vLLM, TGI, SGLang)
- **Analyzes** performance metrics to detect bottlenecks
- **Recommends** optimizations (quantization, batching, caching)
- **Manages** optimization workflows with approval gates
- **Validates** performance improvements

## 🎯 Key Features

- **Multi-Instance Support**: vLLM, TGI, SGLang
- **Automatic Bottleneck Detection**: Memory, latency, throughput issues
- **Smart Optimizations**: Quantization, batching, KV cache tuning
- **Workflow Management**: Approval gates and gradual rollouts
- **Performance Validation**: Automated testing and validation

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Performance Agent                      │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │Collectors│  │ Analysis │  │Optimizer │             │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘             │
│       │             │              │                    │
│  ┌────▼─────────────▼──────────────▼─────┐             │
│  │         Workflow Manager               │             │
│  └────────────────────────────────────────┘             │
│  ┌──────────────────────────────────────┐               │
│  │            FastAPI Layer              │               │
│  └──────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────┘
```

See [Architecture Guide](architecture/README.md) for details.

## 🔗 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check |
| `/api/v1/config` | GET | Get configuration |
| `/api/v1/metrics/collect` | POST | Collect metrics |
| `/api/v1/analysis/detect-bottlenecks` | POST | Detect bottlenecks |
| `/api/v1/optimization/recommend` | POST | Get recommendations |
| `/api/v1/workflows` | POST | Start workflow |
| `/api/v1/workflows/{id}` | GET | Get workflow status |

See [API Reference](api/README.md) for complete documentation.

## 📦 Installation

### Quick Install

```bash
# Clone repository
git clone <repository-url>
cd optiinfra/services/performance-agent

# Install dependencies
pip install -r requirements.txt

# Run the agent
uvicorn src.main:app --reload --port 8002
```

### Docker

```bash
docker run -d \
  --name performance-agent \
  -p 8002:8002 \
  performance-agent:latest
```

See [Deployment Guide](deployment/README.md) for more options.

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run performance tests
pytest tests/performance/ -v
```

Current test coverage: **77%** (149 tests)

## 📊 Performance

- **Response Time**: 8-15ms average
- **Throughput**: 100+ req/s
- **Concurrent Load**: 100+ concurrent requests
- **Success Rate**: 100%

See [Performance Test Results](../tests/performance/) for details.

## 🤝 Contributing

We welcome contributions! See the [Development Guide](development/README.md) for:
- Development setup
- Code style guidelines
- Testing requirements
- Pull request process

## 📝 License

[Add your license here]

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/optiinfra/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/optiinfra/discussions)
- **Email**: support@example.com

## 🗺️ Roadmap

- [ ] Support for more LLM frameworks
- [ ] Advanced optimization strategies
- [ ] ML-based bottleneck prediction
- [ ] Cost optimization integration
- [ ] Multi-region support

## 📚 Additional Resources

- [OptiInfra Architecture](../../docs/architecture.md)
- [Project Context](../../docs/context.md)
- [API Examples](user-guide/README.md#common-use-cases)

---

**Version**: 1.0.0  
**Last Updated**: 2024-01-01  
**Status**: Production Ready
