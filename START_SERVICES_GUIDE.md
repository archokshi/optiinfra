# How to Start All OptiInfra Services

**Last Updated**: October 28, 2025  
**Status**: All Python agents are ready to start.

---

## Prerequisites

- Docker Desktop running locally.
- Database containers started with `docker-compose up -d postgres redis clickhouse qdrant`.
- Python 3.11 environment with each agent's dependencies installed (`pip install -r services\<agent>\requirements.txt`).
- Required environment variables defined in each agent's `.env` file (see examples in the service folders).

---

## What Should Already Be Running

The Docker stack provides these services:

- PostgreSQL (port 5432)
- Redis (port 6379)
- ClickHouse (ports 8123, 9000)
- Qdrant (ports 6333, 6334)
- Prometheus (port 9090)
- Grafana (port 3000)

The new launch script checks for the four databases (PostgreSQL, Redis, ClickHouse, Qdrant) before starting any agents.

---

## Option 1: PowerShell Script (recommended)

Run the helper script from the repository root:

```powershell
# Core Python agents only
.\start-all-services.ps1

# Include Orchestrator (8080) and Portal (3001)
.\start-all-services.ps1 -IncludeOptional
```

The script:

1. Verifies Docker is available.
2. Confirms the four database containers are running.
3. Starts each Python agent in its own PowerShell window using `uvicorn`.
4. Optionally starts the Go orchestrator (`go run ./cmd/orchestrator`) and the portal (`npm run dev -- --port 3001`) when `-IncludeOptional` is set and toolchains are available.
5. Prints the service URLs for quick access.

Close the spawned windows or press `Ctrl+C` in each to stop the services.

---

## Option 2: Start Services Manually

Open four PowerShell windows and run the following commands:

### Cost Agent (port 8001)
```powershell
cd services\cost-agent
python -m uvicorn src.main:app --host 0.0.0.0 --port 8001
```

### Performance Agent (port 8002)
```powershell
cd services\performance-agent
python -m uvicorn src.main:app --host 0.0.0.0 --port 8002
```

### Resource Agent (port 8003)
```powershell
cd services\resource-agent
python -m uvicorn src.main:app --host 0.0.0.0 --port 8003
```

### Application Agent (port 8004)
```powershell
cd services\application-agent
python -m uvicorn src.main:app --host 0.0.0.0 --port 8004
```

### Orchestrator (optional, port 8080)
```powershell
cd services\orchestrator
go run ./cmd/orchestrator
```

### Portal UI (optional, port 3001)
```powershell
cd portal
npm install  # first run
npm run dev -- --port 3001
```

---

## Health Checks

After the agents start, confirm they are responding:

```powershell
curl http://localhost:8001/health  # Cost Agent
curl http://localhost:8002/health  # Performance Agent
curl http://localhost:8003/health  # Resource Agent
curl http://localhost:8004/health  # Application Agent
```

Each request should return `{"status": "healthy"}`.

---

## Running Tests

Once all services respond, execute the end-to-end suite:

```powershell
python -m pytest tests/e2e tests/integration tests/performance tests/security -v
```

Or target specific groups:

```powershell
python -m pytest tests/e2e -v
python -m pytest tests/integration -v
python -m pytest tests/performance -v
python -m pytest tests/security -v
```

---

## Troubleshooting

### Containers Not Running

```powershell
docker-compose up -d postgres redis clickhouse qdrant
```

### Port In Use

```powershell
netstat -ano | findstr :8001
taskkill /PID <process_id> /F
```

### Missing Dependencies

```powershell
cd services\<agent-name>
pip install -r requirements.txt
```

---

With all four agents active you can run the full OptiInfra test suite without the orchestrator or portal services.
