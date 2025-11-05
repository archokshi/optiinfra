"""
Analysis Engine

Main engine for bottleneck detection and SLO monitoring.
"""

import logging
from typing import List, Optional, Union
from datetime import datetime

from src.models.analysis import AnalysisResult, AnalysisRequest, SLOTarget
from src.models.metrics import (
    VLLMMetricsSnapshot,
    TGIMetricsSnapshot,
    SGLangMetricsSnapshot
)
from src.analysis.bottleneck_detector import BottleneckDetector
from src.analysis.slo_monitor import SLOMonitor

logger = logging.getLogger(__name__)


class AnalysisEngine:
    """Main analysis engine."""
    
    def __init__(self, custom_thresholds: Optional[dict] = None):
        """
        Initialize engine.
        
        Args:
            custom_thresholds: Custom threshold values
        """
        self.bottleneck_detector = BottleneckDetector(custom_thresholds)
        self.slo_monitor = SLOMonitor()
    
    def analyze(
        self,
        metrics: Union[VLLMMetricsSnapshot, TGIMetricsSnapshot, SGLangMetricsSnapshot],
        instance_type: str,
        slo_targets: Optional[List[SLOTarget]] = None
    ) -> AnalysisResult:
        """
        Analyze metrics and generate insights.
        
        Args:
            metrics: Metrics snapshot
            instance_type: Type of instance (vllm, tgi, sglang)
            slo_targets: Optional SLO targets
            
        Returns:
            Analysis result
        """
        logger.info(f"Analyzing metrics for {instance_type} instance {metrics.instance_id}")
        
        # Detect bottlenecks
        if instance_type == "vllm":
            bottlenecks = self.bottleneck_detector.detect_vllm_bottlenecks(metrics)
        elif instance_type == "tgi":
            bottlenecks = self.bottleneck_detector.detect_tgi_bottlenecks(metrics)
        elif instance_type == "sglang":
            bottlenecks = self.bottleneck_detector.detect_sglang_bottlenecks(metrics)
        else:
            raise ValueError(f"Unknown instance type: {instance_type}")
        
        # Check SLOs
        slo_statuses = []
        if slo_targets:
            slo_statuses = self.slo_monitor.check_slos(metrics, slo_targets)
        
        # Calculate health score
        health_score = self._calculate_health_score(bottlenecks, slo_statuses)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(bottlenecks, slo_statuses)
        
        return AnalysisResult(
            instance_id=metrics.instance_id,
            instance_type=instance_type,
            timestamp=datetime.utcnow(),
            bottlenecks=bottlenecks,
            slo_statuses=slo_statuses,
            overall_health_score=health_score,
            recommendations=recommendations
        )
    
    def _calculate_health_score(self, bottlenecks, slo_statuses) -> float:
        """Calculate overall health score (0-100)."""
        score = 100.0
        
        # Deduct points for bottlenecks
        for bottleneck in bottlenecks:
            if bottleneck.severity.value == "critical":
                score -= 25
            elif bottleneck.severity.value == "high":
                score -= 15
            elif bottleneck.severity.value == "medium":
                score -= 10
            else:
                score -= 5
        
        # Deduct points for SLO violations
        if slo_statuses:
            violations = sum(1 for s in slo_statuses if not s.is_compliant)
            score -= (violations / len(slo_statuses)) * 20
        
        return max(0.0, min(100.0, score))
    
    def _generate_recommendations(self, bottlenecks, slo_statuses) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Add bottleneck recommendations
        for bottleneck in bottlenecks:
            if bottleneck.recommendation not in recommendations:
                recommendations.append(bottleneck.recommendation)
        
        # Add SLO-specific recommendations
        for status in slo_statuses:
            if not status.is_compliant:
                rec = f"Address {status.target.name} SLO violation: current {status.current_value:.2f}, target {status.target.target_value:.2f}"
                if rec not in recommendations:
                    recommendations.append(rec)
        
        return recommendations
