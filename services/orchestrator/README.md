# OptiInfra Orchestrator

Go-based orchestrator for coordinating multiple AI agents in the OptiInfra platform.

## Features

- HTTP server (Gin framework)
- Structured JSON logging (Zap)
- Health check endpoint
- Configuration from environment
- Graceful shutdown
- Docker support

## Development

### Prerequisites

- Go 1.21+
- Docker (optional)

### Running Locally

```bash
# Install dependencies
go mod download

# Run
make run

# Or
go run ./cmd/orchestrator
```

### Building

```bash
# Build binary
make build

# Build Docker image
make docker-build
```

### Testing

```bash
# Run tests
make test

# View coverage
open coverage.html
```

## API Endpoints

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-16T10:00:00Z",
  "version": "0.1.0",
  "uptime": "5m30s"
}
```

### GET /

Service info endpoint.

**Response:**
```json
{
  "service": "OptiInfra Orchestrator",
  "version": "0.1.0",
  "status": "running"
}
```

## Configuration

Environment variables:

- `ORCHESTRATOR_PORT` - Port to listen on (default: 8080)
- `ENVIRONMENT` - Environment name (default: development)
- `LOG_LEVEL` - Log level: debug, info, warn, error (default: info)

## Docker

```bash
# Build image
docker build -t optiinfra-orchestrator .

# Run container
docker run -p 8080:8080 optiinfra-orchestrator

# Or use docker-compose (from project root)
docker-compose up orchestrator
```

## Architecture

```
main.go
  ↓
config.Load()    # Load environment variables
  ↓
logger.New()     # Initialize structured logger
  ↓
gin.New()        # Create HTTP router
  ↓
RegisterRoutes() # Register endpoints
  ↓
srv.Start()      # Start HTTP server
  ↓
GracefulShutdown() # Wait for SIGTERM
```

## Next Steps

After this pilot phase:
- Add agent registry (Foundation phase)
- Add request routing
- Add coordination logic
- Add authentication
- Add metrics (Prometheus)
