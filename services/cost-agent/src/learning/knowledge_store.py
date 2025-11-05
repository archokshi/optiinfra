"""
Knowledge Store.

Stores and retrieves learning data using Qdrant vector database.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from openai import OpenAI

from src.models.learning_loop import (
    OutcomeRecord,
    SimilarCase
)

logger = logging.getLogger(__name__)


class KnowledgeStore:
    """Stores and retrieves learning data using Qdrant."""
    
    COLLECTION_NAME = "recommendation_outcomes"
    EMBEDDING_SIZE = 1536  # OpenAI text-embedding-3-small
    
    def __init__(self, qdrant_url: str = "http://localhost:6333", openai_api_key: str = None):
        """
        Initialize knowledge store.
        
        Args:
            qdrant_url: Qdrant server URL
            openai_api_key: OpenAI API key for embeddings
        """
        self.qdrant_client = QdrantClient(url=qdrant_url)
        self.openai_api_key = openai_api_key
        self.openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None
    
    async def initialize_collections(self):
        """Initialize Qdrant collections."""
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.COLLECTION_NAME not in collection_names:
                logger.info(f"Creating collection: {self.COLLECTION_NAME}")
                
                # Create collection
                self.qdrant_client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=self.EMBEDDING_SIZE,
                        distance=Distance.COSINE
                    )
                )
                
                logger.info(f"Collection created: {self.COLLECTION_NAME}")
            else:
                logger.info(f"Collection already exists: {self.COLLECTION_NAME}")
            
        except Exception as e:
            logger.error(f"Error initializing collections: {e}", exc_info=True)
            raise
    
    async def check_health(self) -> bool:
        """
        Check Qdrant health.
        
        Returns:
            True if healthy
        """
        try:
            collections = self.qdrant_client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False
    
    async def store_recommendation_outcome(
        self,
        recommendation: Dict[str, Any],
        outcome: Dict[str, Any],
        embedding: Optional[List[float]] = None
    ) -> str:
        """
        Store recommendation outcome in Qdrant.
        
        Args:
            recommendation: Recommendation data
            outcome: Outcome data
            embedding: Pre-computed embedding (optional)
        
        Returns:
            Vector ID
        """
        try:
            logger.info(f"Storing outcome for recommendation {recommendation.get('recommendation_id')}")
            
            # Generate embedding if not provided
            if embedding is None:
                embedding = await self._generate_embedding(recommendation)
            
            # Generate vector ID
            vector_id = str(uuid.uuid4())
            
            # Prepare payload
            payload = {
                "recommendation_id": recommendation.get("recommendation_id"),
                "recommendation_type": recommendation.get("recommendation_type"),
                "resource_type": recommendation.get("resource_type"),
                "resource_id": recommendation.get("resource_id"),
                "region": recommendation.get("region"),
                "success": outcome.get("success", False),
                "actual_savings": outcome.get("actual_savings", 0.0),
                "predicted_savings": outcome.get("predicted_savings", 0.0),
                "savings_accuracy": outcome.get("savings_accuracy", 0.0),
                "execution_date": outcome.get("timestamp", datetime.utcnow()).isoformat(),
                "outcome_data": outcome
            }
            
            # Store in Qdrant
            point = PointStruct(
                id=vector_id,
                vector=embedding,
                payload=payload
            )
            
            self.qdrant_client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=[point]
            )
            
            logger.info(f"Outcome stored in Qdrant: {vector_id}")
            
            return vector_id
            
        except Exception as e:
            logger.error(f"Error storing outcome: {e}", exc_info=True)
            raise
    
    async def find_similar_cases(
        self,
        recommendation: Dict[str, Any],
        limit: int = 10
    ) -> List[SimilarCase]:
        """
        Find similar historical cases.
        
        Args:
            recommendation: Current recommendation
            limit: Maximum number of similar cases
        
        Returns:
            List of similar cases
        """
        try:
            logger.info(f"Finding similar cases for recommendation type: {recommendation.get('recommendation_type')}")
            
            # Generate embedding for query
            query_embedding = await self._generate_embedding(recommendation)
            
            # Search in Qdrant
            search_result = self.qdrant_client.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=query_embedding,
                limit=limit
            )
            
            # Convert to SimilarCase objects
            similar_cases = []
            for hit in search_result:
                payload = hit.payload
                
                # Create outcome record from payload
                outcome = OutcomeRecord(
                    outcome_id=payload.get("outcome_data", {}).get("outcome_id", "unknown"),
                    execution_id=payload.get("outcome_data", {}).get("execution_id", "unknown"),
                    recommendation_id=payload["recommendation_id"],
                    recommendation_type=payload["recommendation_type"],
                    success=payload["success"],
                    actual_savings=payload.get("actual_savings"),
                    predicted_savings=payload["predicted_savings"],
                    savings_accuracy=payload["savings_accuracy"],
                    execution_duration_seconds=payload.get("outcome_data", {}).get("execution_duration_seconds", 0.0),
                    issues_encountered=payload.get("outcome_data", {}).get("issues_encountered", []),
                    post_execution_metrics=payload.get("outcome_data", {}).get("post_execution_metrics", {}),
                    timestamp=datetime.fromisoformat(payload["execution_date"])
                )
                
                similar_case = SimilarCase(
                    recommendation_id=payload["recommendation_id"],
                    similarity_score=hit.score,
                    outcome=outcome,
                    context={
                        "resource_type": payload.get("resource_type"),
                        "region": payload.get("region")
                    }
                )
                
                similar_cases.append(similar_case)
            
            logger.info(f"Found {len(similar_cases)} similar cases")
            
            return similar_cases
            
        except Exception as e:
            logger.error(f"Error finding similar cases: {e}", exc_info=True)
            return []
    
    async def get_historical_outcomes(
        self,
        recommendation_type: str,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Get historical outcomes by type.
        
        Args:
            recommendation_type: Type of recommendation
            filters: Additional filters
        
        Returns:
            List of historical outcomes
        """
        try:
            logger.info(f"Getting historical outcomes for type: {recommendation_type}")
            
            # Build filter
            must_conditions = [
                FieldCondition(
                    key="recommendation_type",
                    match=MatchValue(value=recommendation_type)
                )
            ]
            
            # Add additional filters
            if filters:
                for key, value in filters.items():
                    must_conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
            
            # Scroll through all matching points
            scroll_result = self.qdrant_client.scroll(
                collection_name=self.COLLECTION_NAME,
                scroll_filter=Filter(must=must_conditions),
                limit=100
            )
            
            outcomes = [point.payload for point in scroll_result[0]]
            
            logger.info(f"Retrieved {len(outcomes)} historical outcomes")
            
            return outcomes
            
        except Exception as e:
            logger.error(f"Error getting historical outcomes: {e}", exc_info=True)
            return []
    
    async def get_success_rate(
        self,
        recommendation_type: str
    ) -> float:
        """
        Get success rate for a recommendation type.
        
        Args:
            recommendation_type: Type of recommendation
        
        Returns:
            Success rate (0.0 to 1.0)
        """
        try:
            outcomes = await self.get_historical_outcomes(recommendation_type)
            
            if not outcomes:
                return 0.0
            
            successful = sum(1 for o in outcomes if o.get("success", False))
            success_rate = successful / len(outcomes)
            
            logger.info(f"Success rate for {recommendation_type}: {success_rate:.1%}")
            
            return success_rate
            
        except Exception as e:
            logger.error(f"Error calculating success rate: {e}", exc_info=True)
            return 0.0
    
    async def get_avg_savings_accuracy(
        self,
        recommendation_type: str
    ) -> float:
        """
        Get average savings accuracy for a recommendation type.
        
        Args:
            recommendation_type: Type of recommendation
        
        Returns:
            Average savings accuracy
        """
        try:
            outcomes = await self.get_historical_outcomes(recommendation_type)
            
            if not outcomes:
                return 0.0
            
            # Filter successful outcomes with savings data
            valid_outcomes = [
                o for o in outcomes
                if o.get("success", False) and o.get("savings_accuracy", 0) > 0
            ]
            
            if not valid_outcomes:
                return 0.0
            
            avg_accuracy = sum(o["savings_accuracy"] for o in valid_outcomes) / len(valid_outcomes)
            
            logger.info(f"Avg savings accuracy for {recommendation_type}: {avg_accuracy:.1%}")
            
            return avg_accuracy
            
        except Exception as e:
            logger.error(f"Error calculating avg savings accuracy: {e}", exc_info=True)
            return 0.0
    
    # Private helper methods
    
    async def _generate_embedding(
        self,
        recommendation: Dict[str, Any]
    ) -> List[float]:
        """
        Generate embedding for recommendation.
        
        Args:
            recommendation: Recommendation data
        
        Returns:
            Embedding vector
        """
        try:
            # Create text representation
            text = f"""
            Type: {recommendation.get('recommendation_type', 'unknown')}
            Resource: {recommendation.get('resource_type', 'unknown')} {recommendation.get('resource_id', 'unknown')}
            Region: {recommendation.get('region', 'unknown')}
            Predicted Savings: ${recommendation.get('monthly_savings', 0)}/month
            Risk: {recommendation.get('risk_level', 'medium')}
            """
            
            # Generate embedding using OpenAI
            if self.openai_client:
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text.strip()
                )
                embedding = response.data[0].embedding
            else:
                # Mock embedding for testing
                logger.warning("No OpenAI API key, using mock embedding")
                embedding = [0.0] * self.EMBEDDING_SIZE
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            # Return zero vector as fallback
            return [0.0] * self.EMBEDDING_SIZE
