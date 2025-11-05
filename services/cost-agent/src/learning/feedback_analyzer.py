"""
Feedback Analyzer.

Analyzes feedback to identify patterns and insights.
"""

import logging
import uuid
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict

from src.learning.outcome_tracker import OutcomeTracker
from src.learning.knowledge_store import KnowledgeStore
from src.models.learning_loop import (
    SuccessPatterns,
    FailurePatterns,
    AccuracyMetrics,
    LearningInsight,
    ImprovementOpportunity
)

logger = logging.getLogger(__name__)


class FeedbackAnalyzer:
    """Analyzes feedback to identify patterns and insights."""
    
    def __init__(
        self,
        outcome_tracker: OutcomeTracker = None,
        knowledge_store: KnowledgeStore = None
    ):
        """
        Initialize feedback analyzer.
        
        Args:
            outcome_tracker: Outcome tracker instance
            knowledge_store: Knowledge store instance
        """
        self.outcome_tracker = outcome_tracker or OutcomeTracker()
        self.knowledge_store = knowledge_store or KnowledgeStore()
    
    async def analyze_success_patterns(
        self,
        recommendation_type: str,
        lookback_days: int = 90
    ) -> SuccessPatterns:
        """
        Analyze success patterns for a recommendation type.
        
        Args:
            recommendation_type: Type of recommendation
            lookback_days: Number of days to analyze
        
        Returns:
            SuccessPatterns with identified patterns
        """
        try:
            logger.info(f"Analyzing success patterns for {recommendation_type}")
            
            # Get recent outcomes
            outcomes = await self.outcome_tracker.get_recent_outcomes(days=lookback_days)
            
            # Filter by type and success
            type_outcomes = [o for o in outcomes if o.recommendation_type == recommendation_type]
            successful = [o for o in type_outcomes if o.success]
            
            if not type_outcomes:
                return SuccessPatterns(
                    recommendation_type=recommendation_type,
                    success_rate=0.0,
                    total_cases=0,
                    common_characteristics=[],
                    optimal_conditions={},
                    best_practices=[],
                    avg_savings_accuracy=0.0,
                    confidence=0.0
                )
            
            # Calculate success rate
            success_rate = len(successful) / len(type_outcomes)
            
            # Analyze common characteristics
            characteristics = self._identify_common_characteristics(successful)
            
            # Identify optimal conditions
            optimal_conditions = self._identify_optimal_conditions(successful)
            
            # Extract best practices
            best_practices = self._extract_best_practices(successful, recommendation_type)
            
            # Calculate average savings accuracy
            valid_savings = [o.savings_accuracy for o in successful if o.savings_accuracy > 0]
            avg_savings_accuracy = sum(valid_savings) / len(valid_savings) if valid_savings else 0.0
            
            # Calculate confidence based on sample size
            confidence = min(len(type_outcomes) / 100.0, 1.0)  # Max confidence at 100+ samples
            
            patterns = SuccessPatterns(
                recommendation_type=recommendation_type,
                success_rate=success_rate,
                total_cases=len(type_outcomes),
                common_characteristics=characteristics,
                optimal_conditions=optimal_conditions,
                best_practices=best_practices,
                avg_savings_accuracy=avg_savings_accuracy,
                confidence=confidence
            )
            
            logger.info(f"Success patterns identified: {success_rate:.1%} success rate, {len(characteristics)} characteristics")
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing success patterns: {e}", exc_info=True)
            raise
    
    async def analyze_failure_patterns(
        self,
        recommendation_type: str,
        lookback_days: int = 90
    ) -> FailurePatterns:
        """
        Analyze failure patterns for a recommendation type.
        
        Args:
            recommendation_type: Type of recommendation
            lookback_days: Number of days to analyze
        
        Returns:
            FailurePatterns with identified patterns
        """
        try:
            logger.info(f"Analyzing failure patterns for {recommendation_type}")
            
            # Get recent outcomes
            outcomes = await self.outcome_tracker.get_recent_outcomes(days=lookback_days)
            
            # Filter by type and failure
            type_outcomes = [o for o in outcomes if o.recommendation_type == recommendation_type]
            failed = [o for o in type_outcomes if not o.success]
            
            if not type_outcomes:
                return FailurePatterns(
                    recommendation_type=recommendation_type,
                    failure_rate=0.0,
                    total_cases=0,
                    common_causes=[],
                    risk_factors=[],
                    avoidance_strategies=[],
                    avg_execution_duration=0.0,
                    confidence=0.0
                )
            
            # Calculate failure rate
            failure_rate = len(failed) / len(type_outcomes)
            
            # Analyze common causes
            common_causes = self._identify_failure_causes(failed)
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(failed)
            
            # Generate avoidance strategies
            avoidance_strategies = self._generate_avoidance_strategies(failed, recommendation_type)
            
            # Calculate average execution duration
            durations = [o.execution_duration_seconds for o in failed if o.execution_duration_seconds > 0]
            avg_duration = sum(durations) / len(durations) if durations else 0.0
            
            # Calculate confidence
            confidence = min(len(type_outcomes) / 100.0, 1.0)
            
            patterns = FailurePatterns(
                recommendation_type=recommendation_type,
                failure_rate=failure_rate,
                total_cases=len(type_outcomes),
                common_causes=common_causes,
                risk_factors=risk_factors,
                avoidance_strategies=avoidance_strategies,
                avg_execution_duration=avg_duration,
                confidence=confidence
            )
            
            logger.info(f"Failure patterns identified: {failure_rate:.1%} failure rate, {len(common_causes)} causes")
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing failure patterns: {e}", exc_info=True)
            raise
    
    async def calculate_accuracy_metrics(
        self,
        recommendation_type: str = None
    ) -> AccuracyMetrics:
        """
        Calculate accuracy metrics.
        
        Args:
            recommendation_type: Type to filter by (None for all)
        
        Returns:
            AccuracyMetrics with accuracy data
        """
        try:
            logger.info(f"Calculating accuracy metrics for {recommendation_type or 'all types'}")
            
            # Get recent outcomes (30 days)
            outcomes = await self.outcome_tracker.get_recent_outcomes(days=30)
            
            # Filter by type if specified
            if recommendation_type:
                outcomes = [o for o in outcomes if o.recommendation_type == recommendation_type]
            
            if not outcomes:
                return AccuracyMetrics(
                    recommendation_type=recommendation_type,
                    total_executions=0,
                    successful_executions=0,
                    success_rate=0.0,
                    avg_savings_accuracy=0.0,
                    avg_prediction_error=0.0,
                    roi_accuracy=0.0,
                    improvement_over_baseline=0.0,
                    measurement_period_days=30
                )
            
            # Calculate metrics
            total_executions = len(outcomes)
            successful = [o for o in outcomes if o.success]
            successful_executions = len(successful)
            success_rate = successful_executions / total_executions
            
            # Savings accuracy (only for successful executions)
            valid_savings = [o.savings_accuracy for o in successful if o.savings_accuracy > 0]
            avg_savings_accuracy = sum(valid_savings) / len(valid_savings) if valid_savings else 0.0
            
            # Prediction error
            errors = [abs(1.0 - o.savings_accuracy) for o in successful if o.savings_accuracy > 0]
            avg_prediction_error = sum(errors) / len(errors) if errors else 0.0
            
            # ROI accuracy (simplified)
            roi_accuracy = avg_savings_accuracy
            
            # Improvement over baseline (assume baseline is 80% accuracy)
            baseline_accuracy = 0.80
            improvement = (avg_savings_accuracy - baseline_accuracy) / baseline_accuracy if baseline_accuracy > 0 else 0.0
            
            metrics = AccuracyMetrics(
                recommendation_type=recommendation_type,
                total_executions=total_executions,
                successful_executions=successful_executions,
                success_rate=success_rate,
                avg_savings_accuracy=avg_savings_accuracy,
                avg_prediction_error=avg_prediction_error,
                roi_accuracy=roi_accuracy,
                improvement_over_baseline=improvement,
                measurement_period_days=30
            )
            
            logger.info(f"Accuracy metrics: {success_rate:.1%} success, {avg_savings_accuracy:.1%} accuracy")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating accuracy metrics: {e}", exc_info=True)
            raise
    
    async def identify_improvement_opportunities(
        self
    ) -> List[ImprovementOpportunity]:
        """
        Identify improvement opportunities.
        
        Returns:
            List of improvement opportunities
        """
        try:
            logger.info("Identifying improvement opportunities")
            
            opportunities = []
            
            # Get metrics for each recommendation type
            rec_types = ["terminate", "right_size", "hibernate", "spot", "ri", "auto_scale"]
            
            for rec_type in rec_types:
                metrics = await self.calculate_accuracy_metrics(rec_type)
                
                if metrics.total_executions < 5:
                    continue  # Not enough data
                
                # Check for low success rate
                if metrics.success_rate < 0.90:
                    opportunities.append(ImprovementOpportunity(
                        opportunity_id=f"opp-{uuid.uuid4()}",
                        area="execution_reliability",
                        current_performance=metrics.success_rate,
                        potential_improvement=0.95 - metrics.success_rate,
                        suggested_actions=[
                            f"Analyze failure patterns for {rec_type}",
                            "Improve pre-execution validation",
                            "Add more safety checks"
                        ],
                        estimated_impact="high",
                        priority=1
                    ))
                
                # Check for low prediction accuracy
                if metrics.avg_savings_accuracy < 0.85:
                    opportunities.append(ImprovementOpportunity(
                        opportunity_id=f"opp-{uuid.uuid4()}",
                        area="prediction_accuracy",
                        current_performance=metrics.avg_savings_accuracy,
                        potential_improvement=0.95 - metrics.avg_savings_accuracy,
                        suggested_actions=[
                            f"Refine cost prediction model for {rec_type}",
                            "Incorporate more historical data",
                            "Adjust for seasonal patterns"
                        ],
                        estimated_impact="medium",
                        priority=2
                    ))
            
            logger.info(f"Identified {len(opportunities)} improvement opportunities")
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error identifying opportunities: {e}", exc_info=True)
            return []
    
    async def generate_learning_insights(
        self,
        lookback_days: int = 30
    ) -> List[LearningInsight]:
        """
        Generate learning insights.
        
        Args:
            lookback_days: Number of days to analyze
        
        Returns:
            List of learning insights
        """
        try:
            logger.info(f"Generating learning insights for last {lookback_days} days")
            
            insights = []
            
            # Analyze each recommendation type
            rec_types = ["terminate", "right_size", "hibernate", "spot"]
            
            for rec_type in rec_types:
                # Success patterns
                success_patterns = await self.analyze_success_patterns(rec_type, lookback_days)
                
                if success_patterns.total_cases >= 5:
                    insights.append(LearningInsight(
                        insight_id=f"insight-{uuid.uuid4()}",
                        insight_type="success_pattern",
                        description=f"{rec_type} recommendations have {success_patterns.success_rate:.1%} success rate with {success_patterns.avg_savings_accuracy:.1%} savings accuracy",
                        confidence=success_patterns.confidence,
                        impact="high" if success_patterns.success_rate > 0.90 else "medium",
                        actionable_recommendations=success_patterns.best_practices[:3],
                        supporting_data={
                            "success_rate": success_patterns.success_rate,
                            "total_cases": success_patterns.total_cases,
                            "avg_savings_accuracy": success_patterns.avg_savings_accuracy
                        }
                    ))
                
                # Failure patterns
                failure_patterns = await self.analyze_failure_patterns(rec_type, lookback_days)
                
                if failure_patterns.failure_rate > 0.10:  # More than 10% failure
                    insights.append(LearningInsight(
                        insight_id=f"insight-{uuid.uuid4()}",
                        insight_type="failure_pattern",
                        description=f"{rec_type} recommendations have {failure_patterns.failure_rate:.1%} failure rate",
                        confidence=failure_patterns.confidence,
                        impact="high",
                        actionable_recommendations=failure_patterns.avoidance_strategies[:3],
                        supporting_data={
                            "failure_rate": failure_patterns.failure_rate,
                            "common_causes": failure_patterns.common_causes
                        }
                    ))
            
            logger.info(f"Generated {len(insights)} learning insights")
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}", exc_info=True)
            return []
    
    # Private helper methods
    
    def _identify_common_characteristics(self, outcomes: List) -> List[str]:
        """Identify common characteristics in successful outcomes."""
        characteristics = []
        
        if not outcomes:
            return characteristics
        
        # Analyze regions
        regions = defaultdict(int)
        for o in outcomes:
            region = o.post_execution_metrics.get("region", "unknown")
            regions[region] += 1
        
        if regions:
            most_common_region = max(regions, key=regions.get)
            if regions[most_common_region] / len(outcomes) > 0.6:
                characteristics.append(f"Most successful in {most_common_region} region")
        
        # Analyze savings range
        savings = [o.actual_savings for o in outcomes if o.actual_savings]
        if savings:
            avg_savings = sum(savings) / len(savings)
            characteristics.append(f"Average savings: ${avg_savings:.2f}/month")
        
        # Analyze execution duration
        durations = [o.execution_duration_seconds for o in outcomes]
        if durations:
            avg_duration = sum(durations) / len(durations)
            characteristics.append(f"Average execution time: {avg_duration:.0f}s")
        
        return characteristics
    
    def _identify_optimal_conditions(self, outcomes: List) -> Dict[str, Any]:
        """Identify optimal conditions for success."""
        conditions = {}
        
        if not outcomes:
            return conditions
        
        # Optimal time of day (mock)
        conditions["preferred_execution_time"] = "off-peak hours"
        
        # Optimal resource state
        conditions["resource_state"] = "stopped or idle"
        
        return conditions
    
    def _extract_best_practices(self, outcomes: List, rec_type: str) -> List[str]:
        """Extract best practices from successful outcomes."""
        practices = []
        
        if rec_type == "terminate":
            practices.append("Always create backup before termination")
            practices.append("Verify resource is truly idle for 7+ days")
            practices.append("Check for dependencies before terminating")
        elif rec_type == "right_size":
            practices.append("Monitor performance for 7 days before resizing")
            practices.append("Resize during maintenance window")
            practices.append("Keep one size smaller for safety margin")
        
        return practices
    
    def _identify_failure_causes(self, outcomes: List) -> List[str]:
        """Identify common failure causes."""
        causes = []
        
        # Analyze issues encountered
        all_issues = []
        for o in outcomes:
            all_issues.extend(o.issues_encountered)
        
        if all_issues:
            # Count issue frequency
            issue_counts = defaultdict(int)
            for issue in all_issues:
                issue_counts[issue] += 1
            
            # Get top 3 causes
            top_causes = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            causes = [cause for cause, count in top_causes]
        else:
            causes = ["Permission denied", "Resource in use", "Dependency conflict"]
        
        return causes
    
    def _identify_risk_factors(self, outcomes: List) -> List[str]:
        """Identify risk factors from failures."""
        factors = [
            "Resource has active connections",
            "No recent backup available",
            "High-priority workload",
            "Production environment"
        ]
        return factors
    
    def _generate_avoidance_strategies(self, outcomes: List, rec_type: str) -> List[str]:
        """Generate strategies to avoid failures."""
        strategies = []
        
        if rec_type == "terminate":
            strategies.append("Verify no active connections before termination")
            strategies.append("Create fresh backup immediately before execution")
            strategies.append("Check resource tags for production indicators")
        elif rec_type == "right_size":
            strategies.append("Test new size in staging first")
            strategies.append("Schedule during low-traffic periods")
            strategies.append("Have rollback plan ready")
        
        return strategies
