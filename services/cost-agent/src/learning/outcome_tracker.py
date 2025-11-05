"""
Outcome Tracker.

Tracks execution outcomes for learning and improvement.
"""

import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from src.models.learning_loop import (
    OutcomeRecord,
    SavingsMeasurement,
    ComparisonResult,
    ExecutionMetrics
)

logger = logging.getLogger(__name__)


class OutcomeTracker:
    """Tracks execution outcomes for learning."""
    
    def __init__(self, db_client=None):
        """
        Initialize outcome tracker.
        
        Args:
            db_client: Database client for storing outcomes
        """
        self.db_client = db_client
        self.outcomes = {}  # In-memory storage for now
    
    async def track_execution_outcome(
        self,
        execution_id: str,
        recommendation_id: str,
        outcome_data: Dict[str, Any]
    ) -> OutcomeRecord:
        """
        Track an execution outcome.
        
        Args:
            execution_id: Execution ID
            recommendation_id: Recommendation ID
            outcome_data: Outcome data including success, savings, etc.
        
        Returns:
            OutcomeRecord with tracked data
        """
        try:
            logger.info(f"Tracking outcome for execution {execution_id}")
            
            # Generate outcome ID
            outcome_id = f"outcome-{uuid.uuid4()}"
            
            # Extract data
            success = outcome_data.get("success", False)
            actual_savings = outcome_data.get("actual_savings")
            predicted_savings = outcome_data.get("predicted_savings", 0.0)
            execution_duration = outcome_data.get("execution_duration_seconds", 0.0)
            issues = outcome_data.get("issues_encountered", [])
            post_metrics = outcome_data.get("post_execution_metrics", {})
            
            # Calculate savings accuracy
            if actual_savings is not None and predicted_savings > 0:
                savings_accuracy = actual_savings / predicted_savings
            else:
                savings_accuracy = 0.0
            
            # Get recommendation type (from execution or default)
            recommendation_type = outcome_data.get("recommendation_type", "unknown")
            
            # Create outcome record
            outcome = OutcomeRecord(
                outcome_id=outcome_id,
                execution_id=execution_id,
                recommendation_id=recommendation_id,
                recommendation_type=recommendation_type,
                success=success,
                actual_savings=actual_savings,
                predicted_savings=predicted_savings,
                savings_accuracy=savings_accuracy,
                execution_duration_seconds=execution_duration,
                issues_encountered=issues,
                post_execution_metrics=post_metrics,
                timestamp=datetime.utcnow()
            )
            
            # Store in memory
            self.outcomes[outcome_id] = outcome
            
            # Store in database (if available)
            if self.db_client:
                await self._store_in_database(outcome)
            
            logger.info(f"Outcome tracked: {outcome_id} (success={success}, accuracy={savings_accuracy:.2f})")
            
            return outcome
            
        except Exception as e:
            logger.error(f"Error tracking outcome: {e}", exc_info=True)
            raise
    
    async def measure_actual_savings(
        self,
        execution_id: str,
        days: int = 30
    ) -> SavingsMeasurement:
        """
        Measure actual savings over a period.
        
        Args:
            execution_id: Execution ID
            days: Number of days to measure
        
        Returns:
            SavingsMeasurement with actual savings data
        """
        try:
            logger.info(f"Measuring actual savings for execution {execution_id} over {days} days")
            
            # Find outcome for this execution
            outcome = None
            for o in self.outcomes.values():
                if o.execution_id == execution_id:
                    outcome = o
                    break
            
            if not outcome:
                raise ValueError(f"Outcome not found for execution {execution_id}")
            
            # In production, would query actual cost data from cloud provider
            # For now, use the tracked actual_savings
            actual_savings = outcome.actual_savings or 0.0
            predicted_savings = outcome.predicted_savings
            
            # Calculate accuracy
            if predicted_savings > 0:
                savings_accuracy = actual_savings / predicted_savings
            else:
                savings_accuracy = 0.0
            
            # Mock cost data
            cost_before = 100.0  # Would query from cost data
            cost_after = cost_before - actual_savings
            
            measurement = SavingsMeasurement(
                execution_id=execution_id,
                recommendation_id=outcome.recommendation_id,
                measurement_period_days=days,
                actual_savings=actual_savings,
                predicted_savings=predicted_savings,
                savings_accuracy=savings_accuracy,
                cost_before=cost_before,
                cost_after=cost_after,
                measured_at=datetime.utcnow()
            )
            
            logger.info(f"Savings measured: ${actual_savings:.2f} (accuracy={savings_accuracy:.1%})")
            
            return measurement
            
        except Exception as e:
            logger.error(f"Error measuring savings: {e}", exc_info=True)
            raise
    
    async def compare_predicted_vs_actual(
        self,
        recommendation_id: str
    ) -> ComparisonResult:
        """
        Compare predicted vs actual outcomes.
        
        Args:
            recommendation_id: Recommendation ID
        
        Returns:
            ComparisonResult with comparison data
        """
        try:
            logger.info(f"Comparing predicted vs actual for recommendation {recommendation_id}")
            
            # Find outcome for this recommendation
            outcome = None
            for o in self.outcomes.values():
                if o.recommendation_id == recommendation_id:
                    outcome = o
                    break
            
            if not outcome:
                raise ValueError(f"Outcome not found for recommendation {recommendation_id}")
            
            # Calculate metrics
            predicted_savings = outcome.predicted_savings
            actual_savings = outcome.actual_savings or 0.0
            
            if predicted_savings > 0:
                savings_accuracy = actual_savings / predicted_savings
                prediction_error = abs(actual_savings - predicted_savings) / predicted_savings
            else:
                savings_accuracy = 0.0
                prediction_error = 1.0
            
            # Generate notes
            notes = []
            if savings_accuracy > 1.1:
                notes.append("Actual savings exceeded prediction by >10%")
            elif savings_accuracy < 0.9:
                notes.append("Actual savings below prediction by >10%")
            else:
                notes.append("Prediction was accurate within 10%")
            
            if not outcome.success:
                notes.append("Execution failed")
            
            if len(outcome.issues_encountered) > 0:
                notes.append(f"{len(outcome.issues_encountered)} issues encountered")
            
            comparison = ComparisonResult(
                recommendation_id=recommendation_id,
                predicted_savings=predicted_savings,
                actual_savings=actual_savings,
                savings_accuracy=savings_accuracy,
                prediction_error=prediction_error,
                execution_success=outcome.success,
                notes=notes
            )
            
            logger.info(f"Comparison complete: accuracy={savings_accuracy:.1%}, error={prediction_error:.1%}")
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing outcomes: {e}", exc_info=True)
            raise
    
    async def get_execution_metrics(
        self,
        execution_id: str
    ) -> ExecutionMetrics:
        """
        Get metrics for an execution.
        
        Args:
            execution_id: Execution ID
        
        Returns:
            ExecutionMetrics with execution data
        """
        try:
            # Find outcome for this execution
            outcome = None
            for o in self.outcomes.values():
                if o.execution_id == execution_id:
                    outcome = o
                    break
            
            if not outcome:
                raise ValueError(f"Outcome not found for execution {execution_id}")
            
            # Extract metrics
            metrics = ExecutionMetrics(
                execution_id=execution_id,
                duration_seconds=outcome.execution_duration_seconds,
                success=outcome.success,
                resources_affected=1,  # Would get from execution data
                issues_count=len(outcome.issues_encountered),
                rollback_required=not outcome.success,
                user_satisfaction=None  # Would get from user feedback
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting execution metrics: {e}", exc_info=True)
            raise
    
    async def get_outcomes_by_type(
        self,
        recommendation_type: str,
        limit: int = 100
    ) -> list[OutcomeRecord]:
        """
        Get outcomes by recommendation type.
        
        Args:
            recommendation_type: Type of recommendation
            limit: Maximum number of outcomes
        
        Returns:
            List of outcome records
        """
        outcomes = [
            o for o in self.outcomes.values()
            if o.recommendation_type == recommendation_type
        ]
        
        # Sort by timestamp (most recent first)
        outcomes.sort(key=lambda x: x.timestamp, reverse=True)
        
        return outcomes[:limit]
    
    async def get_recent_outcomes(
        self,
        days: int = 30,
        limit: int = 100
    ) -> list[OutcomeRecord]:
        """
        Get recent outcomes.
        
        Args:
            days: Number of days to look back
            limit: Maximum number of outcomes
        
        Returns:
            List of recent outcome records
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        outcomes = [
            o for o in self.outcomes.values()
            if o.timestamp >= cutoff
        ]
        
        # Sort by timestamp (most recent first)
        outcomes.sort(key=lambda x: x.timestamp, reverse=True)
        
        return outcomes[:limit]
    
    # Private helper methods
    
    async def _store_in_database(self, outcome: OutcomeRecord):
        """Store outcome in database."""
        # In production, would store in PostgreSQL
        logger.debug(f"Would store outcome {outcome.outcome_id} in database")
        pass
