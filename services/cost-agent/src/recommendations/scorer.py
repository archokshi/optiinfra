"""
Recommendation Scorer Module.

Scores and prioritizes recommendations based on ROI, risk, urgency, and business impact.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RecommendationScorer:
    """Scores and prioritizes recommendations."""
    
    def __init__(self):
        """Initialize recommendation scorer."""
        self.default_weights = {
            "roi": 0.40,
            "risk": 0.20,
            "urgency": 0.25,
            "impact": 0.15
        }
    
    def score_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        context: Dict[str, Any],
        weights: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Score and prioritize recommendations.
        
        Args:
            recommendations: List of recommendations to score
            context: Business context for scoring
            weights: Custom scoring weights (optional)
        
        Returns:
            List of scored recommendations with priority scores
        """
        if not recommendations:
            return []
        
        # Use custom weights or defaults
        scoring_weights = weights or self.default_weights
        
        scored_recommendations = []
        
        for rec in recommendations:
            try:
                # Calculate individual scores
                roi_score = self.calculate_roi_score(rec)
                risk_score = self.calculate_risk_score(rec)
                urgency_score = self.calculate_urgency_score(rec)
                impact_score = self.calculate_business_impact_score(rec, context)
                
                # Calculate final priority score
                priority_score = self.compute_priority_score(
                    roi_score, risk_score, urgency_score, impact_score, scoring_weights
                )
                
                # Categorize recommendation
                category = self._categorize_recommendation(
                    roi_score, risk_score, priority_score
                )
                
                scored_rec = {
                    "recommendation": rec,
                    "roi_score": roi_score,
                    "risk_score": risk_score,
                    "urgency_score": urgency_score,
                    "business_impact_score": impact_score,
                    "priority_score": priority_score,
                    "rank": 0,  # Will be set after sorting
                    "category": category,
                    "scoring_context": {
                        "weights": scoring_weights,
                        "scored_at": datetime.utcnow()
                    }
                }
                
                scored_recommendations.append(scored_rec)
                
            except Exception as e:
                logger.error(f"Error scoring recommendation {rec.get('recommendation_id')}: {e}")
                continue
        
        # Sort by priority score (descending)
        scored_recommendations.sort(key=lambda x: x["priority_score"], reverse=True)
        
        # Assign ranks
        for i, scored_rec in enumerate(scored_recommendations, 1):
            scored_rec["rank"] = i
        
        logger.info(f"Scored {len(scored_recommendations)} recommendations")
        
        return scored_recommendations
    
    def calculate_roi_score(self, recommendation: Dict[str, Any]) -> float:
        """
        Calculate ROI score (0-100).
        
        ROI = (Annual Savings - Implementation Cost) / Implementation Cost
        Normalized to 0-100 scale.
        """
        annual_savings = recommendation.get("annual_savings", 0)
        implementation_cost = recommendation.get("implementation_cost", 0)
        confidence = recommendation.get("confidence", 0.8)
        
        # Handle zero implementation cost (infinite ROI)
        if implementation_cost == 0:
            if annual_savings > 0:
                roi_score = 100.0
            else:
                roi_score = 0.0
        else:
            # Calculate ROI percentage
            roi = ((annual_savings - implementation_cost) / implementation_cost) * 100
            
            # Normalize to 0-100 scale
            # ROI > 300% = 100 points
            # ROI = 0% = 50 points
            # ROI < 0% = 0 points
            if roi >= 300:
                roi_score = 100.0
            elif roi >= 0:
                roi_score = 50.0 + (roi / 300) * 50
            else:
                roi_score = max(0, 50 + (roi / 100) * 50)
        
        # Adjust by confidence
        roi_score = roi_score * confidence
        
        return min(100.0, max(0.0, roi_score))
    
    def calculate_risk_score(self, recommendation: Dict[str, Any]) -> float:
        """
        Calculate risk score (0-100, where 0 = high risk, 100 = low risk).
        
        Based on risk level, complexity, and potential impact.
        """
        risk_level = recommendation.get("risk_level", "medium")
        estimated_time = recommendation.get("estimated_time_minutes", 60)
        requires_approval = recommendation.get("requires_approval", True)
        risk_factors = recommendation.get("risk_factors", [])
        
        # Base risk score by level
        base_risk = {
            "low": 90.0,
            "medium": 60.0,
            "high": 30.0
        }.get(risk_level, 60.0)
        
        # Adjust for complexity (time required)
        if estimated_time > 240:  # > 4 hours
            complexity_penalty = -15.0
        elif estimated_time > 120:  # > 2 hours
            complexity_penalty = -10.0
        elif estimated_time > 60:  # > 1 hour
            complexity_penalty = -5.0
        else:
            complexity_penalty = 0.0
        
        # Adjust for approval requirement
        approval_penalty = -5.0 if requires_approval else 0.0
        
        # Adjust for number of risk factors
        risk_factor_penalty = -2.0 * len(risk_factors)
        
        risk_score = base_risk + complexity_penalty + approval_penalty + risk_factor_penalty
        
        return min(100.0, max(0.0, risk_score))
    
    def calculate_urgency_score(self, recommendation: Dict[str, Any]) -> float:
        """
        Calculate urgency score (0-100).
        
        Based on cost impact, security impact, and time sensitivity.
        """
        monthly_savings = recommendation.get("monthly_savings", 0)
        rec_type = recommendation.get("recommendation_type", "")
        source = recommendation.get("source", "")
        expires_at = recommendation.get("expires_at")
        
        # Base urgency by savings amount
        if monthly_savings >= 1000:
            savings_urgency = 90.0
        elif monthly_savings >= 500:
            savings_urgency = 75.0
        elif monthly_savings >= 100:
            savings_urgency = 60.0
        elif monthly_savings >= 50:
            savings_urgency = 45.0
        else:
            savings_urgency = 30.0
        
        # Boost for security/compliance issues
        if rec_type in ["security_fix", "config_fix"]:
            type_boost = 30.0
        elif rec_type == "terminate":
            type_boost = 20.0
        elif source == "anomaly_detection":
            type_boost = 15.0
        else:
            type_boost = 0.0
        
        # Boost for expiring recommendations
        time_boost = 0.0
        if expires_at:
            try:
                from datetime import datetime
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at)
                days_until_expiry = (expires_at - datetime.utcnow()).days
                if days_until_expiry <= 3:
                    time_boost = 20.0
                elif days_until_expiry <= 7:
                    time_boost = 10.0
            except:
                pass
        
        urgency_score = savings_urgency + type_boost + time_boost
        
        return min(100.0, max(0.0, urgency_score))
    
    def calculate_business_impact_score(
        self,
        recommendation: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        """
        Calculate business impact score (0-100).
        
        Based on affected services, user impact, and business criticality.
        """
        rec_type = recommendation.get("recommendation_type", "")
        resource_type = recommendation.get("resource_type", "")
        monthly_savings = recommendation.get("monthly_savings", 0)
        
        # Base impact by recommendation type
        type_impact = {
            "terminate": 70.0,  # High impact - removes resource
            "spot": 60.0,  # Medium-high - changes availability model
            "ri": 80.0,  # High - long-term commitment
            "right_size": 50.0,  # Medium - changes capacity
            "hibernate": 40.0,  # Medium-low - temporary unavailability
            "auto_scale": 65.0,  # Medium-high - changes scaling behavior
            "security_fix": 90.0,  # Very high - security impact
            "config_fix": 60.0,  # Medium-high - changes configuration
            "storage_optimize": 40.0,  # Medium-low - storage changes
            "investigate": 30.0  # Low - just investigation
        }.get(rec_type, 50.0)
        
        # Adjust by resource type criticality (from context if available)
        resource_criticality = context.get("resource_criticality", {}).get(resource_type, 1.0)
        type_impact = type_impact * resource_criticality
        
        # Adjust by savings amount (higher savings = higher impact)
        if monthly_savings >= 1000:
            savings_boost = 20.0
        elif monthly_savings >= 500:
            savings_boost = 10.0
        elif monthly_savings >= 100:
            savings_boost = 5.0
        else:
            savings_boost = 0.0
        
        impact_score = type_impact + savings_boost
        
        return min(100.0, max(0.0, impact_score))
    
    def compute_priority_score(
        self,
        roi_score: float,
        risk_score: float,
        urgency_score: float,
        impact_score: float,
        weights: Dict[str, float]
    ) -> float:
        """
        Compute final priority score using weighted combination.
        
        Args:
            roi_score: ROI score (0-100)
            risk_score: Risk score (0-100, higher = lower risk)
            urgency_score: Urgency score (0-100)
            impact_score: Business impact score (0-100)
            weights: Scoring weights
        
        Returns:
            Priority score (0-100)
        """
        priority_score = (
            roi_score * weights.get("roi", 0.40) +
            risk_score * weights.get("risk", 0.20) +
            urgency_score * weights.get("urgency", 0.25) +
            impact_score * weights.get("impact", 0.15)
        )
        
        return min(100.0, max(0.0, priority_score))
    
    def _categorize_recommendation(
        self,
        roi_score: float,
        risk_score: float,
        priority_score: float
    ) -> str:
        """
        Categorize recommendation into quick_win, strategic, or long_term.
        
        Args:
            roi_score: ROI score
            risk_score: Risk score (higher = lower risk)
            priority_score: Overall priority score
        
        Returns:
            Category: "quick_win", "strategic", or "long_term"
        """
        # Quick wins: High ROI, Low Risk, High Priority
        if roi_score >= 70 and risk_score >= 70 and priority_score >= 75:
            return "quick_win"
        
        # Strategic: High ROI or High Priority, Medium-High Risk acceptable
        elif (roi_score >= 60 or priority_score >= 65) and risk_score >= 40:
            return "strategic"
        
        # Long-term: Lower ROI or Priority, or Higher Risk
        else:
            return "long_term"
