"""
SLO Monitor

Monitors Service Level Objectives compliance.
"""

import logging
from typing import List
from datetime import datetime

from src.models.analysis import SLOTarget, SLOStatus
from src.models.metrics import (
    VLLMMetricsSnapshot,
    TGIMetricsSnapshot,
    SGLangMetricsSnapshot
)

logger = logging.getLogger(__name__)


class SLOMonitor:
    """Monitors SLO compliance."""
    
    def check_slos(
        self,
        metrics: any,
        targets: List[SLOTarget]
    ) -> List[SLOStatus]:
        """
        Check SLO compliance.
        
        Args:
            metrics: Metrics snapshot (vLLM, TGI, or SGLang)
            targets: List of SLO targets
            
        Returns:
            List of SLO statuses
        """
        statuses = []
        
        for target in targets:
            current_value = self._extract_metric_value(metrics, target.metric)
            
            if current_value is None:
                logger.warning(f"Metric {target.metric} not found in snapshot")
                continue
            
            is_compliant = self._check_compliance(
                current_value,
                target.target_value,
                target.comparison
            )
            
            deviation = self._calculate_deviation(
                current_value,
                target.target_value
            )
            
            statuses.append(SLOStatus(
                target=target,
                current_value=current_value,
                is_compliant=is_compliant,
                deviation_percent=deviation
            ))
        
        return statuses
    
    def _extract_metric_value(self, metrics: any, metric_path: str) -> float:
        """Extract metric value from snapshot using dot notation."""
        parts = metric_path.split('.')
        value = metrics
        
        for part in parts:
            if hasattr(value, part):
                value = getattr(value, part)
            else:
                return None
        
        return float(value) if value is not None else None
    
    def _check_compliance(
        self,
        current: float,
        target: float,
        comparison: str
    ) -> bool:
        """Check if current value meets target."""
        if comparison == "<":
            return current < target
        elif comparison == "<=":
            return current <= target
        elif comparison == ">":
            return current > target
        elif comparison == ">=":
            return current >= target
        elif comparison == "==":
            return abs(current - target) < 0.01
        else:
            logger.warning(f"Unknown comparison operator: {comparison}")
            return False
    
    def _calculate_deviation(self, current: float, target: float) -> float:
        """Calculate deviation percentage."""
        if target == 0:
            return 0.0
        return ((current - target) / target) * 100.0
