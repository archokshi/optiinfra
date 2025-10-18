# Development Guide

## Getting Started

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Git 2.30+
- Make 4.0+
- Go 1.21+ (for orchestrator development)
- Python 3.11+ (for agent development)
- Node.js 18+ (for portal development)

### Initial Setup

```bash
# Clone repository
git clone https://github.com/yourorg/optiinfra.git
cd optiinfra

# Run setup
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

## Development Workflow

### Start Services

```bash
# Foreground mode (see logs)
make dev

# Detached mode
make up
```

### View Logs

```bash
# All services
make logs

# Specific service
docker-compose logs -f postgres
docker-compose logs -f cost-agent
```

### Stop Services

```bash
make down
```

### Clean Up

```bash
# Remove containers and volumes
make clean
```

## Developing Orchestrator (Go)

### Setup

```bash
cd services/orchestrator
go mod download
```

### Run Locally

```bash
go run cmd/server/main.go
```

### Run Tests

```bash
go test ./... -v
go test ./... -cover
```

### Linting

```bash
go fmt ./...
go vet ./...
```

### Build

```bash
go build -o bin/orchestrator cmd/server/main.go
```

## Developing Agents (Python)

### Setup

```bash
cd services/cost-agent  # or any agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run Locally

```bash
uvicorn src.main:app --reload --port 8001
```

### Run Tests

```bash
pytest tests/ -v
pytest tests/ -v --cov=src
```

### Linting

```bash
black src/ tests/
flake8 src/ tests/
mypy src/
isort src/ tests/
```

## Developing Portal (Next.js)

### Setup

```bash
cd portal
npm install
```

### Run Locally

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Build

```bash
npm run build
npm start
```

### Linting

```bash
npm run lint
```

## Database Migrations

### PostgreSQL (Alembic)

```bash
cd services/cost-agent  # or any agent

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Testing

### Unit Tests

```bash
# All tests
make test

# Specific service
cd services/cost-agent
pytest tests/unit/ -v
```

### Integration Tests

```bash
cd services/cost-agent
pytest tests/integration/ -v
```

### E2E Tests

```bash
# Coming soon
```

## Code Style

### Go
- Follow [Effective Go](https://golang.org/doc/effective_go.html)
- Use `gofmt` for formatting
- Use `golint` for linting

### Python
- Follow [PEP 8](https://pep8.org/)
- Use `black` for formatting (line length: 88)
- Use `flake8` for linting
- Use `mypy` for type checking

### TypeScript
- Follow [TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)
- Use ESLint for linting
- Use Prettier for formatting

## Debugging

### Orchestrator (Go)

```bash
# Use delve debugger
dlv debug cmd/server/main.go
```

### Agents (Python)

```bash
# Use debugpy
python -m debugpy --listen 5678 --wait-for-client src/main.py
```

### Portal (Next.js)

Use browser DevTools or VS Code debugger.

## Environment Variables

See `.env.example` for all available variables.

Key variables:
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `OPENAI_API_KEY` - OpenAI API key
- `LOG_LEVEL` - Logging level (debug, info, warn, error)

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.
