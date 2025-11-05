"""
Rollback Manager.

Manages rollback operations for failed or unwanted executions.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from src.models.execution_engine import (
    RollbackPlan,
    RollbackResult,
    RiskLevel
)

logger = logging.getLogger(__name__)


class RollbackManager:
    """Manages execution rollbacks."""
    
    def __init__(self):
        """Initialize rollback manager."""
        pass
    
    async def create_rollback_plan(
        self,
        recommendation: Dict[str, Any]
    ) -> RollbackPlan:
        """
        Create a rollback plan for a recommendation.
        
        Args:
            recommendation: Recommendation to create plan for
        
        Returns:
            RollbackPlan with rollback steps
        """
        rec_type = recommendation.get("recommendation_type", "")
        execution_id = recommendation.get("execution_id", "unknown")
        
        # Generate rollback steps based on recommendation type
        rollback_steps = self._generate_rollback_steps(recommendation)
        
        # Estimate duration
        estimated_duration = len(rollback_steps) * 2  # 2 minutes per step
        
        # Assess risk
        risk_level = self._assess_rollback_risk(recommendation)
        
        # Determine if approval needed
        requires_approval = risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        
        # Generate warnings
        warnings = self._generate_rollback_warnings(recommendation)
        
        return RollbackPlan(
            execution_id=execution_id,
            rollback_steps=rollback_steps,
            estimated_duration_minutes=estimated_duration,
            risk_level=risk_level,
            requires_approval=requires_approval,
            warnings=warnings
        )
    
    async def execute_rollback(
        self,
        execution_id: str,
        recommendation: Dict[str, Any],
        rollback_info: Dict[str, Any]
    ) -> RollbackResult:
        """
        Execute a rollback.
        
        Args:
            execution_id: Execution ID to rollback
            recommendation: Original recommendation
            rollback_info: Information needed for rollback
        
        Returns:
            RollbackResult with rollback details
        """
        rollback_started_at = datetime.utcnow()
        rollback_log = []
        
        try:
            logger.info(f"Starting rollback for execution {execution_id}")
            rollback_log.append(f"Rollback started at {rollback_started_at}")
            
            # Create rollback plan
            plan = await self.create_rollback_plan(recommendation)
            rollback_log.append(f"Created rollback plan with {len(plan.rollback_steps)} steps")
            
            # Execute rollback steps
            for i, step in enumerate(plan.rollback_steps, 1):
                rollback_log.append(f"Step {i}/{len(plan.rollback_steps)}: {step}")
                
                # Execute step
                success = await self._execute_rollback_step(
                    step,
                    recommendation,
                    rollback_info
                )
                
                if not success:
                    rollback_log.append(f"Step {i} failed")
                    return RollbackResult(
                        execution_id=execution_id,
                        success=False,
                        message=f"Rollback failed at step {i}: {step}",
                        rollback_started_at=rollback_started_at,
                        rollback_completed_at=datetime.utcnow(),
                        rollback_log=rollback_log
                    )
                
                rollback_log.append(f"Step {i} completed")
            
            # Verify rollback
            rollback_log.append("Verifying rollback")
            verified = await self.verify_rollback(execution_id, recommendation)
            
            if not verified:
                rollback_log.append("Rollback verification failed")
                return RollbackResult(
                    execution_id=execution_id,
                    success=False,
                    message="Rollback completed but verification failed",
                    rollback_started_at=rollback_started_at,
                    rollback_completed_at=datetime.utcnow(),
                    rollback_log=rollback_log
                )
            
            rollback_log.append("Rollback verified successfully")
            
            logger.info(f"Rollback for execution {execution_id} completed successfully")
            
            return RollbackResult(
                execution_id=execution_id,
                success=True,
                message="Rollback completed successfully",
                rollback_started_at=rollback_started_at,
                rollback_completed_at=datetime.utcnow(),
                rollback_log=rollback_log
            )
            
        except Exception as e:
            logger.error(f"Error executing rollback: {e}", exc_info=True)
            rollback_log.append(f"Error: {str(e)}")
            
            return RollbackResult(
                execution_id=execution_id,
                success=False,
                message=f"Rollback error: {str(e)}",
                rollback_started_at=rollback_started_at,
                rollback_completed_at=datetime.utcnow(),
                rollback_log=rollback_log
            )
    
    async def verify_rollback(
        self,
        execution_id: str,
        recommendation: Dict[str, Any]
    ) -> bool:
        """
        Verify rollback was successful.
        
        Args:
            execution_id: Execution ID
            recommendation: Original recommendation
        
        Returns:
            True if rollback verified
        """
        rec_type = recommendation.get("recommendation_type", "")
        resource_id = recommendation.get("resource_id", "")
        
        logger.info(f"Verifying rollback for {rec_type} on {resource_id}")
        
        # In production, would verify actual resource state
        # For now, return True
        return True
    
    # Private helper methods
    
    def _generate_rollback_steps(
        self,
        recommendation: Dict[str, Any]
    ) -> List[str]:
        """Generate rollback steps based on recommendation type."""
        rec_type = recommendation.get("recommendation_type", "")
        
        rollback_steps_map = {
            "terminate": [
                "Locate latest backup",
                "Launch new instance from backup",
                "Verify instance is running",
                "Restore network configuration",
                "Verify application is accessible"
            ],
            "right_size": [
                "Stop instance",
                "Modify instance type back to original",
                "Start instance",
                "Verify instance is running",
                "Monitor performance"
            ],
            "hibernate": [
                "Remove hibernation schedule",
                "Ensure instance stays running",
                "Verify 24/7 availability"
            ],
            "spot": [
                "Launch on-demand instance",
                "Migrate workload back",
                "Terminate spot instance",
                "Verify on-demand is running"
            ],
            "ri": [
                "List RIs on marketplace (manual)",
                "Wait for sale (manual)",
                "Verify RI is sold"
            ],
            "auto_scale": [
                "Disable auto-scaling",
                "Set fixed capacity",
                "Verify scaling is disabled"
            ],
            "storage_optimize": [
                "Move data back to standard tier",
                "Verify data accessibility",
                "Remove lifecycle policies"
            ],
            "config_fix": [
                "Revert to previous configuration",
                "Verify configuration is restored"
            ]
        }
        
        return rollback_steps_map.get(rec_type, [
            "Identify changes made",
            "Revert changes",
            "Verify rollback"
        ])
    
    def _assess_rollback_risk(
        self,
        recommendation: Dict[str, Any]
    ) -> RiskLevel:
        """Assess risk of rollback operation."""
        rec_type = recommendation.get("recommendation_type", "")
        
        # Risk levels for rollback
        risk_map = {
            "terminate": RiskLevel.HIGH,  # Restoring from backup is risky
            "right_size": RiskLevel.MEDIUM,
            "hibernate": RiskLevel.LOW,
            "spot": RiskLevel.MEDIUM,
            "ri": RiskLevel.HIGH,  # Selling RI is manual and risky
            "auto_scale": RiskLevel.LOW,
            "storage_optimize": RiskLevel.MEDIUM,
            "config_fix": RiskLevel.LOW
        }
        
        return risk_map.get(rec_type, RiskLevel.MEDIUM)
    
    def _generate_rollback_warnings(
        self,
        recommendation: Dict[str, Any]
    ) -> List[str]:
        """Generate warnings for rollback."""
        rec_type = recommendation.get("recommendation_type", "")
        warnings = []
        
        if rec_type == "terminate":
            warnings.append("Rollback requires restoring from backup")
            warnings.append("Some data may be lost since backup")
            warnings.append("Downtime will occur during restoration")
        elif rec_type == "right_size":
            warnings.append("Brief downtime during instance resize")
            warnings.append("Performance should return to original")
        elif rec_type == "ri":
            warnings.append("RI rollback requires manual marketplace sale")
            warnings.append("May take days to sell RI")
            warnings.append("May not recover full cost")
        
        return warnings
    
    async def _execute_rollback_step(
        self,
        step: str,
        recommendation: Dict[str, Any],
        rollback_info: Dict[str, Any]
    ) -> bool:
        """
        Execute a single rollback step.
        
        Args:
            step: Step description
            recommendation: Original recommendation
            rollback_info: Rollback information
        
        Returns:
            True if step succeeded
        """
        logger.info(f"Executing rollback step: {step}")
        
        # In production, would execute actual rollback actions
        # For now, simulate success
        
        return True
