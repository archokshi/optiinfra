# Cost Agent Operations Guide

**Version**: 1.0.0  
**Last Updated**: 2025-01-23

---

## Table of Contents

- [Service Management](#service-management)
- [Health Monitoring](#health-monitoring)
- [Performance Tuning](#performance-tuning)
- [Backup and Recovery](#backup-and-recovery)
- [Scaling](#scaling)
- [Incident Response](#incident-response)
- [Maintenance](#maintenance)

---

## Service Management

### Starting the Service

**Local Development**:
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8001
```

**Docker**:
```bash
docker start cost-agent
docker-compose up -d cost-agent
```

**Kubernetes**:
```bash
kubectl scale deployment cost-agent --replicas=3 -n optiinfra
```

### Stopping the Service

```bash
# Graceful shutdown
kill -TERM <pid>

# Docker
docker stop cost-agent

# Kubernetes
kubectl scale deployment cost-agent --replicas=0 -n optiinfra
```

---

## Health Monitoring

### Health Check Endpoints

```bash
# Basic health
curl http://localhost:8001/api/v1/health

# Detailed health
curl http://localhost:8001/api/v1/health/detailed
```

### Key Health Indicators

1. **API Responsiveness**: < 100ms
2. **Database Connectivity**: < 50ms latency
3. **Cache Connectivity**: < 10ms latency
4. **Memory Usage**: < 80% of limit
5. **CPU Usage**: < 70% average

---

## Performance Tuning

### Database Optimization

```python
# Connection pool settings
DB_POOL_SIZE = 20
DB_MAX_OVERFLOW = 10
DB_POOL_TIMEOUT = 30
```

### Cache Configuration

```bash
# Redis settings
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

---

## Backup and Recovery

### Database Backup

```bash
# Automated backup
pg_dump cost_agent > backup_$(date +%Y%m%d).sql
gzip backup_$(date +%Y%m%d).sql
aws s3 cp backup_$(date +%Y%m%d).sql.gz s3://optiinfra-backups/
```

### Database Restore

```bash
# Restore from backup
aws s3 cp s3://optiinfra-backups/backup_20250123.sql.gz .
gunzip backup_20250123.sql.gz
psql cost_agent < backup_20250123.sql
```

---

## Scaling

### Horizontal Scaling

```bash
# Kubernetes manual scaling
kubectl scale deployment cost-agent --replicas=5 -n optiinfra

# Auto-scaling
kubectl autoscale deployment cost-agent \
  --min=3 --max=10 --cpu-percent=70 -n optiinfra
```

---

## Incident Response

### Incident Classification

| Severity | Description | Response Time |
|----------|-------------|---------------|
| P0 | Service down | Immediate |
| P1 | Major degradation | < 15 minutes |
| P2 | Minor issues | < 1 hour |
| P3 | Low impact | < 4 hours |

### Response Procedures

1. **Verify Issue**: Check health endpoints
2. **Check Logs**: Review application logs
3. **Check Dependencies**: Database, Redis, APIs
4. **Apply Fix**: Restart, scale, or rollback
5. **Monitor Recovery**: Verify metrics return to normal

---

## Maintenance

### Routine Maintenance

**Daily**:
- Monitor health dashboards
- Review error logs
- Check disk space

**Weekly**:
- Review performance metrics
- Check for security updates
- Analyze cost trends

**Monthly**:
- Database maintenance (VACUUM, ANALYZE)
- Update dependencies
- Capacity planning

---

**Last Updated**: 2025-01-23  
**Version**: 1.0.0
