# OptiInfra Monitoring Stack

Complete Prometheus and Grafana monitoring setup for the OptiInfra multi-agent system.

## 🎯 Overview

This monitoring stack provides:
- **Prometheus** - Metrics collection and storage
- **Grafana** - Visualization and dashboards
- **Database Exporters** - PostgreSQL, ClickHouse, Redis metrics
- **Custom Metrics** - Agent-specific and orchestrator metrics
- **Alerting** - Automated alerts for critical conditions

## 📊 Components

### Prometheus (Port 9090)
- Scrapes metrics from all services every 15 seconds
- Stores time-series data
- Evaluates alert rules
- Provides PromQL query interface

### Grafana (Port 3000)
- 7 pre-built dashboards
- Real-time metric visualization
- Alert management
- Data exploration

### Exporters
- **postgres-exporter** (9187) - PostgreSQL metrics
- **clickhouse-exporter** (9116) - ClickHouse metrics
- **redis-exporter** (9121) - Redis metrics

## 🚀 Quick Start

### 1. Start Monitoring Stack

```bash
cd ~/optiinfra
docker-compose up -d prometheus grafana postgres-exporter clickhouse-exporter redis-exporter
```

### 2. Verify Services

```bash
# Check Prometheus
curl http://localhost:9090/-/healthy
# Expected: Prometheus is Healthy.

# Check Grafana
curl http://localhost:3000/api/health
# Expected: {"database":"ok"}

# Check targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```

### 3. Access Dashboards

- **Prometheus UI**: http://localhost:9090
- **Grafana UI**: http://localhost:3000
  - Username: `admin`
  - Password: `optiinfra_admin`

## 📈 Dashboards

### 1. System Overview
Single-pane view of entire OptiInfra system:
- Total cost savings
- Active optimizations
- Service health status
- Request rates and error rates

### 2. Cost Agent
Deep dive into cost optimization:
- Total savings by provider
- Spot migration success rate
- Reserved instance coverage
- Right-sizing opportunities

### 3. Performance Agent
Performance optimization metrics:
- Latency improvements
- Throughput (QPS)
- KV cache hit rate
- Quantization speedup

### 4. Resource Agent
Resource utilization and scaling:
- GPU utilization by ID
- Scaling events
- CPU/Memory usage
- Resource costs

### 5. Application Agent
Quality monitoring:
- Quality scores
- Regression detections
- A/B test results
- Auto-rollback events

### 6. Infrastructure
Database and system health:
- PostgreSQL connections
- ClickHouse query rate
- Redis memory usage
- Container metrics

### 7. Alerts
Alert monitoring:
- Active alerts
- Alert history
- Most frequent alerts

## 🔍 Sample Queries

### Service Health
```promql
# All services status
up{job=~"orchestrator|.*-agent"}

# Services down
up{job=~"orchestrator|.*-agent"} == 0
```

### Performance
```promql
# P95 latency
histogram_quantile(0.95, rate(request_duration_seconds_bucket[5m]))

# Request rate (QPS)
sum(rate(requests_total[1m])) by (service)

# Error rate
sum(rate(errors_total[5m])) / sum(rate(requests_total[5m])) * 100
```

### Cost Savings
```promql
# Total savings (24h)
increase(cost_savings_total[24h])

# Savings rate (per hour)
rate(cost_savings_total[5m]) * 3600
```

### Resource Utilization
```promql
# Average GPU utilization
avg(gpu_utilization) by (gpu_id)

# Memory usage (GB)
sum(process_resident_memory_bytes) by (service) / 1024 / 1024 / 1024
```

## 🔔 Alerts

### Configured Alert Rules

1. **ServiceDown** - Service unavailable for >1 minute
2. **HighErrorRate** - Error rate >5% for 5 minutes
3. **HighLatency** - P95 latency >1 second
4. **HighDatabaseConnectionUsage** - Connection pool >90%
5. **AgentExecutionFailures** - >3 failures in 5 minutes
6. **CostAnomaly** - Cost change >20%
7. **QualityRegression** - Quality score <0.95
8. **HighGPUUtilization** - GPU >95% for 10 minutes
9. **HighMemoryUsage** - Memory >90%

### Alert Channels

Configure in Grafana:
- Slack: `#optiinfra-alerts`
- Email: `team@optiinfra.com`
- PagerDuty: (for production)

## 🛠️ Metrics Endpoints

All services expose metrics on `/metrics`:

```bash
# Orchestrator
curl http://localhost:8080/metrics

# Cost Agent
curl http://localhost:8001/metrics

# Performance Agent
curl http://localhost:8002/metrics

# Resource Agent
curl http://localhost:8003/metrics

# Application Agent
curl http://localhost:8004/metrics
```

## 📊 Custom Metrics

### Orchestrator (Go)
```go
import "github.com/prometheus/client_golang/prometheus"

// Example: Record agent request
metrics.RecordAgentRequest("cost-agent", "success", duration)

// Example: Update active optimizations
metrics.UpdateActiveOptimizations(5)
```

### Python Agents
```python
from shared.utils.prometheus_metrics import BaseMetrics

# Initialize metrics
metrics = BaseMetrics('cost-agent')

# Track request
metrics.track_request('/analyze', 'POST', 200, 0.5)

# Track LLM call
metrics.track_llm_call('openai', 'gpt-4', 1000, 500, 0.05)

# Track optimization
metrics.track_optimization('spot-migration', 'success', 0.95)
```

## 🧪 Testing

### Test Prometheus Scraping
```bash
# Check all targets are up
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health != "up")'
# Should return empty if all healthy

# Query a metric
curl 'http://localhost:9090/api/v1/query?query=up' | jq '.data.result'
```

### Test Grafana Dashboards
```bash
# List all dashboards
curl -u admin:optiinfra_admin http://localhost:3000/api/search | jq '.[].title'

# Test data source
curl -u admin:optiinfra_admin http://localhost:3000/api/datasources/proxy/1/api/v1/query?query=up
```

### Generate Test Metrics
```bash
# Trigger some requests
for i in {1..10}; do
  curl -X POST http://localhost:8001/api/v1/health
  curl -X POST http://localhost:8002/api/v1/health
  sleep 1
done

# Check metrics updated
curl http://localhost:8001/metrics | grep requests_total
```

## 🐛 Troubleshooting

### Prometheus Not Scraping
```bash
# Check Prometheus logs
docker logs optiinfra-prometheus

# Verify service is reachable
docker exec optiinfra-prometheus wget -O- http://cost-agent:8001/metrics

# Check Prometheus config
docker exec optiinfra-prometheus promtool check config /etc/prometheus/prometheus.yml
```

### Grafana Dashboards Not Loading
```bash
# Check Grafana logs
docker logs optiinfra-grafana

# Verify provisioning
docker exec optiinfra-grafana ls -la /etc/grafana/provisioning/dashboards/

# Restart Grafana
docker restart optiinfra-grafana
```

### Metrics Not Updating
```bash
# Check if service is exposing metrics
curl http://localhost:8001/metrics

# Check Prometheus is scraping
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job == "cost-agent")'

# Check for errors in service logs
docker logs optiinfra-cost-agent
```

## 📚 Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Cheat Sheet](https://promlabs.com/promql-cheat-sheet/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)

## 🔄 Maintenance

### Backup Dashboards
```bash
# Export all dashboards
cd monitoring/grafana/dashboards
for dash in $(curl -s -u admin:optiinfra_admin http://localhost:3000/api/search | jq -r '.[].uid'); do
  curl -s -u admin:optiinfra_admin \
    http://localhost:3000/api/dashboards/uid/$dash | \
    jq '.dashboard' > backup-$dash.json
done
```

### Update Alert Rules
```bash
# Edit alerts
vim monitoring/prometheus/alerts.yml

# Validate syntax
promtool check rules monitoring/prometheus/alerts.yml

# Reload Prometheus
curl -X POST http://localhost:9090/-/reload
```

### Clean Up Old Data
```bash
# Prometheus retains data for 15 days by default
# To change retention:
# Add to docker-compose.yml:
#   command:
#     - '--storage.tsdb.retention.time=30d'
```

## 🎯 Next Steps

1. **Customize Dashboards** - Adjust panels for your needs
2. **Configure Alerts** - Set up Slack/PagerDuty notifications
3. **Add Custom Metrics** - Track business-specific KPIs
4. **Set Up Recording Rules** - Pre-compute expensive queries
5. **Enable Remote Storage** - For long-term metrics retention

---

**Version:** 1.0  
**Last Updated:** October 21, 2025  
**Maintainer:** OptiInfra Team
