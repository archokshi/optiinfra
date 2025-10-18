# OptiInfra

**Multi-Agent AI Platform for Complete LLM Infrastructure Optimization**

Cut costs 50% • Improve performance 3x • Ensure quality

---

## 🚀 Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- Git 2.30+
- Make 4.0+

### Setup
```bash
# Clone repository
git clone https://github.com/yourorg/optiinfra.git
cd optiinfra

# Initial setup
make setup

# Update .env with your credentials
cp .env.example .env
# Edit .env file

# Start services
make dev
```

### Verify Installation
```bash
make verify
```

Expected output:
```
PostgreSQL... ✅ HEALTHY
ClickHouse... ✅ HEALTHY
Qdrant...     ✅ HEALTHY
Redis...      ✅ HEALTHY
```

---

## 🏗️ Architecture

OptiInfra uses a **multi-agent architecture** with 4 specialized agents:

1. **Cost Agent** - Optimize cloud spending (spot instances, right-sizing, RIs)
2. **Performance Agent** - Improve latency and throughput (KV cache, quantization)
3. **Resource Agent** - Maximize GPU/CPU utilization
4. **Application Agent** - Monitor quality and prevent regressions

All coordinated by a **Go-based orchestrator** with intelligent routing and conflict resolution.

---

## 📁 Project Structure

```
optiinfra/
├── services/          # Microservices (orchestrator, agents)
├── portal/            # Customer dashboard (Next.js)
├── docs/              # Documentation
├── scripts/           # Utility scripts
├── .windsurf/         # AI-assisted development prompts
└── k8s/               # Kubernetes deployment manifests
```

---

## 🛠️ Development

### Start services
```bash
make dev       # Foreground mode
make up        # Detached mode
```

### View logs
```bash
make logs
```

### Run tests
```bash
make test
```

### Stop services
```bash
make down
```

---

## 📊 Services

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 5432 | Primary database |
| ClickHouse | 8123/9000 | Time-series metrics |
| Qdrant | 6333 | Vector database (LLM memory) |
| Redis | 6379 | Caching and pub/sub |
| Orchestrator | 8080 | Request routing |
| Cost Agent | 8001 | Cost optimization |
| Performance Agent | 8002 | Performance optimization |
| Resource Agent | 8003 | Resource optimization |
| Application Agent | 8004 | Quality monitoring |
| Portal | 3000 | Customer dashboard |

---

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

---

## 🤝 Contributing

This project is currently in development. Contribution guidelines coming soon.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

## 🔗 Links

- [Website](https://optiinfra.ai)
- [Documentation](https://docs.optiinfra.ai)
- [API Reference](https://api.optiinfra.ai/docs)

---

**Built with ❤️ for the LLM infrastructure community**
