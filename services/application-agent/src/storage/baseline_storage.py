"""
Baseline Storage

In-memory storage for baselines with CRUD operations.
"""

from typing import Dict, List, Optional
from ..models.baseline import Baseline, BaselineStatus
from ..core.logger import logger


class BaselineStorage:
    """In-memory storage for baselines."""
    
    def __init__(self):
        """Initialize baseline storage."""
        self._baselines: Dict[str, Baseline] = {}
        self._index_by_model: Dict[str, List[str]] = {}
    
    def create(self, baseline: Baseline) -> Baseline:
        """
        Create a new baseline.
        
        Args:
            baseline: Baseline to create
            
        Returns:
            Created baseline
        """
        self._baselines[baseline.baseline_id] = baseline
        
        # Update index
        key = f"{baseline.model_name}:{baseline.config_hash}"
        if key not in self._index_by_model:
            self._index_by_model[key] = []
        self._index_by_model[key].append(baseline.baseline_id)
        
        logger.info(f"Created baseline {baseline.baseline_id} for {key}")
        return baseline
    
    def get(self, baseline_id: str) -> Optional[Baseline]:
        """
        Get baseline by ID.
        
        Args:
            baseline_id: Baseline ID
            
        Returns:
            Baseline if found, None otherwise
        """
        return self._baselines.get(baseline_id)
    
    def get_by_model(
        self,
        model_name: str,
        config_hash: str = "default",
        status: Optional[BaselineStatus] = BaselineStatus.ACTIVE
    ) -> Optional[Baseline]:
        """
        Get active baseline for a model and configuration.
        
        Args:
            model_name: Model name
            config_hash: Configuration hash
            status: Baseline status filter
            
        Returns:
            Most recent baseline if found, None otherwise
        """
        key = f"{model_name}:{config_hash}"
        baseline_ids = self._index_by_model.get(key, [])
        
        # Get baselines and filter by status
        baselines = [
            self._baselines[bid]
            for bid in baseline_ids
            if bid in self._baselines and (status is None or self._baselines[bid].status == status)
        ]
        
        # Return most recent
        if baselines:
            return max(baselines, key=lambda b: b.created_at)
        
        return None
    
    def list_all(
        self,
        model_name: Optional[str] = None,
        status: Optional[BaselineStatus] = None
    ) -> List[Baseline]:
        """
        List all baselines with optional filters.
        
        Args:
            model_name: Filter by model name
            status: Filter by status
            
        Returns:
            List of baselines
        """
        baselines = list(self._baselines.values())
        
        # Apply filters
        if model_name:
            baselines = [b for b in baselines if b.model_name == model_name]
        
        if status:
            baselines = [b for b in baselines if b.status == status]
        
        # Sort by created_at descending
        baselines.sort(key=lambda b: b.created_at, reverse=True)
        
        return baselines
    
    def update(self, baseline_id: str, baseline: Baseline) -> Optional[Baseline]:
        """
        Update an existing baseline.
        
        Args:
            baseline_id: Baseline ID
            baseline: Updated baseline
            
        Returns:
            Updated baseline if found, None otherwise
        """
        if baseline_id not in self._baselines:
            return None
        
        self._baselines[baseline_id] = baseline
        logger.info(f"Updated baseline {baseline_id}")
        return baseline
    
    def delete(self, baseline_id: str) -> bool:
        """
        Delete a baseline.
        
        Args:
            baseline_id: Baseline ID
            
        Returns:
            True if deleted, False if not found
        """
        if baseline_id not in self._baselines:
            return False
        
        baseline = self._baselines[baseline_id]
        key = f"{baseline.model_name}:{baseline.config_hash}"
        
        # Remove from index
        if key in self._index_by_model:
            self._index_by_model[key] = [
                bid for bid in self._index_by_model[key]
                if bid != baseline_id
            ]
        
        # Remove baseline
        del self._baselines[baseline_id]
        logger.info(f"Deleted baseline {baseline_id}")
        return True
    
    def count(self) -> int:
        """
        Get total number of baselines.
        
        Returns:
            Number of baselines
        """
        return len(self._baselines)


# Global instance
baseline_storage = BaselineStorage()
