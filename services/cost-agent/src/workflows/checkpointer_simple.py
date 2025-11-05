"""
Simple In-Memory Checkpointer for LangGraph

Provides state persistence using in-memory storage for development and testing.
For production, use PostgreSQL checkpointer when psycopg2 is available.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime


class SimpleMemoryCheckpointer:
    """
    Simple in-memory checkpoint saver for LangGraph workflows
    
    Stores workflow state in memory for development and testing.
    Compatible with LangGraph 0.2.55 API.
    """
    
    def __init__(self):
        """Initialize in-memory checkpointer"""
        self.checkpoints: Dict[str, list] = {}
        self.versions: Dict[str, int] = {}
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialized SimpleMemoryCheckpointer")
    
    def put(
        self,
        config: Dict[str, Any],
        checkpoint: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Save a checkpoint to memory
        
        Args:
            config: Configuration dict with thread_id
            checkpoint: Checkpoint data to save
            metadata: Checkpoint metadata
        """
        thread_id = config.get('configurable', {}).get('thread_id', 'default')
        
        if thread_id not in self.checkpoints:
            self.checkpoints[thread_id] = []
        
        checkpoint_data = {
            'checkpoint': checkpoint,
            'metadata': metadata or {},
            'timestamp': datetime.utcnow()
        }
        
        self.checkpoints[thread_id].append(checkpoint_data)
        self.logger.debug(f"Saved checkpoint for thread {thread_id}")
    
    def get(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Retrieve the latest checkpoint for a thread
        
        Args:
            config: Configuration dict with thread_id
            
        Returns:
            Latest checkpoint or None
        """
        thread_id = config.get('configurable', {}).get('thread_id')
        
        if not thread_id or thread_id not in self.checkpoints:
            return None
        
        checkpoints = self.checkpoints[thread_id]
        if not checkpoints:
            return None
        
        return checkpoints[-1]['checkpoint']
    
    def list(self, config: Dict[str, Any], limit: int = 10) -> list:
        """
        List checkpoints for a thread
        
        Args:
            config: Configuration dict with thread_id
            limit: Maximum number of checkpoints to return
            
        Returns:
            List of checkpoints
        """
        thread_id = config.get('configurable', {}).get('thread_id')
        
        if not thread_id or thread_id not in self.checkpoints:
            return []
        
        checkpoints = self.checkpoints[thread_id]
        return [cp['checkpoint'] for cp in checkpoints[-limit:]]
    
    def delete(self, config: Dict[str, Any]) -> None:
        """
        Delete all checkpoints for a thread
        
        Args:
            config: Configuration dict with thread_id
        """
        thread_id = config.get('configurable', {}).get('thread_id')
        
        if thread_id and thread_id in self.checkpoints:
            del self.checkpoints[thread_id]
            if thread_id in self.versions:
                del self.versions[thread_id]
            self.logger.info(f"Deleted checkpoints for thread {thread_id}")
    
    def get_next_version(self, config: Dict[str, Any]) -> int:
        """
        Get the next version number for a thread
        
        Args:
            config: Configuration dict with thread_id
            
        Returns:
            Next version number
        """
        thread_id = config.get('configurable', {}).get('thread_id', 'default')
        
        if thread_id not in self.versions:
            self.versions[thread_id] = 1
        else:
            self.versions[thread_id] += 1
        
        return self.versions[thread_id]


def create_simple_checkpointer() -> SimpleMemoryCheckpointer:
    """
    Factory function to create a simple memory checkpointer
    
    Returns:
        SimpleMemoryCheckpointer instance
    """
    return SimpleMemoryCheckpointer()
