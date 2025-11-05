"""
Initialize Qdrant collections for Learning Loop.

This script creates the necessary Qdrant collections with proper schemas.
"""

import asyncio
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def initialize_qdrant_collections(qdrant_url: str = "http://localhost:6333"):
    """
    Initialize Qdrant collections.
    
    Args:
        qdrant_url: Qdrant server URL
    """
    try:
        logger.info(f"Connecting to Qdrant at {qdrant_url}")
        client = QdrantClient(url=qdrant_url)
        
        # Check connection
        collections = client.get_collections()
        logger.info(f"Connected successfully. Found {len(collections.collections)} existing collections")
        
        # Collection configurations
        collections_config = {
            "recommendation_outcomes": {
                "size": 1536,  # OpenAI text-embedding-3-small
                "distance": Distance.COSINE,
                "description": "Stores recommendation outcomes with embeddings for similarity search"
            },
            "execution_history": {
                "size": 1536,
                "distance": Distance.COSINE,
                "description": "Stores execution history for learning"
            },
            "learning_insights": {
                "size": 1536,
                "distance": Distance.COSINE,
                "description": "Stores derived learning insights"
            }
        }
        
        # Create collections
        existing_names = [c.name for c in collections.collections]
        
        for collection_name, config in collections_config.items():
            if collection_name in existing_names:
                logger.info(f"✓ Collection '{collection_name}' already exists")
                
                # Optionally recreate
                recreate = input(f"Recreate '{collection_name}'? (y/N): ").lower() == 'y'
                if recreate:
                    logger.info(f"Deleting collection '{collection_name}'")
                    client.delete_collection(collection_name)
                else:
                    continue
            
            logger.info(f"Creating collection '{collection_name}'")
            logger.info(f"  - Vector size: {config['size']}")
            logger.info(f"  - Distance: {config['distance']}")
            logger.info(f"  - Description: {config['description']}")
            
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=config["size"],
                    distance=config["distance"]
                )
            )
            
            logger.info(f"✓ Collection '{collection_name}' created successfully")
        
        # Verify collections
        logger.info("\n" + "="*60)
        logger.info("VERIFICATION")
        logger.info("="*60)
        
        collections = client.get_collections()
        for collection in collections.collections:
            info = client.get_collection(collection.name)
            logger.info(f"\n✓ {collection.name}")
            logger.info(f"  - Vectors: {info.vectors_count}")
            logger.info(f"  - Points: {info.points_count}")
            logger.info(f"  - Status: {info.status}")
        
        logger.info("\n" + "="*60)
        logger.info("✓ ALL COLLECTIONS INITIALIZED SUCCESSFULLY")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"Error initializing Qdrant collections: {e}", exc_info=True)
        return False


async def test_qdrant_operations(qdrant_url: str = "http://localhost:6333"):
    """
    Test basic Qdrant operations.
    
    Args:
        qdrant_url: Qdrant server URL
    """
    try:
        logger.info("\n" + "="*60)
        logger.info("TESTING QDRANT OPERATIONS")
        logger.info("="*60)
        
        client = QdrantClient(url=qdrant_url)
        
        # Test 1: Insert a test point
        logger.info("\nTest 1: Inserting test point")
        test_vector = [0.1] * 1536
        test_point = PointStruct(
            id="test-point-1",
            vector=test_vector,
            payload={
                "recommendation_id": "rec-test-123",
                "recommendation_type": "terminate",
                "success": True,
                "actual_savings": 50.0,
                "test": True
            }
        )
        
        client.upsert(
            collection_name="recommendation_outcomes",
            points=[test_point]
        )
        logger.info("✓ Test point inserted")
        
        # Test 2: Search for similar points
        logger.info("\nTest 2: Searching for similar points")
        search_results = client.search(
            collection_name="recommendation_outcomes",
            query_vector=test_vector,
            limit=5
        )
        logger.info(f"✓ Found {len(search_results)} similar points")
        
        # Test 3: Retrieve point by ID
        logger.info("\nTest 3: Retrieving point by ID")
        retrieved = client.retrieve(
            collection_name="recommendation_outcomes",
            ids=["test-point-1"]
        )
        logger.info(f"✓ Retrieved {len(retrieved)} points")
        
        # Test 4: Delete test point
        logger.info("\nTest 4: Deleting test point")
        client.delete(
            collection_name="recommendation_outcomes",
            points_selector=["test-point-1"]
        )
        logger.info("✓ Test point deleted")
        
        logger.info("\n" + "="*60)
        logger.info("✓ ALL TESTS PASSED")
        logger.info("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing Qdrant operations: {e}", exc_info=True)
        return False


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize Qdrant collections")
    parser.add_argument(
        "--url",
        default="http://localhost:6333",
        help="Qdrant server URL (default: http://localhost:6333)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run tests after initialization"
    )
    parser.add_argument(
        "--skip-init",
        action="store_true",
        help="Skip initialization, only run tests"
    )
    
    args = parser.parse_args()
    
    # Initialize collections
    if not args.skip_init:
        success = await initialize_qdrant_collections(args.url)
        if not success:
            logger.error("Failed to initialize collections")
            return 1
    
    # Run tests
    if args.test:
        success = await test_qdrant_operations(args.url)
        if not success:
            logger.error("Tests failed")
            return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
