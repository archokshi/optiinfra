"""
Configuration Tracker

Tracks LLM configuration changes and maintains history.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from ..models.configuration import (
    ConfigurationSnapshot,
    ConfigurationChange
)
from ..core.config import settings
from ..core.logger import logger


class ConfigurationTracker:
    """Tracks configuration changes and history."""
    
    def __init__(self):
        """Initialize configuration tracker."""
        self.snapshots: List[ConfigurationSnapshot] = []
        self.changes: List[ConfigurationChange] = []
        logger.info("Configuration tracker initialized")
    
    def get_current_config(self) -> ConfigurationSnapshot:
        """
        Get current configuration snapshot.
        
        Returns:
            Current configuration
        """
        snapshot = ConfigurationSnapshot(
            snapshot_id=f"cfg-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.utcnow(),
            model=settings.groq_model,
            temperature=0.3,  # Default from LLM prompts
            max_tokens=500,   # Default from LLM client
            timeout=settings.llm_timeout,
            max_retries=settings.llm_max_retries,
            enabled=settings.llm_enabled,
            metadata={
                "agent": "application-agent",
                "version": "1.0.0"
            }
        )
        
        logger.debug(f"Current config snapshot: {snapshot.snapshot_id}")
        return snapshot
    
    def track_configuration(self) -> ConfigurationSnapshot:
        """
        Track current configuration.
        
        Returns:
            Configuration snapshot
        """
        snapshot = self.get_current_config()
        self.snapshots.append(snapshot)
        
        logger.info(f"Configuration tracked: {snapshot.snapshot_id}")
        return snapshot
    
    def track_change(
        self,
        parameter: str,
        old_value: Any,
        new_value: Any,
        reason: str,
        changed_by: str = "system"
    ) -> ConfigurationChange:
        """
        Track a configuration change.
        
        Args:
            parameter: Parameter that changed
            old_value: Previous value
            new_value: New value
            reason: Reason for change
            changed_by: Who made the change
            
        Returns:
            Configuration change record
        """
        change = ConfigurationChange(
            change_id=f"chg-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.utcnow(),
            parameter=parameter,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            changed_by=changed_by
        )
        
        self.changes.append(change)
        
        # Create new snapshot after change
        self.track_configuration()
        
        logger.info(f"Configuration change tracked: {parameter} = {new_value}")
        return change
    
    def get_config_history(
        self,
        limit: int = 10,
        parameter: Optional[str] = None
    ) -> List[ConfigurationSnapshot]:
        """
        Get configuration history.
        
        Args:
            limit: Maximum number of snapshots to return
            parameter: Filter by specific parameter
            
        Returns:
            List of configuration snapshots
        """
        snapshots = self.snapshots[-limit:]
        
        logger.debug(f"Retrieved {len(snapshots)} config snapshots")
        return snapshots
    
    def get_change_history(
        self,
        limit: int = 10,
        parameter: Optional[str] = None
    ) -> List[ConfigurationChange]:
        """
        Get change history.
        
        Args:
            limit: Maximum number of changes to return
            parameter: Filter by specific parameter
            
        Returns:
            List of configuration changes
        """
        changes = self.changes
        
        if parameter:
            changes = [c for c in changes if c.parameter == parameter]
        
        changes = changes[-limit:]
        
        logger.debug(f"Retrieved {len(changes)} config changes")
        return changes
    
    def compare_configs(
        self,
        config1: ConfigurationSnapshot,
        config2: ConfigurationSnapshot
    ) -> Dict[str, Any]:
        """
        Compare two configurations.
        
        Args:
            config1: First configuration
            config2: Second configuration
            
        Returns:
            Dictionary of differences
        """
        differences = {}
        
        if config1.model != config2.model:
            differences["model"] = {"old": config1.model, "new": config2.model}
        
        if config1.temperature != config2.temperature:
            differences["temperature"] = {
                "old": config1.temperature,
                "new": config2.temperature
            }
        
        if config1.max_tokens != config2.max_tokens:
            differences["max_tokens"] = {
                "old": config1.max_tokens,
                "new": config2.max_tokens
            }
        
        if config1.timeout != config2.timeout:
            differences["timeout"] = {"old": config1.timeout, "new": config2.timeout}
        
        if config1.max_retries != config2.max_retries:
            differences["max_retries"] = {
                "old": config1.max_retries,
                "new": config2.max_retries
            }
        
        logger.debug(f"Config comparison: {len(differences)} differences found")
        return differences


# Global instance
config_tracker = ConfigurationTracker()
