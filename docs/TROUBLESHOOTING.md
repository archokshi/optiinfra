# Troubleshooting Guide

## Common Issues

### Docker Issues

#### Issue: Docker images won't pull

**Symptoms**:
```
Error response from daemon: Get https://registry-1.docker.io/v2/: dial tcp: lookup registry-1.docker.io: no such host
```

**Solutions**:
1. Check internet connection:
   ```bash
   ping google.com
   ```

2. Check Docker daemon:
   ```bash
   docker info
   ```

3. Restart Docker:
   ```bash
   # Linux
   sudo systemctl restart docker
   
   # macOS/Windows
   # Restart Docker Desktop
   ```

#### Issue: Port conflicts

**Symptoms**:
```
Error starting userland proxy: listen tcp 0.0.0.0:5432: bind: address already in use
```

**Solutions**:
1. Check what's using the port:
   ```bash
   # Linux/macOS
   lsof -i :5432
   
   # Windows
   netstat -ano | findstr :5432
   ```

2. Kill the process or change ports in `docker-compose.yml`:
   ```yaml
   ports:
     - "5433:5432"  # Use different host port
   ```

#### Issue: Services start but aren't healthy

**Symptoms**:
```
PostgreSQL... ❌ UNHEALTHY
```

**Solutions**:
1. View logs:
   ```bash
   docker-compose logs postgres
   ```

2. Wait longer (services need 30-60s to start):
   ```bash
   sleep 60 && make verify
   ```

3. Check container status:
   ```bash
   docker ps -a
   ```

4. Restart services:
   ```bash
   make restart
   ```

### Database Issues

#### Issue: PostgreSQL connection refused

**Symptoms**:
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Solutions**:
1. Verify PostgreSQL is running:
   ```bash
   docker ps | grep postgres
   ```

2. Check connection string in `.env`:
   ```bash
   DATABASE_URL=postgresql://optiinfra:optiinfra_dev_password@localhost:5432/optiinfra
   ```

3. Test connection:
   ```bash
   docker exec optiinfra-postgres psql -U optiinfra -d optiinfra -c "SELECT 1;"
   ```

#### Issue: ClickHouse query timeout

**Symptoms**:
```
clickhouse_driver.errors.NetworkError: Code: 159. Timeout exceeded
```

**Solutions**:
1. Increase timeout in client:
   ```python
   client = Client(host='localhost', send_receive_timeout=300)
   ```

2. Optimize query (add indexes, use materialized views)

3. Check ClickHouse logs:
   ```bash
   docker-compose logs clickhouse
   ```

### Agent Issues

#### Issue: Agent won't start

**Symptoms**:
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solutions**:
1. Verify dependencies installed:
   ```bash
   cd services/cost-agent
   pip install -r requirements.txt
   ```

2. Check Python version:
   ```bash
   python --version  # Should be 3.11+
   ```

3. Use virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

#### Issue: LLM API errors

**Symptoms**:
```
openai.error.AuthenticationError: Incorrect API key provided
```

**Solutions**:
1. Check API key in `.env`:
   ```bash
   OPENAI_API_KEY=sk-your-actual-key
   ```

2. Verify API key is valid:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

3. Check rate limits and quotas

### Orchestrator Issues

#### Issue: Orchestrator can't connect to agents

**Symptoms**:
```
Error: dial tcp 127.0.0.1:8001: connect: connection refused
```

**Solutions**:
1. Verify agents are running:
   ```bash
   docker ps | grep agent
   ```

2. Check agent endpoints in orchestrator config

3. Test agent health:
   ```bash
   curl http://localhost:8001/health
   ```

#### Issue: Agent registration fails

**Symptoms**:
```
Error registering agent: agent already exists
```

**Solutions**:
1. Clear Redis cache:
   ```bash
   docker exec optiinfra-redis redis-cli FLUSHDB
   ```

2. Restart orchestrator:
   ```bash
   docker-compose restart orchestrator
   ```

### Portal Issues

#### Issue: Portal won't start

**Symptoms**:
```
Error: Cannot find module 'next'
```

**Solutions**:
1. Install dependencies:
   ```bash
   cd portal
   npm install
   ```

2. Clear cache:
   ```bash
   rm -rf .next node_modules
   npm install
   ```

3. Check Node version:
   ```bash
   node --version  # Should be 18+
   ```

#### Issue: API connection errors

**Symptoms**:
```
Error: Network Error
```

**Solutions**:
1. Check API URL in `.env.local`:
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:8080
   ```

2. Verify orchestrator is running:
   ```bash
   curl http://localhost:8080/health
   ```

3. Check CORS configuration in orchestrator

### Performance Issues

#### Issue: Slow queries

**Solutions**:
1. Add database indexes
2. Use connection pooling
3. Enable query caching
4. Optimize LLM prompts
5. Use batch processing

#### Issue: High memory usage

**Solutions**:
1. Set resource limits in `docker-compose.yml`:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 2G
   ```

2. Optimize database queries
3. Clear caches regularly
4. Monitor with Prometheus

### Kubernetes Issues

#### Issue: Pods in CrashLoopBackOff

**Solutions**:
1. Check logs:
   ```bash
   kubectl logs pod-name -n optiinfra
   ```

2. Describe pod:
   ```bash
   kubectl describe pod pod-name -n optiinfra
   ```

3. Check resource limits
4. Verify secrets and configmaps

#### Issue: Service not accessible

**Solutions**:
1. Check service:
   ```bash
   kubectl get svc -n optiinfra
   ```

2. Check endpoints:
   ```bash
   kubectl get endpoints -n optiinfra
   ```

3. Test connectivity:
   ```bash
   kubectl run -it --rm debug --image=busybox --restart=Never -- wget -O- http://service-name:port/health
   ```

## Getting Help

If you're still stuck:

1. Check GitHub Issues: https://github.com/yourorg/optiinfra/issues
2. Join Discord: https://discord.gg/optiinfra
3. Email support: support@optiinfra.ai

## Debug Mode

Enable debug logging:

```bash
# In .env
LOG_LEVEL=debug
DEBUG=true
```

View detailed logs:

```bash
make logs
```
