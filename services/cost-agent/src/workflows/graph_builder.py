"""
LangGraph Workflow Builder

Constructs StateGraph workflows with conditional routing and checkpointing.
"""

import logging
from typing import Dict, Any, Callable, Optional
from langgraph.graph import StateGraph, END

# Import checkpointer - handle different API versions
try:
    from langgraph.checkpoint.base import BaseCheckpointSaver
except ImportError:
    try:
        from langgraph.checkpoint import BaseCheckpointSaver
    except ImportError:
        # Fallback for validation without checkpointer
        BaseCheckpointSaver = object

from .states import OptimizationState
from .base import BaseWorkflow


class WorkflowGraphBuilder:
    """
    Builder for LangGraph workflows
    
    Constructs StateGraph with nodes, edges, and conditional routing.
    """
    
    def __init__(self, workflow: BaseWorkflow, checkpointer: Optional[Any] = None):
        """
        Initialize graph builder
        
        Args:
            workflow: Workflow implementation
            checkpointer: Checkpoint saver for state persistence (optional)
        """
        self.workflow = workflow
        self.checkpointer = checkpointer
        self.logger = logging.getLogger(__name__)
    
    def build(self) -> StateGraph:
        """
        Build the complete workflow graph
        
        Returns:
            Compiled StateGraph ready for execution
        """
        self.logger.info(f"Building workflow graph for {self.workflow.workflow_type}")
        
        # Create state graph
        graph = StateGraph(OptimizationState)
        
        # Add nodes
        graph.add_node("analyze", self.workflow.analyze)
        graph.add_node("generate_recommendations", self.workflow.generate_recommendations)
        graph.add_node("check_approval", self.workflow.check_approval_needed)
        graph.add_node("wait_approval", self.workflow.wait_for_approval)
        graph.add_node("handle_approval", self.workflow.handle_approval_decision)
        graph.add_node("execute", self.workflow.execute)
        graph.add_node("rollback", self.workflow.rollback)
        graph.add_node("learn", self.workflow.learn)
        
        # Set entry point
        graph.set_entry_point("analyze")
        
        # Add edges
        graph.add_edge("analyze", "generate_recommendations")
        graph.add_edge("generate_recommendations", "check_approval")
        
        # Conditional routing after approval check
        graph.add_conditional_edges(
            "check_approval",
            self._route_after_approval_check,
            {
                "wait_approval": "wait_approval",
                "execute": "execute",
                "end": END
            }
        )
        
        # After waiting for approval, handle the decision
        graph.add_edge("wait_approval", "handle_approval")
        
        # Conditional routing after approval decision
        graph.add_conditional_edges(
            "handle_approval",
            self._route_after_approval_decision,
            {
                "execute": "execute",
                "end": END
            }
        )
        
        # Conditional routing after execution
        graph.add_conditional_edges(
            "execute",
            self._route_after_execution,
            {
                "rollback": "rollback",
                "learn": "learn"
            }
        )
        
        # After rollback, go to learn
        graph.add_edge("rollback", "learn")
        
        # After learning, end workflow
        graph.add_edge("learn", END)
        
        # Compile graph with checkpointer (if provided)
        if self.checkpointer:
            compiled_graph = graph.compile(checkpointer=self.checkpointer)
        else:
            compiled_graph = graph.compile()
        
        self.logger.info("Workflow graph built successfully")
        return compiled_graph
    
    def _route_after_approval_check(self, state: OptimizationState) -> str:
        """
        Route after checking if approval is needed
        
        Args:
            state: Current workflow state
            
        Returns:
            Next node name
        """
        if not state.get('requires_approval', True):
            # Auto-approved, go directly to execution
            return "execute"
        else:
            # Needs approval, wait for human decision
            return "wait_approval"
    
    def _route_after_approval_decision(self, state: OptimizationState) -> str:
        """
        Route after approval decision is made
        
        Args:
            state: Current workflow state
            
        Returns:
            Next node name
        """
        approval_status = state.get('approval_status', 'pending')
        
        if approval_status == 'approved':
            return "execute"
        else:
            # Rejected, end workflow
            return "end"
    
    def _route_after_execution(self, state: OptimizationState) -> str:
        """
        Route after execution completes
        
        Args:
            state: Current workflow state
            
        Returns:
            Next node name
        """
        if state.get('rollback_needed', False):
            return "rollback"
        else:
            return "learn"


def build_workflow_graph(
    workflow: BaseWorkflow,
    checkpointer: Optional[Any] = None
) -> StateGraph:
    """
    Factory function to build a workflow graph
    
    Args:
        workflow: Workflow implementation
        checkpointer: Checkpoint saver (optional)
        
    Returns:
        Compiled StateGraph
    """
    builder = WorkflowGraphBuilder(workflow, checkpointer)
    return builder.build()
