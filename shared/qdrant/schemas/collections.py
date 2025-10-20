"""
Qdrant collection schemas and configurations.

Defines the structure and settings for all vector collections
used by OptiInfra agents for memory and learning.
"""

from dataclasses import dataclass
from typing import Dict, Any
from qdrant_client.models import Distance, VectorParams


@dataclass
class CollectionConfig:
    """Configuration for a Qdrant collection."""
    
    name: str
    vector_size: int
    distance: Distance
    description: str
    payload_schema: Dict[str, str]
    
    def to_vector_params(self) -> VectorParams:
        """Convert to Qdrant VectorParams."""
        return VectorParams(
            size=self.vector_size,
            distance=self.distance
        )


# ============================================================================
# COLLECTION CONFIGURATIONS
# ============================================================================

COST_OPTIMIZATION_KNOWLEDGE = CollectionConfig(
    name="cost_optimization_knowledge",
    vector_size=1536,  # OpenAI ada-002 embedding size
    distance=Distance.COSINE,
    description="Knowledge base of past cost optimization decisions and outcomes",
    payload_schema={
        "optimization_id": "UUID - Link to optimizations table",
        "customer_id": "UUID - Which customer",
        "optimization_type": "String - spot_migration, reserved_instance, right_sizing",
        "decision_context": "String - Why this decision was made",
        "outcome": "String - success, failed, rolled_back",
        "savings_percent": "Float - Actual savings achieved (if success)",
        "cost_impact": "Float - Dollar savings per month",
        "execution_date": "DateTime - When this was executed",
        "cloud_provider": "String - aws, gcp, azure",
        "instance_type": "String - m5.xlarge, etc",
        "workload_characteristics": "String - Description of workload",
        "lessons_learned": "String - What we learned from this",
        "confidence_score": "Float - How confident we were (0-1)",
        "customer_feedback": "String - Customer's feedback (if any)"
    }
)

PERFORMANCE_PATTERNS = CollectionConfig(
    name="performance_patterns",
    vector_size=1536,
    distance=Distance.COSINE,
    description="Successful performance optimization patterns",
    payload_schema={
        "optimization_id": "UUID - Link to optimizations table",
        "customer_id": "UUID - Which customer",
        "service_type": "String - vllm, tgi, sglang",
        "model_name": "String - Which LLM model",
        "optimization_applied": "String - What was changed",
        "problem_description": "String - Original performance issue",
        "solution_description": "String - How it was solved",
        "before_latency_p95": "Float - P95 latency before (ms)",
        "after_latency_p95": "Float - P95 latency after (ms)",
        "improvement_factor": "Float - How much faster (2.3x, etc)",
        "config_changes": "JSONB - Specific configuration changes",
        "side_effects": "String - Any negative impacts observed",
        "execution_date": "DateTime - When applied",
        "stability_score": "Float - How stable post-change (0-1)",
        "replicable": "Boolean - Can this be repeated for similar cases"
    }
)

CUSTOMER_CONTEXT = CollectionConfig(
    name="customer_context",
    vector_size=1536,
    distance=Distance.COSINE,
    description="Customer-specific context, preferences, and constraints",
    payload_schema={
        "customer_id": "UUID - Which customer",
        "context_type": "String - preference, constraint, historical_note",
        "topic": "String - What this context is about",
        "content": "String - The actual context/note",
        "source": "String - How we learned this (conversation, observation, explicit)",
        "confidence": "Float - How confident we are (0-1)",
        "created_at": "DateTime - When this context was added",
        "updated_at": "DateTime - Last update",
        "priority": "String - low, medium, high, critical",
        "applies_to_agents": "List[String] - Which agents should use this",
        "examples": "String - Example scenarios where this applies",
        "exceptions": "String - When this doesn't apply"
    }
)


# ============================================================================
# COLLECTION REGISTRY
# ============================================================================

ALL_COLLECTIONS = [
    COST_OPTIMIZATION_KNOWLEDGE,
    PERFORMANCE_PATTERNS,
    CUSTOMER_CONTEXT
]


def get_collection_config(collection_name: str) -> CollectionConfig:
    """
    Get configuration for a specific collection.
    
    Args:
        collection_name: Name of the collection
    
    Returns:
        CollectionConfig for the requested collection
    
    Raises:
        ValueError: If collection not found
    """
    for config in ALL_COLLECTIONS:
        if config.name == collection_name:
            return config
    
    raise ValueError(f"Unknown collection: {collection_name}")
