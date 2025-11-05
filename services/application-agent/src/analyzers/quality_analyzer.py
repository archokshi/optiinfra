"""
Quality Analyzer

Analyzes quality metrics and provides insights.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from ..models.quality_metrics import QualityMetrics, QualityTrend
from ..core.logger import logger


class QualityAnalyzer:
    """Analyzes quality metrics."""
    
    def __init__(self):
        """Initialize quality analyzer."""
        self.metrics_history: List[QualityMetrics] = []
    
    def add_metrics(self, metrics: QualityMetrics):
        """
        Add metrics to history.
        
        Args:
            metrics: Quality metrics to add
        """
        self.metrics_history.append(metrics)
        
        # Keep only last 1000 metrics
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
    
    def get_quality_trend(self, time_period: str = "1h") -> QualityTrend:
        """
        Get quality trend for a time period.
        
        Args:
            time_period: Time period (e.g., '1h', '24h', '7d')
            
        Returns:
            Quality trend
        """
        # Parse time period
        period_hours = self._parse_time_period(time_period)
        cutoff_time = datetime.utcnow() - timedelta(hours=period_hours)
        
        # Filter metrics
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp >= cutoff_time
        ]
        
        if not recent_metrics:
            return QualityTrend(
                time_period=time_period,
                average_quality=0.0,
                min_quality=0.0,
                max_quality=0.0,
                total_requests=0,
                quality_distribution={}
            )
        
        # Calculate statistics
        qualities = [m.overall_quality for m in recent_metrics]
        
        # Grade distribution
        distribution = {}
        for m in recent_metrics:
            grade = m.quality_grade
            distribution[grade] = distribution.get(grade, 0) + 1
        
        return QualityTrend(
            time_period=time_period,
            average_quality=sum(qualities) / len(qualities),
            min_quality=min(qualities),
            max_quality=max(qualities),
            total_requests=len(recent_metrics),
            quality_distribution=distribution
        )
    
    def get_quality_insights(self) -> Dict[str, Any]:
        """
        Get quality insights.
        
        Returns:
            Quality insights
        """
        if not self.metrics_history:
            return {
                "status": "no_data",
                "message": "No quality metrics available"
            }
        
        recent = self.metrics_history[-100:]  # Last 100 requests
        
        # Calculate averages
        avg_quality = sum(m.overall_quality for m in recent) / len(recent)
        avg_relevance = sum(m.relevance.score for m in recent) / len(recent)
        avg_coherence = sum(m.coherence.score for m in recent) / len(recent)
        avg_hallucination = sum(m.hallucination.hallucination_rate for m in recent) / len(recent)
        
        # Identify issues
        issues = []
        if avg_quality < 70:
            issues.append("Overall quality below acceptable threshold (70%)")
        if avg_relevance < 70:
            issues.append("Relevance scores are low")
        if avg_coherence < 70:
            issues.append("Coherence scores are low")
        if avg_hallucination > 30:
            issues.append("High hallucination rate detected")
        
        return {
            "status": "ok" if not issues else "warning",
            "average_quality": round(avg_quality, 2),
            "average_relevance": round(avg_relevance, 2),
            "average_coherence": round(avg_coherence, 2),
            "average_hallucination": round(avg_hallucination, 2),
            "total_analyzed": len(recent),
            "issues": issues,
            "recommendation": self._generate_recommendation(avg_quality, avg_relevance, avg_coherence, avg_hallucination)
        }
    
    def _parse_time_period(self, period: str) -> float:
        """Parse time period string to hours."""
        if period.endswith('h'):
            return float(period[:-1])
        elif period.endswith('d'):
            return float(period[:-1]) * 24
        elif period.endswith('w'):
            return float(period[:-1]) * 24 * 7
        else:
            return 1.0  # Default to 1 hour
    
    def _generate_recommendation(
        self,
        quality: float,
        relevance: float,
        coherence: float,
        hallucination: float
    ) -> str:
        """Generate recommendation based on metrics."""
        if quality >= 85:
            return "Quality is excellent. Continue monitoring."
        elif quality >= 70:
            return "Quality is acceptable but could be improved."
        else:
            if relevance < 70:
                return "Focus on improving response relevance to prompts."
            elif coherence < 70:
                return "Focus on improving response coherence and structure."
            elif hallucination > 30:
                return "High hallucination rate detected. Review model configuration."
            else:
                return "Multiple quality issues detected. Comprehensive review needed."


# Global instance
quality_analyzer = QualityAnalyzer()
