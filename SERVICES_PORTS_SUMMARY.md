# OptiInfra Services & Ports Summary

## Running Services Overview

**Total Services: 19**
- Application Services: 7
- Data Collection: 3
- Databases: 3
- Monitoring: 3
- Exporters: 3

---

## Services by Category

### 1. Application Services (7 services)

| Service | Container Name | Port(s) | Status | Purpose |
|---------|---------------|---------|--------|---------|
| **Portal** | optiinfra-portal | 3001→3000 | ✅ Running | Web UI (Next.js) |
| **Orchestrator** | optiinfra-orchestrator | 8080 | ✅ Healthy | Go orchestration service |
| **Cost Agent** | optiinfra-cost-agent | 8001 | ✅ Healthy | Cost data collection |
| **Performance Agent** | optiinfra-performance-agent | 8002 | ✅ Running | Performance monitoring |
| **Resource Agent** | optiinfra-resource-agent | 8003 | ✅ Running | Resource tracking |
| **Application Agent** | optiinfra-application-agent | 8004 | ✅ Running | LLM quality monitoring |
| **Qdrant** | optiinfra-qdrant | 6333-6334 | ✅ Healthy | Vector database |

### 2. Data Collection Services (3 services)

| Service | Container Name | Port(s) | Status | Purpose |
|---------|---------------|---------|--------|---------|
| **Data Collector** | optiinfra-data-collector | 8005 | ✅ Running | **Generic Collector API** |
| **Celery Worker** | optiinfra-data-collector-worker | - | ✅ Running | Async task processing |
| **Celery Beat** | optiinfra-data-collector-beat | - | ✅ Running | Scheduled tasks |

### 3. Database Services (3 services)

| Service | Container Name | Port(s) | Status | Purpose |
|---------|---------------|---------|--------|---------|
| **PostgreSQL** | optiinfra-postgres | 5432 | ✅ Healthy | Relational database |
| **ClickHouse** | optiinfra-clickhouse | 8123, 9000 | ✅ Healthy | Time-series metrics |
| **Redis** | optiinfra-redis | 6379 | ✅ Healthy | Cache & message broker |

### 4. Monitoring Services (3 services)

| Service | Container Name | Port(s) | Status | Purpose |
|---------|---------------|---------|--------|---------|
| **Prometheus** | optiinfra-prometheus | 9090 | ✅ Running | Metrics collection |
| **Grafana** | optiinfra-grafana | 3000 | ✅ Running | Visualization |
| **Flower** | optiinfra-flower | 5555 | ✅ Running | Celery monitoring |

### 5. Exporters (3 services)

| Service | Container Name | Port(s) | Status | Purpose |
|---------|---------------|---------|--------|---------|
| **Postgres Exporter** | optiinfra-postgres-exporter | 9187 | ✅ Running | PostgreSQL metrics |
| **Redis Exporter** | optiinfra-redis-exporter | 9121 | ✅ Running | Redis metrics |
| **ClickHouse Exporter** | optiinfra-clickhouse-exporter | 9116 | ✅ Running | ClickHouse metrics |

---

## Port Allocation Summary

### Application Ports (8000-8099)
- **8001** - Cost Agent
- **8002** - Performance Agent
- **8003** - Resource Agent
- **8004** - Application Agent
- **8005** - **Data Collector (Generic Collector API)** ⭐
- **8080** - Orchestrator

### Database Ports (5000-6999)
- **5432** - PostgreSQL
- **6333-6334** - Qdrant
- **6379** - Redis

### Monitoring Ports (3000-5999)
- **3000** - Grafana
- **3001** - Portal (mapped from 3000)
- **5555** - Flower (Celery UI)

### Metrics & Exporters (9000-9999)
- **8123** - ClickHouse HTTP
- **9000** - ClickHouse Native
- **9090** - Prometheus
- **9116** - ClickHouse Exporter
- **9121** - Redis Exporter
- **9187** - Postgres Exporter

---

## Service Dependencies

### Data Collector Dependencies
```
optiinfra-data-collector (8005)
├── PostgreSQL (5432) - Collection history
├── ClickHouse (9000) - Metrics storage
├── Redis (6379) - Task queue
└── Celery Worker - Async processing
```

### Portal Dependencies
```
optiinfra-portal (3001)
├── Orchestrator (8080) - API gateway
├── Data Collector (8005) - Collection API
└── Grafana (3000) - Embedded dashboards
```

### Monitoring Stack
```
Prometheus (9090)
├── Postgres Exporter (9187)
├── Redis Exporter (9121)
├── ClickHouse Exporter (9116)
└── Application Agents (8001-8004)
    └── Grafana (3000) - Visualization
```

---

## Health Check Endpoints

| Service | Health Check URL | Expected Response |
|---------|-----------------|-------------------|
| Data Collector | http://localhost:8005/health | `{"status":"healthy"}` |
| Cost Agent | http://localhost:8001/health | `{"status":"healthy"}` |
| Performance Agent | http://localhost:8002/health | `{"status":"healthy"}` |
| Resource Agent | http://localhost:8003/health | `{"status":"healthy"}` |
| Application Agent | http://localhost:8004/health | `{"status":"healthy"}` |
| Orchestrator | http://localhost:8080/health | `{"status":"ok"}` |
| Prometheus | http://localhost:9090/-/healthy | `Prometheus is Healthy` |
| Grafana | http://localhost:3000/api/health | `{"database":"ok"}` |
| ClickHouse | http://localhost:8123/ping | `Ok.` |
| PostgreSQL | `pg_isready -h localhost -p 5432` | `accepting connections` |
| Redis | `redis-cli -h localhost -p 6379 ping` | `PONG` |

---

## Quick Access URLs

### User Interfaces
- **Portal**: http://localhost:3001
- **Grafana**: http://localhost:3000 (admin/admin)
- **Flower (Celery)**: http://localhost:5555
- **Prometheus**: http://localhost:9090

### API Endpoints
- **Data Collector API**: http://localhost:8005
- **Orchestrator API**: http://localhost:8080
- **Cost Agent API**: http://localhost:8001
- **Performance Agent API**: http://localhost:8002
- **Resource Agent API**: http://localhost:8003
- **Application Agent API**: http://localhost:8004

### Database Connections
- **PostgreSQL**: `postgresql://optiinfra:password@localhost:5432/optiinfra`
- **ClickHouse**: `clickhouse://localhost:9000/optiinfra_metrics`
- **Redis**: `redis://localhost:6379/0`
- **Qdrant**: `http://localhost:6333`

---

## Service Resource Usage

| Service | CPU | Memory | Disk | Network |
|---------|-----|--------|------|---------|
| Data Collector | Low | ~100MB | Low | Medium |
| Portal | Low | ~150MB | Low | Low |
| PostgreSQL | Low | ~200MB | Medium | Low |
| ClickHouse | Medium | ~500MB | High | Medium |
| Redis | Low | ~50MB | Low | High |
| Prometheus | Medium | ~300MB | Medium | Medium |
| Grafana | Low | ~100MB | Low | Low |
| Agents (4) | Low | ~50MB each | Low | Low |

**Total Estimated**: ~2GB RAM, ~10GB Disk

---

## Service Startup Order

1. **Infrastructure** (Databases)
   - PostgreSQL
   - ClickHouse
   - Redis
   - Qdrant

2. **Monitoring** (Observability)
   - Prometheus
   - Exporters (3)
   - Grafana

3. **Core Services** (Application)
   - Orchestrator
   - Data Collector
   - Celery Worker & Beat

4. **Agents** (Data Collection)
   - Cost Agent
   - Performance Agent
   - Resource Agent
   - Application Agent

5. **Frontend** (User Interface)
   - Portal

---

## Network Configuration

All services run on Docker network: `optiinfra_default`

### Internal Communication
- Services communicate using container names
- Example: `data-collector` → `clickhouse:9000`

### External Access
- Only exposed ports are accessible from host
- Internal ports (e.g., Celery) not exposed

---

## Scaling Recommendations

### Horizontal Scaling
- **Celery Workers**: Add more workers for parallel processing
- **Data Collector**: Can run multiple instances behind load balancer
- **Agents**: Can run multiple instances per provider

### Vertical Scaling
- **ClickHouse**: Increase memory for larger datasets
- **PostgreSQL**: Increase connections for more concurrent users
- **Redis**: Increase memory for larger queues

---

## Security Notes

### Exposed Services
- All services exposed on `0.0.0.0` (all interfaces)
- **Production**: Use firewall rules to restrict access
- **Recommendation**: Use reverse proxy (nginx/traefik)

### Credentials
- Default credentials used (development only)
- **Production**: Change all default passwords
- **Recommendation**: Use secrets management (Vault, AWS Secrets Manager)

### Network
- All services on same Docker network
- **Production**: Separate networks for different tiers
- **Recommendation**: Use network policies
