"""
Approval Engine

Implements approval/rejection logic for validation decisions.
"""

import uuid
from typing import List
from ..models.validation import (
    ValidationRequest,
    ValidationResult,
    ValidationDecision,
    ValidationHistory
)
from ..core.logger import logger


class ApprovalEngine:
    """Engine for making approval/rejection decisions."""
    
    def __init__(self):
        """Initialize approval engine."""
        self.validation_history: List[ValidationHistory] = []
        self.quality_threshold = 5.0  # 5% drop threshold
        self.confidence_threshold = 0.8
    
    def validate_change(
        self,
        request: ValidationRequest,
        p_value: float = None,
        effect_size: float = None
    ) -> ValidationResult:
        """
        Validate an optimization change.
        
        Args:
            request: Validation request
            p_value: P-value from statistical test (optional)
            effect_size: Effect size from test (optional)
            
        Returns:
            Validation result with decision
        """
        validation_id = str(uuid.uuid4())
        
        logger.info(f"Validating change: {validation_id} - {request.name}")
        
        # Calculate quality change
        quality_change = request.new_quality - request.baseline_quality
        quality_change_pct = (quality_change / request.baseline_quality) * 100
        
        # Check statistical significance
        statistically_significant = False
        if p_value is not None:
            statistically_significant = p_value < 0.05
        
        # Make decision
        decision, confidence, reasoning = self._make_decision(
            quality_change_pct,
            statistically_significant,
            p_value,
            effect_size
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            decision,
            quality_change_pct,
            statistically_significant
        )
        
        result = ValidationResult(
            validation_id=validation_id,
            name=request.name,
            decision=decision,
            confidence=confidence,
            baseline_quality=request.baseline_quality,
            new_quality=request.new_quality,
            quality_change=quality_change,
            quality_change_percentage=quality_change_pct,
            statistically_significant=statistically_significant,
            p_value=p_value,
            effect_size=effect_size,
            recommendation=recommendation,
            reasoning=reasoning,
            metadata=request.metadata
        )
        
        # Add to history
        history = ValidationHistory(
            validation_id=validation_id,
            decision=decision,
            quality_change=quality_change_pct,
            confidence=confidence
        )
        self.validation_history.append(history)
        
        logger.info(
            f"Validation decision: {decision}, "
            f"confidence={confidence:.2f}, "
            f"quality_change={quality_change_pct:.2f}%"
        )
        
        return result
    
    def _make_decision(
        self,
        quality_change_pct: float,
        statistically_significant: bool,
        p_value: float = None,
        effect_size: float = None
    ) -> tuple:
        """
        Make approval/rejection decision.
        
        Args:
            quality_change_pct: Quality change percentage
            statistically_significant: Is change significant
            p_value: P-value
            effect_size: Effect size
            
        Returns:
            Tuple of (decision, confidence, reasoning)
        """
        reasoning = []
        
        # Case 1: Significant improvement
        if quality_change_pct > 0 and statistically_significant:
            decision = ValidationDecision.APPROVE
            confidence = 0.95
            reasoning.append(f"Quality improved by {quality_change_pct:.1f}%")
            reasoning.append("Improvement is statistically significant")
            
        # Case 2: Minor improvement (not significant)
        elif quality_change_pct > 0 and not statistically_significant:
            decision = ValidationDecision.APPROVE
            confidence = 0.85
            reasoning.append(f"Quality improved by {quality_change_pct:.1f}%")
            reasoning.append("No statistical test performed or not significant")
            
        # Case 3: No change or very minor drop (< 2%)
        elif abs(quality_change_pct) < 2.0:
            decision = ValidationDecision.APPROVE
            confidence = 0.90
            reasoning.append("Quality maintained (change < 2%)")
            reasoning.append("No significant degradation detected")
            
        # Case 4: Minor drop (2-5%)
        elif -5.0 <= quality_change_pct < -2.0:
            if statistically_significant:
                decision = ValidationDecision.REJECT
                confidence = 0.85
                reasoning.append(f"Quality dropped by {abs(quality_change_pct):.1f}%")
                reasoning.append("Drop is statistically significant")
            else:
                decision = ValidationDecision.MANUAL_REVIEW
                confidence = 0.70
                reasoning.append(f"Quality dropped by {abs(quality_change_pct):.1f}%")
                reasoning.append("Borderline case - manual review recommended")
            
        # Case 5: Significant drop (> 5%)
        elif quality_change_pct < -5.0:
            decision = ValidationDecision.REJECT
            confidence = 0.95
            reasoning.append(f"Quality dropped by {abs(quality_change_pct):.1f}%")
            reasoning.append("Drop exceeds threshold (5%)")
            if statistically_significant:
                reasoning.append("Drop is statistically significant")
        
        else:
            # Default to manual review for edge cases
            decision = ValidationDecision.MANUAL_REVIEW
            confidence = 0.60
            reasoning.append("Edge case detected")
            reasoning.append("Manual review required")
        
        # Adjust confidence based on effect size
        if effect_size is not None:
            if abs(effect_size) > 0.8:  # Large effect
                confidence = min(confidence + 0.05, 1.0)
                reasoning.append(f"Large effect size detected ({effect_size:.2f})")
            elif abs(effect_size) < 0.2:  # Small effect
                confidence = max(confidence - 0.05, 0.0)
        
        return decision, confidence, reasoning
    
    def _generate_recommendation(
        self,
        decision: ValidationDecision,
        quality_change_pct: float,
        statistically_significant: bool
    ) -> str:
        """
        Generate human-readable recommendation.
        
        Args:
            decision: Validation decision
            quality_change_pct: Quality change percentage
            statistically_significant: Is change significant
            
        Returns:
            Recommendation string
        """
        if decision == ValidationDecision.APPROVE:
            if quality_change_pct > 0:
                return (
                    f"Approve change - Quality improved by {quality_change_pct:.1f}%. "
                    f"{'Statistically significant improvement.' if statistically_significant else 'Safe to deploy.'}"
                )
            else:
                return (
                    f"Approve change - Quality maintained (change: {quality_change_pct:.1f}%). "
                    "No significant degradation detected."
                )
        
        elif decision == ValidationDecision.REJECT:
            return (
                f"Reject change - Quality dropped by {abs(quality_change_pct):.1f}%. "
                f"{'Statistically significant degradation.' if statistically_significant else 'Exceeds acceptable threshold.'} "
                "Recommend rollback."
            )
        
        else:  # MANUAL_REVIEW
            return (
                f"Manual review required - Quality changed by {quality_change_pct:.1f}%. "
                "Borderline case with conflicting signals. Human judgment needed."
            )
    
    def get_validation_history(self, limit: int = 100) -> List[ValidationHistory]:
        """
        Get validation history.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of validation history records
        """
        return self.validation_history[-limit:]


# Global instance
approval_engine = ApprovalEngine()
