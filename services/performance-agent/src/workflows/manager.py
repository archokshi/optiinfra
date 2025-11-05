"""
Workflow Manager

Manages workflow lifecycle and state persistence.
"""

import logging
import uuid
from typing import Dict, Optional
from datetime import datetime

from src.models.workflow import WorkflowState, WorkflowRequest, WorkflowStatus
from src.workflows.optimization_workflow import OptimizationWorkflow

logger = logging.getLogger(__name__)


class WorkflowManager:
    """Manages optimization workflows."""
    
    def __init__(self):
        """Initialize manager."""
        self.workflows: Dict[str, Dict] = {}
        self.optimization_workflow = OptimizationWorkflow()
    
    async def start_workflow(self, request: WorkflowRequest) -> WorkflowState:
        """
        Start a new optimization workflow.
        
        Args:
            request: Workflow request
            
        Returns:
            Initial workflow state
        """
        # Create workflow state
        workflow_id = str(uuid.uuid4())
        
        state_dict = {
            "workflow_id": workflow_id,
            "instance_id": request.instance_id,
            "instance_type": request.instance_type,
            "status": WorkflowStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "requires_approval": request.requires_approval,
            "auto_rollout": request.auto_rollout,
            "monitoring_duration_seconds": request.monitoring_duration_seconds,
            "health_threshold": request.health_threshold,
            "approved": None,
            "approved_by": None,
            "approved_at": None,
            "rollout_history": [],
            "analysis_result": None,
            "optimization_plan": None,
            "current_stage": None,
            "original_config": None,
            "applied_config": None,
            "final_health_score": None,
            "total_improvement": None,
            "error_message": None
        }
        
        # Store state
        self.workflows[workflow_id] = state_dict
        
        # Start workflow asynchronously
        logger.info(f"Starting workflow {workflow_id} for {request.instance_id}")
        
        try:
            # Run workflow
            result = await self.optimization_workflow.run(state_dict)
            
            # Update stored state
            self.workflows[workflow_id] = result
            
            # Convert to WorkflowState model
            return self._dict_to_state(result)
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {e}", exc_info=True)
            state_dict["status"] = WorkflowStatus.FAILED.value
            state_dict["error_message"] = str(e)
            self.workflows[workflow_id] = state_dict
            return self._dict_to_state(state_dict)
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get workflow state by ID."""
        state_dict = self.workflows.get(workflow_id)
        if not state_dict:
            return None
        return self._dict_to_state(state_dict)
    
    def approve_workflow(self, workflow_id: str, approved_by: str) -> Optional[WorkflowState]:
        """Approve a workflow."""
        state_dict = self.workflows.get(workflow_id)
        if not state_dict:
            return None
        
        state_dict["approved"] = True
        state_dict["approved_by"] = approved_by
        state_dict["approved_at"] = datetime.utcnow().isoformat()
        state_dict["status"] = WorkflowStatus.APPROVED.value
        
        logger.info(f"Workflow {workflow_id} approved by {approved_by}")
        
        return self._dict_to_state(state_dict)
    
    def reject_workflow(self, workflow_id: str) -> Optional[WorkflowState]:
        """Reject a workflow."""
        state_dict = self.workflows.get(workflow_id)
        if not state_dict:
            return None
        
        state_dict["approved"] = False
        state_dict["status"] = WorkflowStatus.REJECTED.value
        
        logger.info(f"Workflow {workflow_id} rejected")
        
        return self._dict_to_state(state_dict)
    
    def _dict_to_state(self, state_dict: Dict) -> WorkflowState:
        """Convert dict to WorkflowState model."""
        # Parse datetime strings
        created_at = datetime.fromisoformat(state_dict["created_at"]) if isinstance(state_dict["created_at"], str) else state_dict["created_at"]
        updated_at = datetime.fromisoformat(state_dict["updated_at"]) if isinstance(state_dict["updated_at"], str) else state_dict["updated_at"]
        
        approved_at = None
        if state_dict.get("approved_at"):
            approved_at = datetime.fromisoformat(state_dict["approved_at"]) if isinstance(state_dict["approved_at"], str) else state_dict["approved_at"]
        
        # Parse rollout history
        from src.models.workflow import RolloutStatus, RolloutStage
        rollout_history = []
        for rollout_dict in state_dict.get("rollout_history", []):
            rollout_history.append(RolloutStatus(
                stage=RolloutStage(rollout_dict["stage"]),
                status=rollout_dict["status"],
                started_at=datetime.fromisoformat(rollout_dict["started_at"]) if isinstance(rollout_dict["started_at"], str) else rollout_dict["started_at"],
                completed_at=datetime.fromisoformat(rollout_dict["completed_at"]) if rollout_dict.get("completed_at") and isinstance(rollout_dict["completed_at"], str) else rollout_dict.get("completed_at"),
                health_score_before=rollout_dict["health_score_before"],
                health_score_after=rollout_dict.get("health_score_after"),
                metrics_snapshot=rollout_dict.get("metrics_snapshot"),
                issues=rollout_dict.get("issues", [])
            ))
        
        # Parse analysis result
        from src.models.analysis import AnalysisResult
        analysis_result = None
        if state_dict.get("analysis_result"):
            analysis_result = AnalysisResult(**state_dict["analysis_result"])
        
        # Parse optimization plan
        from src.models.optimization import OptimizationPlan
        optimization_plan = None
        if state_dict.get("optimization_plan"):
            optimization_plan = OptimizationPlan(**state_dict["optimization_plan"])
        
        # Parse current stage
        from src.models.workflow import RolloutStage
        current_stage = None
        if state_dict.get("current_stage"):
            current_stage = RolloutStage(state_dict["current_stage"])
        
        return WorkflowState(
            workflow_id=state_dict["workflow_id"],
            instance_id=state_dict["instance_id"],
            instance_type=state_dict["instance_type"],
            status=WorkflowStatus(state_dict["status"]),
            created_at=created_at,
            updated_at=updated_at,
            analysis_result=analysis_result,
            optimization_plan=optimization_plan,
            requires_approval=state_dict.get("requires_approval", True),
            approved=state_dict.get("approved"),
            approved_by=state_dict.get("approved_by"),
            approved_at=approved_at,
            current_stage=current_stage,
            rollout_history=rollout_history,
            original_config=state_dict.get("original_config"),
            applied_config=state_dict.get("applied_config"),
            health_threshold=state_dict.get("health_threshold", 0.9),
            monitoring_duration_seconds=state_dict.get("monitoring_duration_seconds", 300),
            final_health_score=state_dict.get("final_health_score"),
            total_improvement=state_dict.get("total_improvement"),
            error_message=state_dict.get("error_message")
        )
