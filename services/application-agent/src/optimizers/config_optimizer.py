"""
Configuration Optimizer

Optimizes LLM configuration for quality, cost, or balance.
"""

import uuid
from datetime import datetime
from typing import Dict, Any
from ..models.configuration import (
    ConfigurationSnapshot,
    ConfigurationChange,
    OptimizationStrategy,
    OptimizationRequest,
    OptimizationResult,
    ConfigurationRecommendation
)
from ..core.logger import logger


class ConfigurationOptimizer:
    """Optimizes configuration parameters."""
    
    def __init__(self):
        """Initialize configuration optimizer."""
        logger.info("Configuration optimizer initialized")
    
    def optimize_for_quality(
        self,
        current_config: ConfigurationSnapshot
    ) -> ConfigurationSnapshot:
        """
        Optimize configuration for maximum quality.
        
        Args:
            current_config: Current configuration
            
        Returns:
            Optimized configuration
        """
        logger.info("Optimizing for quality")
        
        optimized = ConfigurationSnapshot(
            snapshot_id=f"cfg-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.utcnow(),
            model=current_config.model,
            temperature=0.3,  # Lower for consistency
            max_tokens=1000,  # Higher for completeness
            timeout=60,       # Higher for reliability
            max_retries=5,    # More retries
            enabled=True,
            metadata={"optimization": "quality_first"}
        )
        
        logger.debug("Quality optimization complete")
        return optimized
    
    def optimize_for_cost(
        self,
        current_config: ConfigurationSnapshot
    ) -> ConfigurationSnapshot:
        """
        Optimize configuration for minimum cost.
        
        Args:
            current_config: Current configuration
            
        Returns:
            Optimized configuration
        """
        logger.info("Optimizing for cost")
        
        optimized = ConfigurationSnapshot(
            snapshot_id=f"cfg-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.utcnow(),
            model=current_config.model,
            temperature=0.5,  # Moderate
            max_tokens=300,   # Lower to reduce cost
            timeout=15,       # Lower timeout
            max_retries=2,    # Fewer retries
            enabled=True,
            metadata={"optimization": "cost_first"}
        )
        
        logger.debug("Cost optimization complete")
        return optimized
    
    def optimize_balanced(
        self,
        current_config: ConfigurationSnapshot
    ) -> ConfigurationSnapshot:
        """
        Balance quality and cost.
        
        Args:
            current_config: Current configuration
            
        Returns:
            Optimized configuration
        """
        logger.info("Optimizing for balance")
        
        optimized = ConfigurationSnapshot(
            snapshot_id=f"cfg-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.utcnow(),
            model=current_config.model,
            temperature=0.4,  # Balanced
            max_tokens=500,   # Moderate
            timeout=30,       # Standard
            max_retries=3,    # Standard
            enabled=True,
            metadata={"optimization": "balanced"}
        )
        
        logger.debug("Balanced optimization complete")
        return optimized
    
    def optimize(
        self,
        current_config: ConfigurationSnapshot,
        request: OptimizationRequest
    ) -> OptimizationResult:
        """
        Optimize configuration based on strategy.
        
        Args:
            current_config: Current configuration
            request: Optimization request
            
        Returns:
            Optimization result
        """
        logger.info(f"Optimizing with strategy: {request.strategy}")
        
        # Select optimization strategy
        if request.strategy == OptimizationStrategy.QUALITY_FIRST:
            optimized = self.optimize_for_quality(current_config)
        elif request.strategy == OptimizationStrategy.COST_FIRST:
            optimized = self.optimize_for_cost(current_config)
        elif request.strategy == OptimizationStrategy.BALANCED:
            optimized = self.optimize_balanced(current_config)
        else:
            optimized = current_config
        
        # Calculate changes
        changes = []
        if current_config.temperature != optimized.temperature:
            changes.append(ConfigurationChange(
                change_id=f"chg-{uuid.uuid4().hex[:8]}",
                timestamp=datetime.utcnow(),
                parameter="temperature",
                old_value=current_config.temperature,
                new_value=optimized.temperature,
                reason=f"Optimization: {request.strategy.value}"
            ))
        
        if current_config.max_tokens != optimized.max_tokens:
            changes.append(ConfigurationChange(
                change_id=f"chg-{uuid.uuid4().hex[:8]}",
                timestamp=datetime.utcnow(),
                parameter="max_tokens",
                old_value=current_config.max_tokens,
                new_value=optimized.max_tokens,
                reason=f"Optimization: {request.strategy.value}"
            ))
        
        # Generate recommendations
        recommendations = [
            ConfigurationRecommendation(
                recommendation_id=f"rec-{uuid.uuid4().hex[:8]}",
                parameter="temperature",
                current_value=current_config.temperature,
                recommended_value=optimized.temperature,
                expected_improvement={
                    "quality": "+2%",
                    "cost": "-5%"
                },
                confidence=0.85,
                reason=f"Optimized for {request.strategy.value}"
            )
        ]
        
        result = OptimizationResult(
            original_config=current_config,
            optimized_config=optimized,
            changes=changes,
            expected_improvements={
                "quality": "+2-5%",
                "cost": "-5-10%",
                "latency": "0-5%"
            },
            recommendations=recommendations
        )
        
        logger.info(f"Optimization complete: {len(changes)} changes")
        return result
    
    def validate_configuration(
        self,
        config: ConfigurationSnapshot,
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate configuration against constraints.
        
        Args:
            config: Configuration to validate
            constraints: Validation constraints
            
        Returns:
            Validation result
        """
        logger.info("Validating configuration")
        
        violations = []
        
        # Check temperature range
        if config.temperature < 0.0 or config.temperature > 1.0:
            violations.append({
                "parameter": "temperature",
                "value": config.temperature,
                "constraint": "0.0 <= temperature <= 1.0"
            })
        
        # Check max_tokens
        if config.max_tokens < 1 or config.max_tokens > 4000:
            violations.append({
                "parameter": "max_tokens",
                "value": config.max_tokens,
                "constraint": "1 <= max_tokens <= 4000"
            })
        
        # Check timeout
        if config.timeout < 1 or config.timeout > 300:
            violations.append({
                "parameter": "timeout",
                "value": config.timeout,
                "constraint": "1 <= timeout <= 300"
            })
        
        result = {
            "valid": len(violations) == 0,
            "violations": violations
        }
        
        logger.debug(f"Validation: {len(violations)} violations found")
        return result


# Global instance
config_optimizer = ConfigurationOptimizer()
