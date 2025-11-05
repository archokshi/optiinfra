"""
Workflow Models

Pydantic models for optimization workflow state and results.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class OptimizationPriority(str, Enum):
    """Optimization priority levels."""
    
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class OptimizationAction(BaseModel):
    """Recommended optimization action."""
    
    title: str = Field(..., description="Action title")
    description: str = Field(..., description="Detailed description")
    priority: OptimizationPriority = Field(..., description="Priority level")
    expected_impact: str = Field(..., description="Expected impact")
    implementation_effort: str = Field(..., description="Implementation effort")
    category: str = Field(..., description="Action category")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisites")


class WorkflowResult(BaseModel):
    """Optimization workflow result."""
    
    workflow_id: str = Field(..., description="Workflow execution ID")
    status: WorkflowStatus = Field(..., description="Workflow status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Input data
    instance_id: str = Field(..., description="Instance identifier")
    
    # Analysis results
    primary_bottleneck: Optional[str] = Field(None, description="Primary bottleneck")
    health_score: Optional[float] = Field(None, description="Overall health score")
    
    # LLM-generated insights
    llm_insights: Optional[str] = Field(None, description="LLM-generated insights")
    
    # Recommended actions
    actions: List[OptimizationAction] = Field(default_factory=list, description="Optimization actions")
    
    # Execution metadata
    execution_time_ms: float = Field(..., description="Workflow execution time (ms)")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class WorkflowState(BaseModel):
    """Current workflow state."""
    
    workflow_id: str = Field(..., description="Workflow execution ID")
    status: WorkflowStatus = Field(default=WorkflowStatus.PENDING)
    current_step: str = Field(default="init", description="Current workflow step")
    
    # Collected data
    gpu_metrics: Optional[Dict[str, Any]] = Field(None, description="GPU metrics")
    system_metrics: Optional[Dict[str, Any]] = Field(None, description="System metrics")
    lmcache_metrics: Optional[Dict[str, Any]] = Field(None, description="LMCache metrics")
    analysis_result: Optional[Dict[str, Any]] = Field(None, description="Analysis result")
    
    # Generated insights
    llm_insights: Optional[str] = Field(None, description="LLM insights")
    
    # Errors
    errors: List[str] = Field(default_factory=list, description="Errors encountered")
