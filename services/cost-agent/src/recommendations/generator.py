"""
Recommendation Generator Module.

Generates cost optimization recommendations from analysis results,
historical data, and detected patterns.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RecommendationGenerator:
    """Generates cost optimization recommendations."""
    
    def __init__(self):
        """Initialize recommendation generator."""
        pass
    
    def generate_recommendations(
        self,
        analysis_report: Dict[str, Any],
        historical_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations from analysis report.
        
        Args:
            analysis_report: Analysis engine output
            historical_data: Historical cost and usage data
        
        Returns:
            List of recommendations
        """
        recommendations = []
        
        try:
            # Generate from idle resources
            if "idle_resources" in analysis_report:
                idle_recs = self.generate_from_idle_resources(
                    analysis_report["idle_resources"]
                )
                recommendations.extend(idle_recs)
                logger.info(f"Generated {len(idle_recs)} recommendations from idle resources")
            
            # Generate from anomalies
            if "anomalies" in analysis_report:
                anomaly_recs = self.generate_from_anomalies(
                    analysis_report["anomalies"]
                )
                recommendations.extend(anomaly_recs)
                logger.info(f"Generated {len(anomaly_recs)} recommendations from anomalies")
            
            # Generate from trends (if historical data available)
            if historical_data and "cost_history" in historical_data:
                trend_recs = self.generate_from_trends(
                    historical_data["cost_history"]
                )
                recommendations.extend(trend_recs)
                logger.info(f"Generated {len(trend_recs)} recommendations from trends")
            
            # Consolidate recommendations
            consolidated = self.consolidate_recommendations(recommendations)
            
            logger.info(f"Generated {len(consolidated)} total recommendations")
            return consolidated
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}", exc_info=True)
            return []
    
    def generate_from_idle_resources(
        self,
        idle_resources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations from idle resources."""
        recommendations = []
        
        for resource in idle_resources:
            severity = resource.get("idle_severity", "low")
            monthly_savings = resource.get("monthly_waste", 0)
            
            rec = {
                "recommendation_id": str(uuid.uuid4()),
                "recommendation_type": "terminate" if severity in ["critical", "high"] else "right_size",
                "resource_id": resource.get("resource_id"),
                "resource_type": resource.get("resource_type"),
                "region": resource.get("region", "unknown"),
                "title": f"Optimize idle {resource.get('resource_type')}",
                "description": f"Resource idle for {resource.get('idle_duration_days', 0)} days",
                "rationale": f"CPU: {resource.get('cpu_avg', 0):.1f}%, Memory: {resource.get('memory_avg', 0):.1f}%",
                "monthly_savings": monthly_savings,
                "annual_savings": monthly_savings * 12,
                "implementation_cost": 0.0 if severity in ["critical", "high"] else 100.0,
                "payback_period_days": 0 if severity in ["critical", "high"] else 10,
                "risk_level": "low" if severity in ["critical", "high"] else "medium",
                "risk_factors": ["Verify no dependencies"],
                "rollback_plan": "Restore from backup",
                "implementation_steps": ["Verify idle", "Backup", "Terminate or resize"],
                "estimated_time_minutes": 15,
                "requires_approval": True,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(days=30),
                "source": "idle_detection",
                "confidence": 0.90
            }
            recommendations.append(rec)
        
        return recommendations
    
    def generate_from_anomalies(
        self,
        anomalies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations from anomalies."""
        recommendations = []
        
        for anomaly in anomalies:
            rec = {
                "recommendation_id": str(uuid.uuid4()),
                "recommendation_type": "investigate",
                "resource_id": anomaly.get("resource_id"),
                "resource_type": anomaly.get("resource_type"),
                "region": anomaly.get("region", "unknown"),
                "title": f"Investigate {anomaly.get('anomaly_type')} anomaly",
                "description": anomaly.get("description", "Anomaly detected"),
                "rationale": f"Deviation: {anomaly.get('deviation_percent', 0):.1f}%",
                "monthly_savings": 0.0,
                "annual_savings": 0.0,
                "implementation_cost": 0.0,
                "payback_period_days": 0,
                "risk_level": "low",
                "risk_factors": [],
                "rollback_plan": "N/A",
                "implementation_steps": ["Investigate", "Analyze", "Take action"],
                "estimated_time_minutes": 30,
                "requires_approval": False,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(days=7),
                "source": "anomaly_detection",
                "confidence": 0.85
            }
            recommendations.append(rec)
        
        return recommendations
    
    def generate_from_trends(
        self,
        cost_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations from cost trends."""
        recommendations = []
        
        if len(cost_history) < 7:
            return recommendations
        
        # Analyze variance for spot/RI recommendations
        costs = [entry.get("cost", 0) for entry in cost_history]
        avg_cost = sum(costs) / len(costs)
        variance = sum((c - avg_cost) ** 2 for c in costs) / len(costs)
        std_dev = variance ** 0.5
        cv = (std_dev / avg_cost) if avg_cost > 0 else 0
        
        # Low variance -> Spot candidate
        if cv < 0.2:
            rec = {
                "recommendation_id": str(uuid.uuid4()),
                "recommendation_type": "spot",
                "resource_id": None,
                "resource_type": "ec2",
                "region": "all",
                "title": "Migrate to spot instances",
                "description": "Steady workload detected",
                "rationale": "Low variance indicates predictable workload",
                "monthly_savings": avg_cost * 0.7,
                "annual_savings": avg_cost * 0.7 * 12,
                "implementation_cost": 500.0,
                "payback_period_days": 15,
                "risk_level": "medium",
                "risk_factors": ["Potential interruptions"],
                "rollback_plan": "Switch to on-demand",
                "implementation_steps": ["Configure spot", "Test", "Migrate"],
                "estimated_time_minutes": 240,
                "requires_approval": True,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(days=60),
                "source": "trend_analysis",
                "confidence": 0.80
            }
            recommendations.append(rec)
        
        return recommendations
    
    def consolidate_recommendations(
        self,
        recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Consolidate and deduplicate recommendations."""
        if not recommendations:
            return []
        
        # Remove duplicates by resource_id + type
        seen = set()
        unique = []
        
        for rec in recommendations:
            key = (rec.get("resource_id", ""), rec.get("recommendation_type", ""))
            if key not in seen:
                seen.add(key)
                unique.append(rec)
        
        # Filter by minimum savings
        filtered = [r for r in unique if r.get("monthly_savings", 0) >= 10.0 or r.get("recommendation_type") in ["investigate", "security_fix"]]
        
        return filtered
