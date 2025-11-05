# Cost Agent Troubleshooting Guide

**Version**: 1.0.0  
**Last Updated**: 2025-01-23

---

## Common Issues

### Service Won't Start

**Symptoms**: Service fails to start or crashes immediately

**Possible Causes**:
1. Missing environment variables
2. Database connection failure
3. Port already in use
4. Missing dependencies

**Solutions**:

```bash
# Check environment variables
cat .env

# Test database connection
psql $DATABASE_URL -c "SELECT 1"

# Check if port is in use
lsof -i :8001  # Linux/Mac
netstat -ano | findstr :8001  # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

---

### Database Connection Issues

**Symptoms**: "Connection refused" or "Could not connect to database"

**Solutions**:

```bash
# Verify PostgreSQL is running
pg_isready -h localhost -p 5432

# Check connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT version()"

# Check firewall rules
sudo ufw status  # Linux
```

---

### Redis Connection Issues

**Symptoms**: "Connection refused" or cache errors

**Solutions**:

```bash
# Check Redis is running
redis-cli ping

# Verify Redis URL
echo $REDIS_URL

# Check Redis logs
redis-cli INFO
```

---

### API Authentication Errors

**Symptoms**: 401 Unauthorized responses

**Solutions**:

```bash
# Verify API key format
echo $X_API_KEY

# Create new API key
curl -X POST http://localhost:8001/api/v1/auth/api-key/create \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{"customer_id": "test", "name": "Test Key"}'

# Check JWT token expiration
# Tokens expire after 60 minutes by default
```

---

### Rate Limit Exceeded

**Symptoms**: 429 Too Many Requests

**Solutions**:

```bash
# Check rate limit headers
curl -I http://localhost:8001/api/v1/health

# Wait for rate limit reset
# Check X-RateLimit-Reset header

# Increase rate limits (if authorized)
# Edit middleware/rate_limit.py
```

---

### Slow API Responses

**Symptoms**: High latency, timeouts

**Debugging Steps**:

```bash
# Check system resources
top  # CPU usage
free -h  # Memory usage
df -h  # Disk space

# Check database performance
psql $DATABASE_URL -c "
SELECT pid, query, state, wait_event
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY query_start;
"

# Check slow queries
psql $DATABASE_URL -c "
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
"

# Clear Redis cache
redis-cli FLUSHDB
```

---

### Cloud Provider API Errors

#### AWS Errors

**Error**: "AccessDenied" or "InvalidClientTokenId"

**Solutions**:
```bash
# Verify credentials
aws sts get-caller-identity

# Check IAM permissions
aws iam get-user

# Rotate credentials
aws iam create-access-key --user-name your-user
```

#### GCP Errors

**Error**: "Permission denied" or "Invalid credentials"

**Solutions**:
```bash
# Verify service account
gcloud auth list

# Check permissions
gcloud projects get-iam-policy $GCP_PROJECT_ID

# Activate service account
gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS
```

#### Azure Errors

**Error**: "AuthenticationFailed" or "InvalidAuthenticationToken"

**Solutions**:
```bash
# Login to Azure
az login

# Verify subscription
az account show

# Check service principal
az ad sp show --id $AZURE_CLIENT_ID
```

---

### LLM API Errors

**Error**: "API key invalid" or "Rate limit exceeded"

**Solutions**:

```bash
# Verify Groq API key
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY"

# Check rate limits
# Groq has rate limits per minute/day

# Use fallback without LLM
# Set LLM_ENABLED=false in .env
```

---

### Memory Issues

**Symptoms**: Out of memory errors, service crashes

**Solutions**:

```bash
# Check memory usage
docker stats cost-agent  # Docker
kubectl top pod -l app=cost-agent -n optiinfra  # Kubernetes

# Increase memory limit
# Docker: --memory=2g
# Kubernetes: resources.limits.memory: 2Gi

# Check for memory leaks
# Monitor memory over time
# Review code for unclosed connections
```

---

### High CPU Usage

**Symptoms**: Slow performance, high CPU utilization

**Solutions**:

```bash
# Profile CPU usage
py-spy top --pid <pid>

# Check for infinite loops
# Review recent code changes

# Scale horizontally
kubectl scale deployment cost-agent --replicas=5 -n optiinfra
```

---

## Debugging Techniques

### Enable Debug Logging

```bash
# Set log level to DEBUG
export LOG_LEVEL=DEBUG

# Restart service
uvicorn src.main:app --reload --log-level debug
```

### Check Application Logs

```bash
# Docker
docker logs cost-agent --tail 100 --follow

# Kubernetes
kubectl logs -l app=cost-agent -n optiinfra --tail=100 -f

# Local
tail -f logs/cost-agent.log
```

### Check Metrics

```bash
# Prometheus metrics
curl http://localhost:8001/metrics

# Health check
curl http://localhost:8001/api/v1/health/detailed
```

### Database Debugging

```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check locks
SELECT * FROM pg_locks WHERE NOT granted;
```

---

## Known Limitations

1. **LLM Rate Limits**: Groq API has rate limits (30 req/min for free tier)
2. **Cloud API Limits**: AWS/GCP/Azure have API rate limits
3. **Large Datasets**: Analysis of >100k records may be slow
4. **Concurrent Executions**: Limited to 10 concurrent executions per customer
5. **Webhook Retries**: Max 3 retry attempts for failed webhooks

---

## Getting Help

### Self-Service Resources

- **Documentation**: https://docs.optiinfra.com
- **API Reference**: https://docs.optiinfra.com/api
- **GitHub Issues**: https://github.com/optiinfra/cost-agent/issues

### Support Channels

- **Email**: support@optiinfra.com
- **Slack**: #cost-agent-support
- **On-Call**: oncall@optiinfra.com (emergencies only)

### Reporting Bugs

When reporting bugs, include:
1. Error message and stack trace
2. Steps to reproduce
3. Environment details (OS, Python version, deployment method)
4. Relevant logs
5. Request ID (from API response)

---

**Last Updated**: 2025-01-23  
**Version**: 1.0.0
