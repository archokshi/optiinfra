# OptiInfra Port Mapping Reference

**Date:** October 30, 2025  
**Status:** Production - 20 Services Running  
**Environment:** OptiInfra Platform + Vultr Demo Application

---

## 📊 **Table 1: OptiInfra Platform Services (20 Services)**

| # | Layer | Service | Port(s) | Container Name | Purpose | Status |
|---|-------|---------|---------|----------------|---------|--------|
| 1 | **Collection** | Data Collector API | 8005 | optiinfra-collector | Unified metrics collection API | ✅ Running |
| 2 | **Collection** | Data Collector Worker 1 | - | optiinfra-data-collector-beat | Celery beat scheduler | ✅ Running |
| 3 | **Collection** | Data Collector Worker 2 | - | optiinfra-data-collector (worker) | Celery worker for tasks | ✅ Running |
| 4 | **Storage** | PostgreSQL | 5432 | optiinfra-postgres | Primary transactional database | ✅ Running |
| 5 | **Storage** | ClickHouse | 8123, 9000 | optiinfra-clickhouse | Time-series metrics storage | ✅ Running |
| 6 | **Storage** | ClickHouse Exporter | 9116 | optiinfra-clickhouse-exporter | ClickHouse metrics for Prometheus | ✅ Running |
| 7 | **Storage** | Qdrant | 6333, 6334 | optiinfra-qdrant | Vector database for AI learning | ✅ Running |
| 8 | **Storage** | Redis | 6379 | optiinfra-redis | Cache & Pub/Sub | ✅ Running |
| 9 | **Storage** | Redis Exporter | 9121 | optiinfra-redis-exporter | Redis metrics for Prometheus | ✅ Running |
| 10 | **Orchestration** | Orchestrator | 8080 | optiinfra-orchestrator | Multi-agent coordination | ✅ Running |
| 11 | **Agent** | Cost Agent | 8001 | optiinfra-cost-agent | Cost optimization AI | ✅ Running |
| 12 | **Agent** | Performance Agent | 8002 | optiinfra-performance-agent | Performance tuning AI | ✅ Running |
| 13 | **Agent** | Resource Agent | 8003 | optiinfra-resource-agent | Resource optimization AI | ✅ Running |
| 14 | **Agent** | Application Agent | 8004 | optiinfra-application-agent | Quality monitoring AI | ✅ Running |
| 15 | **Monitoring** | Prometheus | 9090 | optiinfra-prometheus | Metrics collection & storage | ✅ Running |
| 16 | **Monitoring** | Grafana | 3000 | optiinfra-grafana | Metrics visualization dashboards | ✅ Running |
| 17 | **Monitoring** | Postgres Exporter | 9187 | optiinfra-postgres-exporter | PostgreSQL metrics for Prometheus | ✅ Running |
| 18 | **Portal** | Portal (Next.js) | 3001 | optiinfra-portal | Customer web interface | ✅ Running |
| 19 | **Workflow** | Flower (Celery Monitor) | 5555 | optiinfra-flower | Celery task monitoring UI | ✅ Running |
| 20 | **Network** | OptiInfra Network | - | optiinfra | Docker network for all services | ✅ Running |

**Total Services:** 20 containers  
**Ports Used:** 3000, 3001, 5432, 5555, 6333, 6334, 6379, 8001, 8002, 8003, 8004, 8005, 8080, 8123, 9000, 9090, 9116, 9121, 9187

---

## 🎯 **Table 2: Vultr Demo Application (Customer LLM Infrastructure Simulation)**

| # | Service | Internal Port | External Port | Container Name | Purpose | Technology |
|---|---------|---------------|---------------|----------------|---------|------------|
| 1 | **vLLM Server** | 8000 | **8100** | vllm-server | Mistral-7B inference engine | vLLM + NVIDIA GPU |
| 2 | **Chat API** | 8080 | **8200** | chat-api | REST API with Prometheus metrics | FastAPI + Python 3.11 |
| 3 | **Prometheus** | 9090 | **9091** | prometheus-demo | Metrics collection & visualization | Prometheus |
| 4 | **DCGM Exporter** | 9400 | **9401** | dcgm-exporter | GPU metrics (utilization, memory, power) | NVIDIA DCGM |
| 5 | **Locust** | 8089 | **8090** | locust | Load testing & traffic generation | Locust + Python |

**Total Services:** 5 containers  
**Ports Used:** 8100, 8200, 9091, 9401, 8090

---

## 🔗 **Table 3: Complete Port Mapping**

| Port | Service | Environment | Access URL | Notes |
|------|---------|-------------|------------|-------|
| **3000** | Grafana | OptiInfra | http://localhost:3000 | Metrics dashboards |
| **3001** | Next.js Portal | OptiInfra | http://localhost:3001 | Customer UI |
| **5432** | PostgreSQL | OptiInfra | postgresql://localhost:5432 | Primary DB |
| **5555** | Flower | OptiInfra | http://localhost:5555 | Celery monitoring |
| **6333** | Qdrant HTTP | OptiInfra | http://localhost:6333 | Vector DB API |
| **6334** | Qdrant gRPC | OptiInfra | grpc://localhost:6334 | Vector DB gRPC |
| **6379** | Redis | OptiInfra | redis://localhost:6379 | Cache/Pub-Sub |
| **8001** | Cost Agent | OptiInfra | http://localhost:8001 | Cost optimization |
| **8002** | Performance Agent | OptiInfra | http://localhost:8002 | Performance tuning |
| **8003** | Resource Agent | OptiInfra | http://localhost:8003 | Resource optimization |
| **8004** | Application Agent | OptiInfra | http://localhost:8004 | Quality monitoring |
| **8005** | Data Collector | OptiInfra | http://localhost:8005 | Metrics collection |
| **8080** | Orchestrator | OptiInfra | http://localhost:8080 | Agent coordination |
| **8123** | ClickHouse HTTP | OptiInfra | http://localhost:8123 | Time-series DB |
| **9000** | ClickHouse Native | OptiInfra | clickhouse://localhost:9000 | Time-series DB |
| **9090** | Prometheus | OptiInfra | http://localhost:9090 | Metrics storage |
| **9116** | ClickHouse Exporter | OptiInfra | http://localhost:9116 | CH metrics |
| **9121** | Redis Exporter | OptiInfra | http://localhost:9121 | Redis metrics |
| **9187** | Postgres Exporter | OptiInfra | http://localhost:9187 | PG metrics |
| - | - | - | - | - |
| **8100** | vLLM | Vultr Demo | http://VULTR_IP:8100 | Mistral-7B inference |
| **8200** | Chat API | Vultr Demo | http://VULTR_IP:8200 | Chat endpoint |
| **8090** | Locust | Vultr Demo | http://VULTR_IP:8090 | Load generator |
| **9091** | Prometheus | Vultr Demo | http://VULTR_IP:9091 | Demo metrics |
| **9401** | DCGM Exporter | Vultr Demo | http://VULTR_IP:9401 | GPU metrics |

---

## ✅ **Port Conflict Check**

| Port Range | OptiInfra | Vultr Demo | Status |
|------------|-----------|------------|--------|
| 3000-3001 | Grafana, Portal | - | ✅ No conflict |
| 5432 | PostgreSQL | - | ✅ No conflict |
| 5555 | Flower | - | ✅ No conflict |
| 6333-6334 | Qdrant | - | ✅ No conflict |
| 6379 | Redis | - | ✅ No conflict |
| 8001-8005 | Agents + Collector | - | ✅ No conflict |
| 8080 | Orchestrator | - | ✅ No conflict |
| 8090 | - | Locust | ✅ No conflict |
| 8100 | - | vLLM | ✅ No conflict |
| 8123 | ClickHouse | - | ✅ No conflict |
| 8200 | - | Chat API | ✅ No conflict |
| 9000 | ClickHouse | - | ✅ No conflict |
| 9090 | Prometheus | - | ✅ No conflict |
| 9091 | - | Prometheus Demo | ✅ No conflict |
| 9116 | CH Exporter | - | ✅ No conflict |
| 9121 | Redis Exporter | - | ✅ No conflict |
| 9187 | PG Exporter | - | ✅ No conflict |
| 9401 | - | DCGM | ✅ No conflict |

**Result:** ✅ **ZERO PORT CONFLICTS** - Both environments can run simultaneously!

---

## 📈 **Summary Statistics**

### **OptiInfra Platform:**
- **Total Containers:** 20
- **Unique Ports:** 19 ports
- **Layers:** 6 (Collection, Storage, Orchestration, Agent, Monitoring, Portal)
- **Exporters:** 3 (ClickHouse, Redis, PostgreSQL)
- **Monitoring:** Prometheus + Grafana + Flower

### **Vultr Demo App:**
- **Total Containers:** 5
- **Unique Ports:** 5 ports
- **GPU Required:** Yes
- **Model:** Mistral-7B-Instruct-v0.3

### **Combined:**
- **Total Containers:** 25
- **Total Unique Ports:** 24 ports
- **Port Conflicts:** 0 ✅

---

## 🚀 **Quick Access URLs**

### **OptiInfra Platform (Local/Production)**

**Core Services:**
```bash
http://localhost:8080  # Orchestrator (Agent coordination)
http://localhost:8005  # Data Collector (Metrics collection)
```

**AI Agents:**
```bash
http://localhost:8001  # Cost Agent
http://localhost:8002  # Performance Agent
http://localhost:8003  # Resource Agent
http://localhost:8004  # Application Agent
```

**Storage:**
```bash
postgresql://localhost:5432       # PostgreSQL
http://localhost:8123             # ClickHouse HTTP
clickhouse://localhost:9000       # ClickHouse Native
http://localhost:6333             # Qdrant HTTP
redis://localhost:6379            # Redis
```

**Monitoring & Dashboards:**
```bash
http://localhost:9090  # Prometheus (Metrics)
http://localhost:3000  # Grafana (Dashboards)
http://localhost:3001  # Portal (Customer UI)
http://localhost:5555  # Flower (Celery Monitor)
```

**Exporters:**
```bash
http://localhost:9116  # ClickHouse Exporter
http://localhost:9121  # Redis Exporter
http://localhost:9187  # PostgreSQL Exporter
```

---

### **Vultr Demo App (Remote)**

Replace `YOUR_VULTR_IP` with your actual Vultr instance IP:

```bash
http://YOUR_VULTR_IP:8100  # vLLM (Mistral-7B Inference)
http://YOUR_VULTR_IP:8200  # Chat API (REST endpoint)
http://YOUR_VULTR_IP:9091  # Prometheus (Demo metrics)
http://YOUR_VULTR_IP:9401  # DCGM (GPU metrics)
http://YOUR_VULTR_IP:8090  # Locust (Load generator UI)
```

---

## 🔧 **Port Usage by Layer**

### **Collection Layer (3 services)**
- 8005 - Data Collector API

### **Storage Layer (6 services)**
- 5432 - PostgreSQL
- 8123, 9000 - ClickHouse
- 6333, 6334 - Qdrant
- 6379 - Redis
- 9116 - ClickHouse Exporter
- 9121 - Redis Exporter

### **Orchestration Layer (1 service)**
- 8080 - Orchestrator

### **Agent Layer (4 services)**
- 8001 - Cost Agent
- 8002 - Performance Agent
- 8003 - Resource Agent
- 8004 - Application Agent

### **Monitoring Layer (4 services)**
- 9090 - Prometheus
- 3000 - Grafana
- 9187 - PostgreSQL Exporter
- 5555 - Flower

### **Portal Layer (1 service)**
- 3001 - Next.js Portal

### **Vultr Demo Layer (5 services)**
- 8100 - vLLM
- 8200 - Chat API
- 9091 - Prometheus Demo
- 9401 - DCGM Exporter
- 8090 - Locust

---

## 🎯 **Data Flow Between Services**

### **Collection Flow:**
```
Vultr Instance (Customer LLM)
    ↓ Port 8100, 8200, 9091, 9401
Data Collector (Port 8005)
    ↓ Port 9000
ClickHouse (Time-series storage)
    ↓ Port 9000
Agents (Read metrics)
    ↓ Port 5432
PostgreSQL (Store recommendations)
```

### **Monitoring Flow:**
```
All Services (Exporters)
    ↓ Ports 9116, 9121, 9187
Prometheus (Port 9090)
    ↓ Port 9090
Grafana (Port 3000)
    ↓ Display
Customer Dashboard
```

### **Agent Coordination Flow:**
```
Customer Request
    ↓ Port 3001
Portal (Next.js)
    ↓ Port 8080
Orchestrator
    ↓ Ports 8001-8004
Agents (AI processing)
    ↓ Groq API (HTTPS)
LLM Analysis
    ↓ Port 5432
PostgreSQL (Store results)
```

---

## 🛡️ **Security Notes**

### **Public Ports (Exposed to Internet):**
- **Vultr Demo:** 8100, 8200, 8090, 9091, 9401
- **OptiInfra:** None (all localhost only)

### **Internal Ports (Localhost only):**
- All OptiInfra services (3000, 3001, 5432, 5555, 6333, 6334, 6379, 8001-8005, 8080, 8123, 9000, 9090, 9116, 9121, 9187)

### **Firewall Rules Required (Vultr):**
```bash
# Allow Vultr demo ports
ufw allow 8100/tcp  # vLLM
ufw allow 8200/tcp  # Chat API
ufw allow 8090/tcp  # Locust
ufw allow 9091/tcp  # Prometheus
ufw allow 9401/tcp  # DCGM
```

---

## 📝 **Maintenance Commands**

### **Check All Ports:**
```bash
# OptiInfra
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"

# Vultr Demo
ssh root@VULTR_IP "docker ps --format 'table {{.Names}}\t{{.Ports}}\t{{.Status}}'"
```

### **Test Port Connectivity:**
```bash
# OptiInfra (local)
curl http://localhost:8080/health  # Orchestrator
curl http://localhost:8005/health  # Data Collector
curl http://localhost:9090/-/healthy  # Prometheus

# Vultr Demo (remote)
curl http://VULTR_IP:8200/health  # Chat API
curl http://VULTR_IP:8100/health  # vLLM
```

### **View Port Usage:**
```bash
# Windows
netstat -ano | findstr "8001 8002 8003 8004 8005 8080"

# Linux
netstat -tulpn | grep -E "8001|8002|8003|8004|8005|8080"
```

---

## 🔄 **Version History**

| Date | Version | Changes |
|------|---------|---------|
| 2025-10-30 | 1.0 | Initial port mapping documentation |
| - | - | 20 OptiInfra services + 5 Vultr demo services |
| - | - | Zero port conflicts confirmed |

---

## 📞 **Support**

If you encounter port conflicts:

1. **Check running services:**
   ```bash
   docker ps
   ```

2. **Check port usage:**
   ```bash
   netstat -ano | findstr "PORT_NUMBER"
   ```

3. **Stop conflicting service:**
   ```bash
   docker stop CONTAINER_NAME
   ```

4. **Restart OptiInfra:**
   ```bash
   docker-compose restart
   ```

---

**Document Status:** ✅ Current and Accurate  
**Last Verified:** October 30, 2025  
**Total Services:** 25 (20 OptiInfra + 5 Vultr Demo)  
**Port Conflicts:** 0
