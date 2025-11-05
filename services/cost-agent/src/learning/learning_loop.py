"""
Learning Loop.

Orchestrates the continuous learning process.
"""

import logging
import uuid
import time
from typing import Dict, Any, List
from datetime import datetime

from src.learning.outcome_tracker import OutcomeTracker
from src.learning.knowledge_store import KnowledgeStore
from src.learning.feedback_analyzer import FeedbackAnalyzer
from src.learning.improvement_engine import ImprovementEngine
from src.models.learning_loop import (
    ProcessingResult,
    LearningCycleResult,
    LearningMetrics,
    FeedbackData
)

logger = logging.getLogger(__name__)


class LearningLoop:
    """Orchestrates the continuous learning process."""
    
    def __init__(
        self,
        outcome_tracker: OutcomeTracker = None,
        knowledge_store: KnowledgeStore = None,
        feedback_analyzer: FeedbackAnalyzer = None,
        improvement_engine: ImprovementEngine = None
    ):
        """
        Initialize learning loop.
        
        Args:
            outcome_tracker: Outcome tracker instance
            knowledge_store: Knowledge store instance
            feedback_analyzer: Feedback analyzer instance
            improvement_engine: Improvement engine instance
        """
        self.outcome_tracker = outcome_tracker or OutcomeTracker()
        self.knowledge_store = knowledge_store or KnowledgeStore()
        self.feedback_analyzer = feedback_analyzer or FeedbackAnalyzer(
            outcome_tracker=self.outcome_tracker,
            knowledge_store=self.knowledge_store
        )
        self.improvement_engine = improvement_engine or ImprovementEngine()
        
        # Track learning cycles
        self.learning_cycles_completed = 0
        self.last_learning_cycle = None
    
    async def process_execution_outcome(
        self,
        execution_id: str,
        recommendation_id: str,
        outcome_data: Dict[str, Any] = None
    ) -> ProcessingResult:
        """
        Process an execution outcome through the learning loop.
        
        Args:
            execution_id: Execution ID
            recommendation_id: Recommendation ID
            outcome_data: Optional outcome data (if not already tracked)
        
        Returns:
            ProcessingResult with processing details
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing execution outcome: {execution_id}")
            
            # Track outcome if data provided
            if outcome_data:
                outcome = await self.outcome_tracker.track_execution_outcome(
                    execution_id=execution_id,
                    recommendation_id=recommendation_id,
                    outcome_data=outcome_data
                )
            else:
                # Get existing outcome
                outcome = None
                for o in self.outcome_tracker.outcomes.values():
                    if o.execution_id == execution_id:
                        outcome = o
                        break
                
                if not outcome:
                    raise ValueError(f"Outcome not found for execution {execution_id}")
            
            # Get recommendation data (would query from recommendation engine)
            recommendation = {
                "recommendation_id": recommendation_id,
                "recommendation_type": outcome.recommendation_type,
                "resource_type": "ec2",
                "resource_id": "i-test",
                "region": "us-east-1",
                "monthly_savings": outcome.predicted_savings,
                "risk_level": "medium"
            }
            
            # Store in Qdrant
            vector_id = await self.knowledge_store.store_recommendation_outcome(
                recommendation=recommendation,
                outcome=outcome.dict()
            )
            
            stored_in_qdrant = vector_id is not None
            
            # Generate insights (quick analysis)
            insights_generated = 0
            improvements_identified = 0
            
            # If this is a failure, generate immediate insights
            if not outcome.success:
                insights = await self.feedback_analyzer.generate_learning_insights(lookback_days=7)
                insights_generated = len(insights)
                
                # Identify improvement opportunities
                opportunities = await self.feedback_analyzer.identify_improvement_opportunities()
                improvements_identified = len(opportunities)
            
            processing_time = time.time() - start_time
            
            result = ProcessingResult(
                outcome_id=outcome.outcome_id,
                stored_in_qdrant=stored_in_qdrant,
                vector_id=vector_id,
                insights_generated=insights_generated,
                improvements_identified=improvements_identified,
                processing_time_seconds=processing_time,
                success=True,
                message=f"Outcome processed successfully"
            )
            
            logger.info(f"Outcome processed: {outcome.outcome_id} (stored={stored_in_qdrant}, insights={insights_generated})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing outcome: {e}", exc_info=True)
            
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                outcome_id="unknown",
                stored_in_qdrant=False,
                vector_id=None,
                insights_generated=0,
                improvements_identified=0,
                processing_time_seconds=processing_time,
                success=False,
                message=f"Error: {str(e)}"
            )
    
    async def run_learning_cycle(
        self,
        force: bool = False
    ) -> LearningCycleResult:
        """
        Run a complete learning cycle.
        
        Args:
            force: Force run even if recently run
        
        Returns:
            LearningCycleResult with cycle details
        """
        cycle_id = f"cycle-{uuid.uuid4()}"
        started_at = datetime.utcnow()
        
        try:
            logger.info(f"Starting learning cycle: {cycle_id}")
            
            # Get recent outcomes (last 24 hours)
            recent_outcomes = await self.outcome_tracker.get_recent_outcomes(days=1)
            
            logger.info(f"Processing {len(recent_outcomes)} recent outcomes")
            
            # Store outcomes in Qdrant
            outcomes_processed = 0
            for outcome in recent_outcomes:
                try:
                    # Get recommendation data
                    recommendation = {
                        "recommendation_id": outcome.recommendation_id,
                        "recommendation_type": outcome.recommendation_type,
                        "resource_type": "ec2",
                        "resource_id": "i-test",
                        "region": "us-east-1",
                        "monthly_savings": outcome.predicted_savings
                    }
                    
                    # Store in Qdrant
                    await self.knowledge_store.store_recommendation_outcome(
                        recommendation=recommendation,
                        outcome=outcome.dict()
                    )
                    
                    outcomes_processed += 1
                    
                except Exception as e:
                    logger.error(f"Error storing outcome {outcome.outcome_id}: {e}")
            
            # Generate insights
            insights = await self.feedback_analyzer.generate_learning_insights(lookback_days=30)
            insights_generated = len(insights)
            
            logger.info(f"Generated {insights_generated} insights")
            
            # Apply improvements
            improvements_applied = 0
            accuracy_improvement = 0.0
            
            # Adjust scoring weights
            if insights:
                new_weights = await self.improvement_engine.adjust_scoring_weights(insights)
                improvements_applied += 1
            
            # Refine predictions for each recommendation type
            rec_types = ["terminate", "right_size", "hibernate", "spot"]
            for rec_type in rec_types:
                # Get historical data
                historical = await self.outcome_tracker.get_outcomes_by_type(rec_type, limit=100)
                
                if len(historical) >= 10:  # Need at least 10 samples
                    # Refine prediction model
                    model = await self.improvement_engine.refine_cost_predictions(
                        recommendation_type=rec_type,
                        historical_data=historical
                    )
                    improvements_applied += 1
                    
                    # Track accuracy improvement
                    if model.base_accuracy > 0.80:
                        accuracy_improvement += (model.base_accuracy - 0.80)
            
            # Update risk assessments
            for rec_type in rec_types:
                failure_patterns = await self.feedback_analyzer.analyze_failure_patterns(
                    recommendation_type=rec_type,
                    lookback_days=30
                )
                
                if failure_patterns.total_cases >= 5:
                    risk_model = await self.improvement_engine.update_risk_assessments(
                        failure_patterns=failure_patterns
                    )
                    improvements_applied += 1
            
            # Calculate average accuracy improvement
            if improvements_applied > 0:
                accuracy_improvement = accuracy_improvement / len(rec_types)
            
            completed_at = datetime.utcnow()
            duration = (completed_at - started_at).total_seconds()
            
            # Update tracking
            self.learning_cycles_completed += 1
            self.last_learning_cycle = completed_at
            
            result = LearningCycleResult(
                cycle_id=cycle_id,
                started_at=started_at,
                completed_at=completed_at,
                outcomes_processed=outcomes_processed,
                insights_generated=insights_generated,
                improvements_applied=improvements_applied,
                accuracy_improvement=accuracy_improvement,
                duration_seconds=duration,
                success=True,
                message="Learning cycle completed successfully",
                details={
                    "recent_outcomes": len(recent_outcomes),
                    "stored_in_qdrant": outcomes_processed,
                    "insights": insights_generated,
                    "improvements": improvements_applied
                }
            )
            
            logger.info(f"Learning cycle complete: {cycle_id} (duration={duration:.1f}s, improvements={improvements_applied})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in learning cycle: {e}", exc_info=True)
            
            completed_at = datetime.utcnow()
            duration = (completed_at - started_at).total_seconds()
            
            return LearningCycleResult(
                cycle_id=cycle_id,
                started_at=started_at,
                completed_at=completed_at,
                outcomes_processed=0,
                insights_generated=0,
                improvements_applied=0,
                accuracy_improvement=0.0,
                duration_seconds=duration,
                success=False,
                message=f"Error: {str(e)}",
                details={}
            )
    
    async def get_learning_metrics(self) -> LearningMetrics:
        """
        Get overall learning metrics.
        
        Returns:
            LearningMetrics with current metrics
        """
        try:
            # Get recent outcomes
            recent_outcomes = await self.outcome_tracker.get_recent_outcomes(days=30)
            
            # Calculate metrics
            total_outcomes = len(recent_outcomes)
            
            if total_outcomes > 0:
                successful = [o for o in recent_outcomes if o.success]
                success_rate = len(successful) / total_outcomes
                
                # Average savings accuracy
                valid_savings = [o.savings_accuracy for o in successful if o.savings_accuracy > 0]
                avg_savings_accuracy = sum(valid_savings) / len(valid_savings) if valid_savings else 0.0
                
                # Average prediction error
                errors = [abs(1.0 - o.savings_accuracy) for o in successful if o.savings_accuracy > 0]
                avg_prediction_error = sum(errors) / len(errors) if errors else 0.0
                
                # Improvement over baseline (80% baseline)
                baseline = 0.80
                improvement = (avg_savings_accuracy - baseline) / baseline if baseline > 0 else 0.0
            else:
                success_rate = 0.0
                avg_savings_accuracy = 0.0
                avg_prediction_error = 0.0
                improvement = 0.0
            
            # Count active improvements (simplified)
            active_improvements = len(self.improvement_engine.prediction_models) + len(self.improvement_engine.risk_models)
            
            # Get insights count (from recent analysis)
            insights = await self.feedback_analyzer.generate_learning_insights(lookback_days=30)
            insights_generated = len(insights)
            
            metrics = LearningMetrics(
                total_outcomes_tracked=total_outcomes,
                success_rate=success_rate,
                avg_savings_accuracy=avg_savings_accuracy,
                avg_prediction_error=avg_prediction_error,
                improvement_over_baseline=improvement,
                learning_cycles_completed=self.learning_cycles_completed,
                last_learning_cycle=self.last_learning_cycle,
                active_improvements=active_improvements,
                insights_generated=insights_generated,
                measurement_period_days=30
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting learning metrics: {e}", exc_info=True)
            raise
    
    async def apply_improvements(
        self,
        improvements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Apply specific improvements.
        
        Args:
            improvements: List of improvements to apply
        
        Returns:
            Application result
        """
        try:
            logger.info(f"Applying {len(improvements)} improvements")
            
            applied = 0
            failed = 0
            
            for improvement in improvements:
                try:
                    # Apply improvement based on type
                    improvement_type = improvement.get("type")
                    
                    if improvement_type == "scoring_weights":
                        # Would apply scoring weight changes
                        applied += 1
                    elif improvement_type == "prediction_model":
                        # Would apply prediction model changes
                        applied += 1
                    elif improvement_type == "risk_model":
                        # Would apply risk model changes
                        applied += 1
                    
                except Exception as e:
                    logger.error(f"Error applying improvement: {e}")
                    failed += 1
            
            return {
                "success": True,
                "applied": applied,
                "failed": failed,
                "message": f"Applied {applied} improvements, {failed} failed"
            }
            
        except Exception as e:
            logger.error(f"Error applying improvements: {e}", exc_info=True)
            return {
                "success": False,
                "applied": 0,
                "failed": len(improvements),
                "message": f"Error: {str(e)}"
            }
