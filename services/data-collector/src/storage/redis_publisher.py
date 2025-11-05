"""
Redis publisher for real-time events
"""
import logging
import json
from typing import Dict, Any
from datetime import datetime

import redis

from ..config import config

logger = logging.getLogger(__name__)


class RedisPublisher:
    """
    Publishes events to Redis pub/sub
    """
    
    def __init__(self):
        """Initialize Redis publisher"""
        self.client = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis"""
        try:
            self.client = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                decode_responses=True
            )
            # Test connection
            self.client.ping()
            logger.info(f"Connected to Redis at {config.REDIS_HOST}:{config.REDIS_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def publish_data_updated(
        self,
        customer_id: str,
        provider: str,
        data_type: str,
        records_count: int
    ):
        """
        Publish data updated event
        
        Args:
            customer_id: Customer ID
            provider: Cloud provider
            data_type: Type of data updated
            records_count: Number of records updated
        """
        try:
            event = {
                "event_type": "data_updated",
                "customer_id": customer_id,
                "provider": provider,
                "data_type": data_type,
                "records_count": records_count,
                "timestamp": datetime.now().isoformat()
            }
            
            # Publish to channel
            channel = f"data_updated:{customer_id}"
            self.client.publish(channel, json.dumps(event))
            
            # Also publish to global channel
            self.client.publish("data_updated", json.dumps(event))
            
            logger.info(f"Published data_updated event for {customer_id}/{provider}/{data_type}")
            
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
    
    def publish_collection_status(
        self,
        task_id: str,
        status: str,
        message: str = None
    ):
        """
        Publish collection status event
        
        Args:
            task_id: Task ID
            status: Collection status
            message: Optional message
        """
        try:
            event = {
                "event_type": "collection_status",
                "task_id": task_id,
                "status": status,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
            
            channel = f"collection_status:{task_id}"
            self.client.publish(channel, json.dumps(event))
            
            logger.info(f"Published collection_status event for task {task_id}: {status}")
            
        except Exception as e:
            logger.error(f"Failed to publish status event: {e}")
    
    def close(self):
        """Close Redis connection"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from Redis")
