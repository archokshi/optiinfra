"""
Qdrant vector database package.

Provides vector storage and semantic search for:
- Cost optimization knowledge (past decisions → outcomes)
- Performance patterns (successful optimizations)
- Customer context (preferences, constraints)

Usage:
    from shared.qdrant import get_qdrant_client
    
    client = get_qdrant_client()
    client.initialize_collections()
    
    # Store decision
    client.store_cost_decision(...)
    
    # Search for similar
    results = client.search_similar_cost_decisions(...)
"""

from shared.qdrant.client import (
    QdrantVectorClient,
    get_qdrant_client
)

from shared.qdrant.schemas.collections import (
    COST_OPTIMIZATION_KNOWLEDGE,
    PERFORMANCE_PATTERNS,
    CUSTOMER_CONTEXT,
    ALL_COLLECTIONS,
    get_collection_config
)

__all__ = [
    'QdrantVectorClient',
    'get_qdrant_client',
    'COST_OPTIMIZATION_KNOWLEDGE',
    'PERFORMANCE_PATTERNS',
    'CUSTOMER_CONTEXT',
    'ALL_COLLECTIONS',
    'get_collection_config'
]
