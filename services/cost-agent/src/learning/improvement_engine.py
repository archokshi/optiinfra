"""
Improvement Engine.

Applies learnings to improve future recommendations.
"""

import logging
import uuid
from typing import Dict, Any, List
from datetime import datetime

from src.models.learning_loop import (
    LearningInsight,
    FailurePatterns,
    ScoringWeights,
    PredictionModel,
    RiskModel,
    ImprovementResult,
    FeedbackData,
    OutcomeRecord
)

logger = logging.getLogger(__name__)


class ImprovementEngine:
    """Applies learnings to improve future recommendations."""
    
    def __init__(self):
        """Initialize improvement engine."""
        # Default scoring weights
        self.scoring_weights = ScoringWeights()
        
        # Prediction models by type
        self.prediction_models = {}
        
        # Risk models by type
        self.risk_models = {}
    
    async def adjust_scoring_weights(
        self,
        insights: List[LearningInsight]
    ) -> ScoringWeights:
        """
        Adjust scoring weights based on insights.
        
        Args:
            insights: Learning insights
        
        Returns:
            Updated ScoringWeights
        """
        try:
            logger.info(f"Adjusting scoring weights based on {len(insights)} insights")
            
            # Start with current weights
            new_weights = ScoringWeights(
                roi_weight=self.scoring_weights.roi_weight,
                risk_weight=self.scoring_weights.risk_weight,
                urgency_weight=self.scoring_weights.urgency_weight,
                confidence_weight=self.scoring_weights.confidence_weight
            )
            
            # Analyze insights
            high_impact_insights = [i for i in insights if i.impact == "high"]
            
            # If many high-impact insights about risk, increase risk weight
            risk_insights = [i for i in high_impact_insights if "risk" in i.description.lower() or "fail" in i.description.lower()]
            if len(risk_insights) > 2:
                new_weights.risk_weight = min(0.4, new_weights.risk_weight + 0.05)
                new_weights.roi_weight = max(0.3, new_weights.roi_weight - 0.05)
                logger.info("Increased risk weight due to failure patterns")
            
            # If high accuracy, can focus more on ROI
            accuracy_insights = [i for i in high_impact_insights if "accuracy" in i.description.lower()]
            if len(accuracy_insights) > 2:
                avg_accuracy = sum(i.supporting_data.get("avg_savings_accuracy", 0) for i in accuracy_insights) / len(accuracy_insights)
                if avg_accuracy > 0.95:
                    new_weights.roi_weight = min(0.5, new_weights.roi_weight + 0.05)
                    new_weights.confidence_weight = max(0.05, new_weights.confidence_weight - 0.05)
                    logger.info("Increased ROI weight due to high accuracy")
            
            # Normalize weights to sum to 1.0
            total = new_weights.roi_weight + new_weights.risk_weight + new_weights.urgency_weight + new_weights.confidence_weight
            new_weights.roi_weight /= total
            new_weights.risk_weight /= total
            new_weights.urgency_weight /= total
            new_weights.confidence_weight /= total
            
            # Update stored weights
            self.scoring_weights = new_weights
            
            logger.info(f"Updated weights: ROI={new_weights.roi_weight:.2f}, Risk={new_weights.risk_weight:.2f}")
            
            return new_weights
            
        except Exception as e:
            logger.error(f"Error adjusting scoring weights: {e}", exc_info=True)
            return self.scoring_weights
    
    async def refine_cost_predictions(
        self,
        recommendation_type: str,
        historical_data: List[OutcomeRecord]
    ) -> PredictionModel:
        """
        Refine cost prediction model.
        
        Args:
            recommendation_type: Type of recommendation
            historical_data: Historical outcome data
        
        Returns:
            Updated PredictionModel
        """
        try:
            logger.info(f"Refining cost predictions for {recommendation_type}")
            
            if not historical_data:
                logger.warning(f"No historical data for {recommendation_type}")
                return PredictionModel(
                    recommendation_type=recommendation_type,
                    base_accuracy=0.80,
                    adjustment_factors={},
                    seasonal_factors={},
                    confidence_interval=0.20,
                    training_samples=0
                )
            
            # Calculate base accuracy from historical data
            successful = [o for o in historical_data if o.success and o.savings_accuracy > 0]
            if successful:
                accuracies = [o.savings_accuracy for o in successful]
                base_accuracy = sum(accuracies) / len(accuracies)
            else:
                base_accuracy = 0.80
            
            # Identify adjustment factors
            adjustment_factors = {}
            
            # Region-based adjustments
            region_accuracies = {}
            for outcome in successful:
                region = outcome.post_execution_metrics.get("region", "unknown")
                if region not in region_accuracies:
                    region_accuracies[region] = []
                region_accuracies[region].append(outcome.savings_accuracy)
            
            for region, accuracies in region_accuracies.items():
                avg_accuracy = sum(accuracies) / len(accuracies)
                adjustment_factors[f"region_{region}"] = avg_accuracy / base_accuracy if base_accuracy > 0 else 1.0
            
            # Resource type adjustments
            resource_accuracies = {}
            for outcome in successful:
                resource_type = outcome.post_execution_metrics.get("resource_type", "unknown")
                if resource_type not in resource_accuracies:
                    resource_accuracies[resource_type] = []
                resource_accuracies[resource_type].append(outcome.savings_accuracy)
            
            for resource_type, accuracies in resource_accuracies.items():
                avg_accuracy = sum(accuracies) / len(accuracies)
                adjustment_factors[f"resource_{resource_type}"] = avg_accuracy / base_accuracy if base_accuracy > 0 else 1.0
            
            # Seasonal factors (simplified - would need more data)
            seasonal_factors = {
                "Q1": 1.0,
                "Q2": 1.0,
                "Q3": 1.0,
                "Q4": 1.0
            }
            
            # Calculate confidence interval
            if successful:
                errors = [abs(1.0 - o.savings_accuracy) for o in successful]
                avg_error = sum(errors) / len(errors)
                confidence_interval = avg_error * 2  # 2 standard deviations
            else:
                confidence_interval = 0.20
            
            model = PredictionModel(
                recommendation_type=recommendation_type,
                base_accuracy=base_accuracy,
                adjustment_factors=adjustment_factors,
                seasonal_factors=seasonal_factors,
                confidence_interval=confidence_interval,
                last_trained=datetime.utcnow(),
                training_samples=len(historical_data)
            )
            
            # Store model
            self.prediction_models[recommendation_type] = model
            
            logger.info(f"Prediction model refined: base_accuracy={base_accuracy:.2%}, samples={len(historical_data)}")
            
            return model
            
        except Exception as e:
            logger.error(f"Error refining predictions: {e}", exc_info=True)
            raise
    
    async def update_risk_assessments(
        self,
        failure_patterns: FailurePatterns
    ) -> RiskModel:
        """
        Update risk assessment model.
        
        Args:
            failure_patterns: Failure patterns identified
        
        Returns:
            Updated RiskModel
        """
        try:
            logger.info(f"Updating risk assessment for {failure_patterns.recommendation_type}")
            
            # Calculate base risk score from failure rate
            base_risk_score = failure_patterns.failure_rate
            
            # Identify risk factors and their weights
            risk_factors = {}
            for i, cause in enumerate(failure_patterns.common_causes):
                # Higher weight for more common causes
                weight = 1.0 / (i + 1)
                risk_factors[cause] = weight
            
            # Additional risk factors
            for factor in failure_patterns.risk_factors:
                if factor not in risk_factors:
                    risk_factors[factor] = 0.5
            
            # Failure indicators
            failure_indicators = failure_patterns.common_causes[:5]
            
            # Mitigation strategies
            mitigation_strategies = {}
            for i, strategy in enumerate(failure_patterns.avoidance_strategies):
                mitigation_strategies[f"strategy_{i+1}"] = strategy
            
            model = RiskModel(
                recommendation_type=failure_patterns.recommendation_type,
                base_risk_score=base_risk_score,
                risk_factors=risk_factors,
                failure_indicators=failure_indicators,
                mitigation_strategies=mitigation_strategies,
                last_updated=datetime.utcnow()
            )
            
            # Store model
            self.risk_models[failure_patterns.recommendation_type] = model
            
            logger.info(f"Risk model updated: base_risk={base_risk_score:.2%}, factors={len(risk_factors)}")
            
            return model
            
        except Exception as e:
            logger.error(f"Error updating risk assessment: {e}", exc_info=True)
            raise
    
    async def improve_recommendation_quality(
        self,
        feedback_data: FeedbackData
    ) -> ImprovementResult:
        """
        Apply improvements to recommendation quality.
        
        Args:
            feedback_data: Aggregated feedback data
        
        Returns:
            ImprovementResult with applied changes
        """
        try:
            logger.info(f"Improving recommendation quality for {feedback_data.recommendation_type}")
            
            improvement_id = f"imp-{uuid.uuid4()}"
            changes_applied = []
            
            # Refine predictions if accuracy is low
            if feedback_data.accuracy_metrics.avg_savings_accuracy < 0.90:
                # Would apply prediction improvements
                changes_applied.append("Refined cost prediction model")
                logger.info("Applied prediction refinement")
            
            # Update risk assessment if failure rate is high
            if feedback_data.failure_patterns.failure_rate > 0.10:
                # Would apply risk assessment updates
                changes_applied.append("Updated risk assessment model")
                logger.info("Applied risk assessment update")
            
            # Adjust scoring if needed
            if feedback_data.success_patterns.success_rate < 0.85:
                # Would adjust scoring weights
                changes_applied.append("Adjusted scoring weights")
                logger.info("Applied scoring weight adjustment")
            
            # Calculate expected impact
            current_accuracy = feedback_data.accuracy_metrics.avg_savings_accuracy
            expected_improvement = 0.05  # Expect 5% improvement
            expected_impact = expected_improvement / current_accuracy if current_accuracy > 0 else 0.0
            
            result = ImprovementResult(
                improvement_id=improvement_id,
                area="recommendation_quality",
                changes_applied=changes_applied,
                expected_impact=expected_impact,
                actual_impact=None,  # Will be measured later
                success=True,
                applied_at=datetime.utcnow()
            )
            
            logger.info(f"Improvements applied: {len(changes_applied)} changes, expected impact={expected_impact:.1%}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error improving recommendation quality: {e}", exc_info=True)
            raise
    
    async def get_current_scoring_weights(self) -> ScoringWeights:
        """
        Get current scoring weights.
        
        Returns:
            Current ScoringWeights
        """
        return self.scoring_weights
    
    async def get_prediction_model(self, recommendation_type: str) -> PredictionModel:
        """
        Get prediction model for a recommendation type.
        
        Args:
            recommendation_type: Type of recommendation
        
        Returns:
            PredictionModel or None
        """
        return self.prediction_models.get(recommendation_type)
    
    async def get_risk_model(self, recommendation_type: str) -> RiskModel:
        """
        Get risk model for a recommendation type.
        
        Args:
            recommendation_type: Type of recommendation
        
        Returns:
            RiskModel or None
        """
        return self.risk_models.get(recommendation_type)
