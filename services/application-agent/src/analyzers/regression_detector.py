"""
Regression Detector

Detects quality regressions by comparing against baselines.
"""

import uuid
import statistics
from typing import Optional
from datetime import datetime
from ..models.baseline import (
    Baseline,
    BaselineConfig,
    BaselineMetrics,
    BaselineStatus,
    RegressionResult,
    RegressionAlert,
    RegressionSeverity,
    AlertLevel,
    RegressionDetectionRequest
)
from ..storage.baseline_storage import baseline_storage
from ..analyzers.quality_analyzer import quality_analyzer
from ..core.logger import logger


class RegressionDetector:
    """Detects quality regressions."""
    
    def __init__(self):
        """Initialize regression detector."""
        self.alerts_history = []
    
    def establish_baseline(
        self,
        config: BaselineConfig
    ) -> Baseline:
        """
        Establish a new quality baseline.
        
        Args:
            config: Baseline configuration
            
        Returns:
            Created baseline
        """
        logger.info(f"Establishing baseline for {config.model_name}:{config.config_hash}")
        
        # Get recent quality metrics
        recent_metrics = quality_analyzer.metrics_history[-config.sample_size:]
        
        if len(recent_metrics) < config.sample_size:
            logger.warning(
                f"Only {len(recent_metrics)} metrics available, "
                f"requested {config.sample_size}"
            )
        
        if not recent_metrics:
            raise ValueError("No quality metrics available to establish baseline")
        
        # Calculate baseline metrics
        qualities = [m.overall_quality for m in recent_metrics]
        relevances = [m.relevance.score for m in recent_metrics]
        coherences = [m.coherence.score for m in recent_metrics]
        hallucinations = [m.hallucination.hallucination_rate for m in recent_metrics]
        
        baseline_metrics = BaselineMetrics(
            average_quality=statistics.mean(qualities),
            average_relevance=statistics.mean(relevances),
            average_coherence=statistics.mean(coherences),
            average_hallucination=statistics.mean(hallucinations),
            std_dev_quality=statistics.stdev(qualities) if len(qualities) > 1 else 0.0,
            min_quality=min(qualities),
            max_quality=max(qualities)
        )
        
        # Create baseline
        baseline = Baseline(
            baseline_id=str(uuid.uuid4()),
            model_name=config.model_name,
            config_hash=config.config_hash,
            baseline_type=config.baseline_type,
            metrics=baseline_metrics,
            sample_size=len(recent_metrics),
            status=BaselineStatus.ACTIVE
        )
        
        # Store baseline
        baseline_storage.create(baseline)
        
        logger.info(
            f"Baseline established: {baseline.baseline_id}, "
            f"avg_quality={baseline_metrics.average_quality:.2f}"
        )
        
        return baseline
    
    def detect_regression(
        self,
        request: RegressionDetectionRequest
    ) -> RegressionResult:
        """
        Detect quality regression.
        
        Args:
            request: Regression detection request
            
        Returns:
            Regression detection result
        """
        logger.info(
            f"Detecting regression for {request.model_name}:{request.config_hash}"
        )
        
        # Get baseline
        baseline = baseline_storage.get_by_model(
            request.model_name,
            request.config_hash
        )
        
        if not baseline:
            raise ValueError(
                f"No baseline found for {request.model_name}:{request.config_hash}"
            )
        
        # Calculate quality drop
        baseline_quality = baseline.metrics.average_quality
        current_quality = request.current_quality
        quality_drop = baseline_quality - current_quality
        quality_drop_percentage = (quality_drop / baseline_quality) * 100 if baseline_quality > 0 else 0
        
        # Calculate Z-score for anomaly detection
        z_score = None
        if baseline.metrics.std_dev_quality and baseline.metrics.std_dev_quality > 0:
            z_score = (current_quality - baseline_quality) / baseline.metrics.std_dev_quality
        
        # Determine if regression detected
        regression_detected = quality_drop_percentage > 5.0  # 5% threshold
        
        # Calculate regression score (0-100, higher = worse regression)
        regression_score = min(quality_drop_percentage * 10, 100) if regression_detected else 0
        
        # Determine severity
        severity = self._classify_severity(quality_drop_percentage)
        
        # Generate alert if regression detected
        alert = None
        if regression_detected:
            alert = self._generate_alert(
                severity=severity,
                quality_drop=quality_drop,
                quality_drop_percentage=quality_drop_percentage,
                baseline_quality=baseline_quality,
                current_quality=current_quality
            )
            self.alerts_history.append(alert)
        
        result = RegressionResult(
            regression_detected=regression_detected,
            regression_score=regression_score,
            severity=severity,
            quality_drop=quality_drop,
            quality_drop_percentage=quality_drop_percentage,
            baseline_quality=baseline_quality,
            current_quality=current_quality,
            z_score=z_score,
            alert=alert,
            details={
                "baseline_id": baseline.baseline_id,
                "baseline_sample_size": baseline.sample_size,
                "threshold_percentage": 5.0
            }
        )
        
        logger.info(
            f"Regression detection complete: detected={regression_detected}, "
            f"severity={severity}, drop={quality_drop_percentage:.2f}%"
        )
        
        return result
    
    def _classify_severity(self, drop_percentage: float) -> RegressionSeverity:
        """
        Classify regression severity.
        
        Args:
            drop_percentage: Quality drop percentage
            
        Returns:
            Regression severity
        """
        if drop_percentage < 5:
            return RegressionSeverity.NONE
        elif drop_percentage < 10:
            return RegressionSeverity.MINOR
        elif drop_percentage < 20:
            return RegressionSeverity.MODERATE
        elif drop_percentage < 30:
            return RegressionSeverity.SEVERE
        else:
            return RegressionSeverity.CRITICAL
    
    def _generate_alert(
        self,
        severity: RegressionSeverity,
        quality_drop: float,
        quality_drop_percentage: float,
        baseline_quality: float,
        current_quality: float
    ) -> RegressionAlert:
        """
        Generate regression alert.
        
        Args:
            severity: Regression severity
            quality_drop: Quality drop amount
            quality_drop_percentage: Quality drop percentage
            baseline_quality: Baseline quality
            current_quality: Current quality
            
        Returns:
            Regression alert
        """
        # Determine alert level
        if severity == RegressionSeverity.CRITICAL:
            level = AlertLevel.CRITICAL
        elif severity in [RegressionSeverity.SEVERE, RegressionSeverity.MODERATE]:
            level = AlertLevel.WARNING
        else:
            level = AlertLevel.INFO
        
        # Generate message
        message = (
            f"Quality regression detected: {severity.value.upper()} - "
            f"Quality dropped by {quality_drop_percentage:.1f}% "
            f"(from {baseline_quality:.1f} to {current_quality:.1f})"
        )
        
        alert = RegressionAlert(
            alert_id=str(uuid.uuid4()),
            level=level,
            message=message,
            severity=severity,
            quality_drop=quality_drop_percentage,
            baseline_quality=baseline_quality,
            current_quality=current_quality,
            metadata={
                "quality_drop_absolute": quality_drop
            }
        )
        
        logger.warning(f"Alert generated: {message}")
        
        return alert
    
    def get_alerts(
        self,
        limit: int = 100,
        level: Optional[AlertLevel] = None
    ) -> list:
        """
        Get recent alerts.
        
        Args:
            limit: Maximum number of alerts to return
            level: Filter by alert level
            
        Returns:
            List of alerts
        """
        alerts = self.alerts_history
        
        # Filter by level
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        # Sort by timestamp descending and limit
        alerts = sorted(alerts, key=lambda a: a.timestamp, reverse=True)[:limit]
        
        return alerts


# Global instance
regression_detector = RegressionDetector()
