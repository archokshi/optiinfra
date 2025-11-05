"""
Workflow State Models

State definitions for LangGraph workflows.
"""

from typing import TypedDict, Optional, List
from enum import Enum


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    BASELINE_CHECKED = "baseline_checked"
    REGRESSION_CHECKED = "regression_checked"
    DECISION_MADE = "decision_made"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowState(TypedDict, total=False):
    """State for quality validation workflow."""
    
    # Request info
    request_id: str
    model_name: str
    config_hash: str
    prompt: str
    response: str
    
    # Quality metrics
    quality_metrics: Optional[dict]
    
    # Baseline
    baseline: Optional[dict]
    baseline_exists: bool
    
    # Regression
    regression_result: Optional[dict]
    
    # Validation
    validation_result: Optional[dict]
    decision: Optional[str]
    
    # Workflow state
    status: str
    current_step: str
    errors: List[str]
    
    # Metadata
    metadata: dict
