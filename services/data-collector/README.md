# OptiInfra Data Collector Service

Unified data collection service that collects all data types (cost, performance, resource, application) from all cloud providers.

## Features

- **Multi-Cloud Support**: 
  - ✅ **Vultr** (Phase 6.1 - Implemented)
  - 📋 **AWS** (Phase 6.5 - Placeholder)
  - 📋 **GCP** (Phase 6.5 - Placeholder)
  - 📋 **Azure** (Phase 6.5 - Placeholder)
- **Multi-Data Types**: Cost, Performance, Resource, Application metrics
- **Automated Collection**: Scheduled collection every 15 minutes (Phase 6.2)
- **Manual Triggers**: API endpoints for on-demand collection
- **Storage Integration**: ClickHouse, PostgreSQL, Redis
- **Real-time Events**: Redis pub/sub for live updates

## Architecture

```
Data Collector Service (Port 8005)
├── Collectors (Cloud-specific)
│   ├── Vultr (Cost, Performance, Resource, Application)
│   ├── AWS (Cost, Performance, Resource)
│   ├── GCP (Cost, Performance, Resource)
│   └── Azure (Cost, Performance, Resource)
├── Storage Writers
│   ├── ClickHouse (Time-series metrics)
│   ├── PostgreSQL (Metadata)
│   └── Redis (Real-time events)
└── API Endpoints
    ├── /health
    ├── /api/v1/collect/trigger
    ├── /api/v1/collect/status/{task_id}
    └── /api/v1/collect/history
```

## API Endpoints

### Health Check
```
GET /health
```

### Trigger Collection
```
POST /api/v1/collect/trigger
{
  "customer_id": "alpesh_chokshi",
  "provider": "vultr",
  "data_types": ["cost"]
}
```

### Get Collection Status
```
GET /api/v1/collect/status/{task_id}
```

### Get Collection History
```
GET /api/v1/collect/history?customer_id=alpesh_chokshi&limit=100
```

## Environment Variables

```bash
# Service Configuration
SERVICE_PORT=8005
HOST=0.0.0.0

# Cloud Provider API Keys
VULTR_API_KEY=your_vultr_api_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
GCP_SERVICE_ACCOUNT_JSON=your_gcp_json
AZURE_SUBSCRIPTION_ID=your_azure_sub

# Database Configuration
CLICKHOUSE_HOST=clickhouse
CLICKHOUSE_PORT=9000
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
REDIS_HOST=redis
REDIS_PORT=6379

# Collection Configuration
COLLECTION_INTERVAL_MINUTES=15
COLLECTION_TIMEOUT_SECONDS=300
MAX_RETRIES=3
```

## Development

### Run Locally
```bash
cd services/data-collector
pip install -r requirements.txt
python -m src.main
```

### Run with Docker
```bash
docker-compose up data-collector
```

## Testing

```bash
# Test health endpoint
curl http://localhost:8005/health

# Test collection trigger
curl -X POST http://localhost:8005/api/v1/collect/trigger \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "test", "provider": "vultr", "data_types": ["cost"]}'
```

## Phase 6.1 Implementation Status

- ✅ Service structure created
- ✅ Base collector class
- ✅ Vultr cost collector
- ✅ Storage writers (ClickHouse, PostgreSQL, Redis)
- ✅ FastAPI application
- ✅ Docker configuration
- ⏳ Celery background jobs (Phase 6.2)
- ⏳ Performance collectors (Phase 6.4)
- ⏳ Resource collectors (Phase 6.4)
- ⏳ Application collectors (Phase 6.5)
