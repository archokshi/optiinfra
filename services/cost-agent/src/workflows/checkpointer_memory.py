"""
Memory Checkpointer for LangGraph (Compatible with 0.2.55)

Provides in-memory state persistence compatible with LangGraph 0.2.55 API.
"""

import logging
from typing import Dict, Any, Optional, Iterator, AsyncIterator, Sequence
from datetime import datetime
from collections import defaultdict


class MemoryCheckpointer:
    """
    In-memory checkpoint saver compatible with LangGraph 0.2.55
    
    Implements the full BaseCheckpointSaver interface for testing and development.
    """
    
    def __init__(self):
        """Initialize in-memory checkpointer"""
        self.storage: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.writes: Dict[str, list] = defaultdict(list)
        self.versions: Dict[str, int] = {}
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialized MemoryCheckpointer (LangGraph 0.2.55 compatible)")
    
    def _get_thread_id(self, config: Dict[str, Any]) -> str:
        """Extract thread_id from config"""
        return config.get('configurable', {}).get('thread_id', 'default')
    
    def get_next_version(self, current: Optional[int], channel: Any) -> int:
        """
        Get the next version number for a channel
        
        Args:
            current: Current version number (or None)
            channel: Channel object
            
        Returns:
            Next version number
        """
        if current is None:
            return 1
        return current + 1
    
    def put(
        self,
        config: Dict[str, Any],
        checkpoint: Dict[str, Any],
        metadata: Dict[str, Any],
        new_versions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save a checkpoint (sync version)
        
        Args:
            config: Configuration dict with thread_id
            checkpoint: Checkpoint data to save
            metadata: Checkpoint metadata
            new_versions: Channel versions
            
        Returns:
            Updated config
        """
        thread_id = self._get_thread_id(config)
        checkpoint_id = checkpoint.get('id', str(datetime.now().timestamp()))
        
        self.storage[thread_id][checkpoint_id] = {
            'checkpoint': checkpoint,
            'metadata': metadata or {},
            'new_versions': new_versions or {},
            'timestamp': datetime.now()
        }
        
        self.logger.debug(f"Saved checkpoint {checkpoint_id} for thread {thread_id}")
        return config
    
    async def aput(
        self,
        config: Dict[str, Any],
        checkpoint: Dict[str, Any],
        metadata: Dict[str, Any],
        new_versions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Save a checkpoint (async version)
        
        Args:
            config: Configuration dict with thread_id
            checkpoint: Checkpoint data to save
            metadata: Checkpoint metadata
            new_versions: Channel versions
            
        Returns:
            Updated config
        """
        return self.put(config, checkpoint, metadata, new_versions)
    
    def get(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Retrieve the latest checkpoint (sync version)
        
        Args:
            config: Configuration dict with thread_id
            
        Returns:
            Latest checkpoint or None
        """
        thread_id = self._get_thread_id(config)
        
        if thread_id not in self.storage or not self.storage[thread_id]:
            return None
        
        # Get the most recent checkpoint
        checkpoints = sorted(
            self.storage[thread_id].items(),
            key=lambda x: x[1]['timestamp'],
            reverse=True
        )
        
        if checkpoints:
            return checkpoints[0][1]['checkpoint']
        return None
    
    async def aget(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Retrieve the latest checkpoint (async version)
        
        Args:
            config: Configuration dict with thread_id
            
        Returns:
            Latest checkpoint or None
        """
        return self.get(config)
    
    def get_tuple(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get checkpoint tuple (checkpoint + metadata)
        
        Args:
            config: Configuration dict with thread_id
            
        Returns:
            Checkpoint tuple or None
        """
        thread_id = self._get_thread_id(config)
        
        if thread_id not in self.storage or not self.storage[thread_id]:
            return None
        
        # Get the most recent checkpoint
        checkpoints = sorted(
            self.storage[thread_id].items(),
            key=lambda x: x[1]['timestamp'],
            reverse=True
        )
        
        if checkpoints:
            checkpoint_id, data = checkpoints[0]
            return {
                'config': config,
                'checkpoint': data['checkpoint'],
                'metadata': data['metadata'],
                'parent_config': None
            }
        return None
    
    async def aget_tuple(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get checkpoint tuple (async version)
        
        Args:
            config: Configuration dict with thread_id
            
        Returns:
            Checkpoint tuple or None
        """
        return self.get_tuple(config)
    
    def list(
        self,
        config: Optional[Dict[str, Any]] = None,
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> Iterator[Dict[str, Any]]:
        """
        List checkpoints (sync version)
        
        Args:
            config: Configuration dict with thread_id
            filter: Filter criteria
            before: Return checkpoints before this config
            limit: Maximum number of checkpoints to return
            
        Returns:
            Iterator of checkpoint tuples
        """
        if config is None:
            return iter([])
        
        thread_id = self._get_thread_id(config)
        
        if thread_id not in self.storage:
            return iter([])
        
        # Get all checkpoints for thread, sorted by timestamp
        checkpoints = sorted(
            self.storage[thread_id].items(),
            key=lambda x: x[1]['timestamp'],
            reverse=True
        )
        
        # Apply limit
        if limit:
            checkpoints = checkpoints[:limit]
        
        # Convert to checkpoint tuples
        result = []
        for checkpoint_id, data in checkpoints:
            result.append({
                'config': config,
                'checkpoint': data['checkpoint'],
                'metadata': data['metadata'],
                'parent_config': None
            })
        
        return iter(result)
    
    async def alist(
        self,
        config: Optional[Dict[str, Any]] = None,
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        List checkpoints (async version)
        
        Args:
            config: Configuration dict with thread_id
            filter: Filter criteria
            before: Return checkpoints before this config
            limit: Maximum number of checkpoints to return
            
        Returns:
            Async iterator of checkpoint tuples
        """
        # Convert sync iterator to async
        for item in self.list(config, filter=filter, before=before, limit=limit):
            yield item
    
    def put_writes(
        self,
        config: Dict[str, Any],
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = ''
    ) -> None:
        """
        Store writes for a task (sync version)
        
        Args:
            config: Configuration dict
            writes: Sequence of (channel, value) tuples
            task_id: Task identifier
            task_path: Task path
        """
        thread_id = self._get_thread_id(config)
        
        self.writes[thread_id].append({
            'task_id': task_id,
            'task_path': task_path,
            'writes': list(writes),
            'timestamp': datetime.now()
        })
        
        self.logger.debug(f"Stored {len(writes)} writes for task {task_id}")
    
    async def aput_writes(
        self,
        config: Dict[str, Any],
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = ''
    ) -> None:
        """
        Store writes for a task (async version)
        
        Args:
            config: Configuration dict
            writes: Sequence of (channel, value) tuples
            task_id: Task identifier
            task_path: Task path
        """
        self.put_writes(config, writes, task_id, task_path)
    
    def delete_thread(self, config: Dict[str, Any]) -> None:
        """
        Delete all checkpoints for a thread
        
        Args:
            config: Configuration dict with thread_id
        """
        thread_id = self._get_thread_id(config)
        
        if thread_id in self.storage:
            del self.storage[thread_id]
        if thread_id in self.writes:
            del self.writes[thread_id]
        if thread_id in self.versions:
            del self.versions[thread_id]
        
        self.logger.info(f"Deleted all data for thread {thread_id}")
    
    async def adelete_thread(self, config: Dict[str, Any]) -> None:
        """
        Delete all checkpoints for a thread (async version)
        
        Args:
            config: Configuration dict with thread_id
        """
        self.delete_thread(config)


def create_memory_checkpointer() -> MemoryCheckpointer:
    """
    Factory function to create a memory checkpointer
    
    Returns:
        MemoryCheckpointer instance compatible with LangGraph 0.2.55
    """
    return MemoryCheckpointer()
