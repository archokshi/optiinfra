# Cost Agent Configuration Reference

**Version**: 1.0.0  
**Last Updated**: 2025-01-23

---

## Environment Variables

### Core Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PORT` | int | 8001 | Server port |
| `ENVIRONMENT` | string | development | Environment name (development, staging, production) |
| `LOG_LEVEL` | string | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `AGENT_ID` | string | cost-agent-001 | Unique agent identifier |

### Database Configuration

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `DATABASE_URL` | string | Yes | PostgreSQL connection string |
| `DB_POOL_SIZE` | int | 20 | Connection pool size |
| `DB_MAX_OVERFLOW` | int | 10 | Max overflow connections |
| `DB_POOL_TIMEOUT` | int | 30 | Pool timeout in seconds |

**Example**:
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/cost_agent
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
```

### Cache Configuration

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `REDIS_URL` | string | Yes | Redis connection string |
| `CACHE_TTL` | int | 3600 | Cache TTL in seconds |
| `CACHE_MAX_SIZE` | int | 1000 | Max cache entries |

**Example**:
```bash
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600
```

### AWS Configuration

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `AWS_ACCESS_KEY_ID` | string | Yes | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | string | Yes | AWS secret key |
| `AWS_DEFAULT_REGION` | string | us-east-1 | Default AWS region |
| `AWS_SESSION_TOKEN` | string | No | Session token (for temporary credentials) |

### GCP Configuration

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `GOOGLE_APPLICATION_CREDENTIALS` | string | Yes | Path to service account JSON |
| `GCP_PROJECT_ID` | string | Yes | GCP project ID |
| `GCP_BILLING_ACCOUNT_ID` | string | No | Billing account ID |

### Azure Configuration

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `AZURE_SUBSCRIPTION_ID` | string | Yes | Azure subscription ID |
| `AZURE_CLIENT_ID` | string | Yes | Service principal client ID |
| `AZURE_CLIENT_SECRET` | string | Yes | Service principal secret |
| `AZURE_TENANT_ID` | string | Yes | Azure tenant ID |

### Vultr Configuration

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `VULTR_API_KEY` | string | Yes | Vultr API key |

### LLM Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `GROQ_API_KEY` | string | Required | Groq API key |
| `LLM_MODEL` | string | llama-3.1-70b-versatile | Model name |
| `LLM_TEMPERATURE` | float | 0.7 | Temperature (0.0-1.0) |
| `LLM_MAX_TOKENS` | int | 2000 | Max tokens per request |

### Security Configuration

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `JWT_SECRET_KEY` | string | Yes | JWT signing secret |
| `JWT_ALGORITHM` | string | HS256 | JWT algorithm |
| `JWT_EXPIRATION_MINUTES` | int | 60 | Token expiration |
| `API_KEY_SALT` | string | Yes | Salt for API key hashing |

### Workflow Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CHECKPOINT_BACKEND` | string | postgres | Checkpoint storage (postgres, redis, memory) |
| `STATE_TTL` | int | 86400 | State TTL in seconds |
| `MAX_WORKFLOW_DURATION` | int | 3600 | Max workflow duration in seconds |

---

## Configuration File

**config.yaml** (optional):
```yaml
application:
  port: 8001
  environment: production
  log_level: INFO

database:
  url: postgresql://user:password@localhost:5432/cost_agent
  pool_size: 20
  max_overflow: 10

cache:
  url: redis://localhost:6379/0
  ttl: 3600

aws:
  region: us-east-1
  
gcp:
  project_id: my-project

llm:
  provider: groq
  model: llama-3.1-70b-versatile
  temperature: 0.7

rate_limits:
  default: 100
  analysis: 50
  bulk: 10
```

---

## Security Best Practices

1. **Never commit secrets** to version control
2. **Use environment variables** for sensitive data
3. **Rotate credentials** regularly
4. **Use least privilege** for cloud IAM roles
5. **Enable encryption** at rest and in transit

---

**Last Updated**: 2025-01-23  
**Version**: 1.0.0
