# Qdrant Vector Database

Vector storage and semantic search for OptiInfra agent memory and learning.

## Overview

Qdrant enables agents to:
- **Learn from past decisions** - "What worked for similar scenarios?"
- **Retrieve relevant context** - "What do we know about this customer?"
- **Semantic search** - Find similar situations, not just exact matches

## Architecture

### Collections
1. **cost_optimization_knowledge** - Past cost optimization decisions
2. **performance_patterns** - Successful performance optimizations
3. **customer_context** - Customer-specific preferences and constraints

Each collection stores:
- **Vector embeddings** (1536-dim from OpenAI ada-002)
- **Metadata payload** (structured data about the decision/pattern)
- **Cosine similarity** for semantic matching

## Usage

### Initialize Collections

```bash
# Run once to create all collections
python << 'EOF'
from shared.qdrant import get_qdrant_client

client = get_qdrant_client()
client.initialize_collections()
print("✅ Collections initialized")
EOF
```

### Python Client

```python
from shared.qdrant import get_qdrant_client

# Get client
client = get_qdrant_client()

# Check connection
if client.ping():
    print("✅ Qdrant connected!")

# Store a cost optimization decision
point_id = client.store_cost_decision(
    optimization_id="123e4567-e89b-12d3-a456-426614174000",
    customer_id="789e0123-e89b-12d3-a456-426614174000",
    optimization_type="spot_migration",
    decision_context="Migrating batch ETL workload to spot instances. Workload can handle interruptions with checkpointing.",
    outcome="success",
    savings_percent=38.5,
    cost_impact=18000,
    cloud_provider="aws",
    instance_type="m5.xlarge"
)

# Search for similar decisions
results = client.search_similar_cost_decisions(
    query="migrate batch processing to spot",
    limit=5,
    filter_outcome="success"
)

for result in results:
    print(f"Score: {result['score']:.3f}")
    print(f"Savings: {result['payload']['savings_percent']}%")
    print(f"Context: {result['payload']['decision_context']}")
```

### Performance Patterns

```python
# Store a performance optimization
point_id = client.store_performance_pattern(
    optimization_id="456e7890-e89b-12d3-a456-426614174000",
    customer_id="789e0123-e89b-12d3-a456-426614174000",
    service_type="vllm",
    model_name="llama-2-70b",
    problem_description="High P95 latency (800ms) due to inefficient KV cache settings",
    solution_description="Tuned KV cache block size from 16 to 32, enabled prefix caching",
    before_latency_p95=800.0,
    after_latency_p95=280.0,
    config_changes={"kv_cache_block_size": 32, "enable_prefix_caching": True},
    replicable=True
)

# Search for similar performance issues
results = client.search_similar_performance_patterns(
    query="high latency due to KV cache issues",
    limit=5,
    filter_service_type="vllm"
)

for result in results:
    print(f"Score: {result['score']:.3f}")
    print(f"Improvement: {result['payload']['improvement_factor']:.1f}x")
    print(f"Problem: {result['payload']['problem_description']}")
    print(f"Solution: {result['payload']['solution_description']}")
```

### Customer Context

```python
# Store customer preference
point_id = client.store_customer_context(
    customer_id="123e4567-e89b-12d3-a456-426614174000",
    context_type="preference",
    topic="rollout_strategy",
    content="Customer prefers slow, cautious rollouts with 24-hour validation periods between stages. They value stability over speed.",
    confidence=0.9,
    source="conversation with CTO on 2025-01-15",
    priority="high",
    applies_to_agents=["performance_agent", "cost_agent"]
)

# Search customer context
results = client.search_customer_context(
    customer_id="123e4567-e89b-12d3-a456-426614174000",
    query="rollout preferences and risk tolerance",
    limit=3
)

for result in results:
    print(f"Score: {result['score']:.3f}")
    print(f"Topic: {result['payload']['topic']}")
    print(f"Content: {result['payload']['content']}")
```

## Use Cases

### Cost Agent
> "I want to migrate to spot instances. What worked for similar customers?"

```python
results = client.search_similar_cost_decisions(
    query="migrate to spot instances for batch processing",
    limit=5,
    filter_outcome="success"
)

# Returns: "3 similar cases, 2 succeeded (35% savings), 1 failed (workload too variable)"
```

### Performance Agent
> "Customer has high P95 latency. What optimizations worked before?"

```python
results = client.search_similar_performance_patterns(
    query="high P95 latency optimization",
    limit=5
)

# Returns: "KV cache tuning worked in 5 similar cases (2.3x improvement)"
```

### Application Agent
> "Customer prefers slow rollouts. What's their risk tolerance?"

```python
results = client.search_customer_context(
    customer_id="customer-uuid",
    query="rollout strategy and risk tolerance",
    limit=3
)

# Returns: "Customer X prefers 10%→25%→50%→100% rollout with 24hr validation"
```

## Data Model

### Cost Optimization Knowledge
- **Vector**: Embedding of decision_context
- **Payload**: optimization_id, customer_id, optimization_type, outcome, savings_percent, cost_impact, cloud_provider, instance_type, workload_characteristics, lessons_learned

### Performance Patterns
- **Vector**: Embedding of problem_description + solution_description
- **Payload**: optimization_id, customer_id, service_type, model_name, before/after latency, improvement_factor, config_changes, replicable

### Customer Context
- **Vector**: Embedding of content
- **Payload**: customer_id, context_type, topic, content, source, confidence, priority, applies_to_agents

## Embedding Function

The default implementation uses random vectors for testing. For production, replace with actual embeddings:

### Option 1: OpenAI

```python
import openai

def embed_text(text: str) -> List[float]:
    response = openai.Embedding.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response['data'][0]['embedding']

# In client initialization:
client.embedding_function = embed_text
```

### Option 2: Sentence-Transformers

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_text(text: str) -> List[float]:
    return model.encode(text).tolist()

# In client initialization:
client.embedding_function = embed_text
```

## Monitoring

### Check Collections

```bash
# Via Python
python << 'EOF'
from shared.qdrant import get_qdrant_client

client = get_qdrant_client()
collections = client.client.get_collections()

for collection in collections.collections:
    info = client.client.get_collection(collection.name)
    print(f"{collection.name}: {info.points_count} points")
EOF
```

### Check via REST API

```bash
# List collections
curl http://localhost:6333/collections

# Get collection info
curl http://localhost:6333/collections/cost_optimization_knowledge

# Search via API
curl -X POST http://localhost:6333/collections/cost_optimization_knowledge/points/search \
  -H 'Content-Type: application/json' \
  -d '{
    "vector": [0.1, 0.2, ...],
    "limit": 5
  }'
```

## Performance

### Search Speed
- **Typical query**: <10ms for collections with <100K points
- **Large collections**: <50ms for collections with 1M+ points
- **Batch search**: Process 100+ queries/second

### Storage
- **Vector size**: 1536 floats × 4 bytes = 6KB per point
- **Payload**: ~1-2KB per point (depends on metadata)
- **Total**: ~8KB per point
- **1M points**: ~8GB storage

### Scalability
- **Single node**: Handles millions of points
- **Distributed**: Scale horizontally for billions of points
- **Sharding**: Automatic distribution across nodes

## Best Practices

1. **Batch Inserts**: Insert multiple points at once for better performance
2. **Meaningful Embeddings**: Use high-quality embedding models (OpenAI ada-002, etc.)
3. **Filter First**: Use filters to narrow search space before vector search
4. **Monitor Quality**: Track search result relevance scores
5. **Update Context**: Regularly update customer context as you learn more
6. **Version Embeddings**: Track which embedding model version was used

## Integration with Other Databases

Qdrant complements PostgreSQL and ClickHouse:

```
PostgreSQL (Structured Data)
  ↓ customer_id, optimization_id
Qdrant (Semantic Memory)
  ↓ Similar past decisions
Agent Decision
  ↓ Metrics
ClickHouse (Time-Series)
```

Use UUIDs from PostgreSQL as foreign keys in Qdrant payloads for cross-database queries.

## Troubleshooting

### Connection Issues

```python
from shared.qdrant import get_qdrant_client

client = get_qdrant_client()
if not client.ping():
    print("❌ Qdrant not responding")
    print("   Check: docker ps | grep qdrant")
else:
    print("✅ Qdrant connected")
```

### Check Logs

```bash
docker logs optiinfra-qdrant --tail 100
```

### Restart Qdrant

```bash
docker-compose restart qdrant
```

### Clear Collection

```python
from shared.qdrant import get_qdrant_client

client = get_qdrant_client()
client.client.delete_collection("cost_optimization_knowledge")
client.initialize_collections()  # Recreate empty
```

## Security

- **API Key**: Set `QDRANT_API_KEY` environment variable for authentication
- **Network**: Qdrant runs on localhost:6333 by default
- **Production**: Use TLS and proper authentication in production
- **Data Privacy**: Embeddings may contain sensitive information - encrypt at rest

## Next Steps

1. **Integrate Embeddings**: Replace random vectors with actual embedding model
2. **Add More Data**: Populate collections with historical decisions
3. **Build Agents**: Use semantic search in agent decision-making
4. **Monitor Quality**: Track search relevance and agent performance
5. **Scale**: Add more nodes as data grows
