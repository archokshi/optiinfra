"""
Configuration Analyzer

Analyzes configuration impact on quality and performance.
"""

import statistics
from typing import List, Dict, Any, Optional
from ..models.configuration import (
    ConfigurationSnapshot,
    ConfigurationMetrics,
    ParameterImpact,
    ConfigurationRecommendation
)
from ..core.logger import logger


class ConfigurationAnalyzer:
    """Analyzes configuration parameters and their impact."""
    
    def __init__(self):
        """Initialize configuration analyzer."""
        self.metrics_history: List[ConfigurationMetrics] = []
        logger.info("Configuration analyzer initialized")
    
    def analyze_parameter_impact(
        self,
        parameter: str,
        samples: int = 100
    ) -> ParameterImpact:
        """
        Analyze a parameter's impact on metrics.
        
        Args:
            parameter: Parameter to analyze
            samples: Number of samples to analyze
            
        Returns:
            Parameter impact analysis
        """
        logger.info(f"Analyzing impact of parameter: {parameter}")
        
        # Simulated analysis (in production, would use real data)
        if parameter == "temperature":
            impact = ParameterImpact(
                parameter="temperature",
                current_value=0.3,
                quality_correlation=-0.65,  # Lower temp = higher quality
                cost_correlation=0.05,       # Minimal cost impact
                latency_correlation=0.02,    # Minimal latency impact
                optimal_range={"min": 0.3, "max": 0.5, "recommended": 0.4}
            )
        elif parameter == "max_tokens":
            impact = ParameterImpact(
                parameter="max_tokens",
                current_value=500,
                quality_correlation=0.45,    # More tokens = better quality
                cost_correlation=0.85,       # More tokens = higher cost
                latency_correlation=0.70,    # More tokens = higher latency
                optimal_range={"min": 300, "max": 800, "recommended": 500}
            )
        else:
            impact = ParameterImpact(
                parameter=parameter,
                current_value=None,
                quality_correlation=0.0,
                cost_correlation=0.0,
                latency_correlation=0.0
            )
        
        logger.debug(f"Parameter impact analysis complete: {parameter}")
        return impact
    
    def find_optimal_temperature(
        self,
        target_quality: float = 85.0,
        samples: int = 100
    ) -> Dict[str, Any]:
        """
        Find optimal temperature setting.
        
        Args:
            target_quality: Target quality score
            samples: Number of samples to analyze
            
        Returns:
            Optimal temperature analysis
        """
        logger.info(f"Finding optimal temperature for quality {target_quality}")
        
        # Simulated analysis
        optimal = {
            "current_temperature": 0.3,
            "optimal_temperature": 0.4,
            "expected_quality": 87.5,
            "quality_improvement": "+2.5%",
            "confidence": 0.85,
            "reasoning": "Temperature 0.4 balances consistency and quality"
        }
        
        logger.debug(f"Optimal temperature: {optimal['optimal_temperature']}")
        return optimal
    
    def analyze_token_efficiency(
        self,
        samples: int = 100
    ) -> Dict[str, Any]:
        """
        Analyze token usage efficiency.
        
        Args:
            samples: Number of samples to analyze
            
        Returns:
            Token efficiency analysis
        """
        logger.info("Analyzing token efficiency")
        
        # Simulated analysis
        efficiency = {
            "avg_tokens_used": 450,
            "avg_quality": 85.0,
            "quality_per_token": 0.189,
            "optimal_token_range": {"min": 300, "max": 600},
            "recommended_max_tokens": 500,
            "potential_cost_savings": "10%",
            "reasoning": "Current token usage is efficient"
        }
        
        logger.debug(f"Token efficiency: {efficiency['quality_per_token']:.3f} quality/token")
        return efficiency
    
    def detect_configuration_drift(
        self,
        current_config: ConfigurationSnapshot,
        optimal_config: ConfigurationSnapshot,
        threshold: float = 0.1
    ) -> Dict[str, Any]:
        """
        Detect configuration drift from optimal.
        
        Args:
            current_config: Current configuration
            optimal_config: Optimal configuration
            threshold: Drift threshold
            
        Returns:
            Drift detection results
        """
        logger.info("Detecting configuration drift")
        
        drifts = []
        
        # Check temperature drift
        temp_diff = abs(current_config.temperature - optimal_config.temperature)
        if temp_diff > threshold:
            drifts.append({
                "parameter": "temperature",
                "current": current_config.temperature,
                "optimal": optimal_config.temperature,
                "drift": temp_diff
            })
        
        # Check max_tokens drift
        token_diff = abs(current_config.max_tokens - optimal_config.max_tokens)
        if token_diff > (optimal_config.max_tokens * threshold):
            drifts.append({
                "parameter": "max_tokens",
                "current": current_config.max_tokens,
                "optimal": optimal_config.max_tokens,
                "drift": token_diff
            })
        
        result = {
            "drift_detected": len(drifts) > 0,
            "drifted_parameters": [d["parameter"] for d in drifts],
            "drifts": drifts,
            "drift_magnitude": len(drifts) / 5.0  # Normalized
        }
        
        logger.debug(f"Drift detection: {len(drifts)} parameters drifted")
        return result
    
    def generate_recommendations(
        self,
        current_config: ConfigurationSnapshot,
        strategy: str = "balanced"
    ) -> List[ConfigurationRecommendation]:
        """
        Generate optimization recommendations.
        
        Args:
            current_config: Current configuration
            strategy: Optimization strategy
            
        Returns:
            List of recommendations
        """
        logger.info(f"Generating recommendations with strategy: {strategy}")
        
        recommendations = []
        
        # Temperature recommendation
        if current_config.temperature > 0.5:
            recommendations.append(ConfigurationRecommendation(
                recommendation_id=f"rec-temp-001",
                parameter="temperature",
                current_value=current_config.temperature,
                recommended_value=0.4,
                expected_improvement={
                    "quality": "+2.5%",
                    "cost": "-5%",
                    "latency": "0%"
                },
                confidence=0.85,
                reason="Lower temperature improves consistency without sacrificing quality",
                priority="high"
            ))
        
        # Max tokens recommendation
        if current_config.max_tokens > 800:
            recommendations.append(ConfigurationRecommendation(
                recommendation_id=f"rec-tokens-001",
                parameter="max_tokens",
                current_value=current_config.max_tokens,
                recommended_value=600,
                expected_improvement={
                    "quality": "-1%",
                    "cost": "-15%",
                    "latency": "-10%"
                },
                confidence=0.75,
                reason="Reducing max tokens can save costs with minimal quality impact",
                priority="medium"
            ))
        
        logger.debug(f"Generated {len(recommendations)} recommendations")
        return recommendations


# Global instance
config_analyzer = ConfigurationAnalyzer()
