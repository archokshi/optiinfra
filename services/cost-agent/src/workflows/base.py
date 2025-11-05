"""
Base Workflow Class

Abstract base class for all Cost Agent workflows.
Provides common patterns for approval, rollback, and learning.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

from .states import OptimizationState


class BaseWorkflow(ABC):
    """Abstract base class for optimization workflows"""
    
    def __init__(self, workflow_type: str):
        self.workflow_type = workflow_type
        self.logger = logging.getLogger(f"{__name__}.{workflow_type}")
    
    # ==================== Abstract Methods ====================
    
    @abstractmethod
    async def analyze(self, state: OptimizationState) -> OptimizationState:
        """
        Analyze infrastructure and identify optimization opportunities
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with analysis_results
        """
        pass
    
    @abstractmethod
    async def generate_recommendations(self, state: OptimizationState) -> OptimizationState:
        """
        Generate specific recommendations based on analysis
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with recommendations
        """
        pass
    
    @abstractmethod
    async def execute(self, state: OptimizationState) -> OptimizationState:
        """
        Execute the optimization recommendations
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with execution_results
        """
        pass
    
    # ==================== Common Workflow Nodes ====================
    
    async def check_approval_needed(self, state: OptimizationState) -> OptimizationState:
        """
        Determine if human approval is needed
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with requires_approval flag
        """
        self.logger.info(f"Checking approval requirements for workflow {state['workflow_id']}")
        
        # Check if estimated savings exceed threshold
        estimated_savings = state.get('estimated_savings', 0)
        confidence_score = state.get('confidence_score', 0)
        
        # Require approval if:
        # 1. Savings > $1000/month
        # 2. Confidence < 0.8
        # 3. Constraints specify manual approval
        requires_approval = (
            estimated_savings > 1000 or
            confidence_score < 0.8 or
            state.get('constraints', {}).get('require_approval', False)
        )
        
        state['requires_approval'] = requires_approval
        state['approval_status'] = 'pending' if requires_approval else 'auto-approved'
        state['updated_at'] = datetime.utcnow()
        
        self.logger.info(f"Approval required: {requires_approval}")
        return state
    
    async def wait_for_approval(self, state: OptimizationState) -> OptimizationState:
        """
        Wait for human approval (checkpoint state)
        
        Args:
            state: Current workflow state
            
        Returns:
            State (unchanged, waiting for external approval)
        """
        self.logger.info(f"Waiting for approval on workflow {state['workflow_id']}")
        
        # This is a checkpoint - workflow will pause here
        # External system will update approval_status
        state['approval_status'] = 'pending'
        state['updated_at'] = datetime.utcnow()
        
        return state
    
    async def handle_approval_decision(self, state: OptimizationState) -> OptimizationState:
        """
        Handle approval decision (approved/rejected)
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state
        """
        approval_status = state.get('approval_status', 'pending')
        
        self.logger.info(f"Handling approval decision: {approval_status}")
        
        if approval_status == 'rejected':
            state['success'] = False
            state['errors'].append("Workflow rejected by approver")
        
        state['updated_at'] = datetime.utcnow()
        return state
    
    async def rollback(self, state: OptimizationState) -> OptimizationState:
        """
        Rollback changes if execution failed
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with rollback_completed flag
        """
        self.logger.warning(f"Rolling back workflow {state['workflow_id']}")
        
        try:
            # Perform rollback logic (workflow-specific)
            await self._perform_rollback(state)
            
            state['rollback_completed'] = True
            state['rollback_needed'] = False
            self.logger.info("Rollback completed successfully")
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {str(e)}")
            state['errors'].append(f"Rollback failed: {str(e)}")
            state['rollback_completed'] = False
        
        state['updated_at'] = datetime.utcnow()
        return state
    
    async def learn(self, state: OptimizationState) -> OptimizationState:
        """
        Learn from workflow outcome and update models
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with learned flag
        """
        self.logger.info(f"Learning from workflow {state['workflow_id']}")
        
        try:
            # Extract outcome data
            outcome = {
                'workflow_type': state['workflow_type'],
                'success': state['success'],
                'estimated_savings': state.get('estimated_savings'),
                'actual_savings': state.get('execution_results', {}).get('actual_savings'),
                'confidence_score': state.get('confidence_score'),
                'errors': state['errors']
            }
            
            state['outcome'] = outcome
            state['learned'] = True
            
            # Store learning data (to be implemented with LLM integration)
            await self._store_learning_data(outcome)
            
            self.logger.info("Learning completed")
            
        except Exception as e:
            self.logger.error(f"Learning failed: {str(e)}")
            state['errors'].append(f"Learning failed: {str(e)}")
        
        state['updated_at'] = datetime.utcnow()
        return state
    
    # ==================== Helper Methods ====================
    
    async def _perform_rollback(self, state: OptimizationState):
        """
        Perform workflow-specific rollback
        Override in subclasses
        """
        self.logger.info("No rollback logic implemented")
        pass
    
    async def _store_learning_data(self, outcome: Dict[str, Any]):
        """
        Store learning data for future model improvements
        Override in subclasses
        """
        self.logger.info(f"Storing learning data: {outcome}")
        # TODO: Implement with Qdrant vector storage
        pass
    
    # ==================== Conditional Routing ====================
    
    def should_execute(self, state: OptimizationState) -> str:
        """
        Determine if workflow should proceed to execution
        
        Args:
            state: Current workflow state
            
        Returns:
            "execute" or "end"
        """
        approval_status = state.get('approval_status')
        
        if approval_status == 'approved' or approval_status == 'auto-approved':
            return "execute"
        elif approval_status == 'rejected':
            return "end"
        else:
            return "wait_approval"
    
    def should_rollback(self, state: OptimizationState) -> str:
        """
        Determine if rollback is needed
        
        Args:
            state: Current workflow state
            
        Returns:
            "rollback" or "learn"
        """
        if state.get('rollback_needed', False) and not state.get('rollback_completed', False):
            return "rollback"
        else:
            return "learn"
    
    def check_success(self, state: OptimizationState) -> str:
        """
        Check if execution was successful
        
        Args:
            state: Current workflow state
            
        Returns:
            "success" or "failure"
        """
        if state.get('success', False):
            return "success"
        else:
            return "failure"
