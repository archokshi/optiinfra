# PHASE2-2.7 PART1: LangGraph Workflow - Code Implementation Plan

**Phase**: PHASE2-2.7  
**Agent**: Performance Agent  
**Objective**: Implement LangGraph workflow for gradual rollout of optimizations  
**Estimated Time**: 30+25m (55 minutes total)  
**Priority**: HIGH  
**Dependencies**: PHASE2-2.6, 2.5, 2.4, 2.3, 2.2, 1.8

---

## Overview

This phase implements a **LangGraph-based workflow** for safely rolling out performance optimizations using a gradual deployment strategy (10% → 50% → 100%). The workflow orchestrates analysis, optimization, validation, and rollout with automatic rollback capabilities.

---

## LangGraph Workflow Overview

### What is LangGraph?

**LangGraph** is a library for building stateful, multi-step workflows with:
- **State Management**: Track workflow progress
- **Conditional Routing**: Dynamic decision-making
- **Human-in-the-Loop**: Approval gates
- **Error Handling**: Automatic retries and rollback
- **Persistence**: Resume from checkpoints

### Why LangGraph for Performance Optimization?

```
Traditional Approach (Risky):
Analyze → Optimize → Apply 100% → Hope it works ❌

LangGraph Workflow (Safe):
Analyze → Optimize → Validate → 10% → Monitor → 50% → Monitor → 100% ✅
                                    ↓           ↓           ↓
                                 Rollback    Rollback    Success
```

---

## Workflow Architecture

### State Machine Diagram

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  COLLECT        │ ← Collect metrics from instance
│  METRICS        │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  ANALYZE        │ ← Detect bottlenecks, calculate health score
│  PERFORMANCE    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  GENERATE       │ ← Create optimization recommendations
│  OPTIMIZATIONS  │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  APPROVAL       │ ← Human approval gate (optional)
│  GATE           │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  ROLLOUT        │ ← Gradual deployment
│  10%            │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  MONITOR        │ ← Check health, SLOs
│  10%            │
└──────┬──────────┘
       │
       ├─ Healthy? ──Yes──┐
       │                  │
       └─ No ─> ROLLBACK  │
                          │
                          ▼
                   ┌─────────────────┐
                   │  ROLLOUT        │
                   │  50%            │
                   └──────┬──────────┘
                          │
                          ▼
                   ┌─────────────────┐
                   │  MONITOR        │
                   │  50%            │
                   └──────┬──────────┘
                          │
                          ├─ Healthy? ──Yes──┐
                          │                  │
                          └─ No ─> ROLLBACK  │
                                             │
                                             ▼
                                      ┌─────────────────┐
                                      │  ROLLOUT        │
                                      │  100%           │
                                      └──────┬──────────┘
                                             │
                                             ▼
                                      ┌─────────────────┐
                                      │  SUCCESS        │
                                      │  COMPLETE       │
                                      └─────────────────┘
```

---

## Implementation Plan

### Step 1: Workflow State Models (5 minutes)

#### 1.1 Create src/models/workflow.py

```python
"""
Workflow State Models

Models for LangGraph workflow state.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from src.models.analysis import AnalysisResult
from src.models.optimization import OptimizationPlan


class WorkflowStatus(str, Enum):
    """Workflow status."""
    PENDING = "pending"
    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    OPTIMIZING = "optimizing"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ROLLING_OUT = "rolling_out"
    MONITORING = "monitoring"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class RolloutStage(str, Enum):
    """Rollout stage."""
    STAGE_10 = "10%"
    STAGE_50 = "50%"
    STAGE_100 = "100%"


class RolloutStatus(BaseModel):
    """Status of a rollout stage."""
    
    stage: RolloutStage
    status: str = Field(..., description="success, failed, in_progress")
    started_at: datetime
    completed_at: Optional[datetime] = None
    health_score_before: float
    health_score_after: Optional[float] = None
    metrics_snapshot: Optional[Dict[str, Any]] = None
    issues: List[str] = Field(default_factory=list)


class WorkflowState(BaseModel):
    """Complete workflow state."""
    
    # Workflow metadata
    workflow_id: str
    instance_id: str
    instance_type: str
    status: WorkflowStatus
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Analysis results
    analysis_result: Optional[AnalysisResult] = None
    
    # Optimization plan
    optimization_plan: Optional[OptimizationPlan] = None
    
    # Approval
    requires_approval: bool = True
    approved: Optional[bool] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    # Rollout tracking
    current_stage: Optional[RolloutStage] = None
    rollout_history: List[RolloutStatus] = Field(default_factory=list)
    
    # Configuration
    original_config: Optional[Dict[str, Any]] = None
    applied_config: Optional[Dict[str, Any]] = None
    
    # Monitoring
    health_threshold: float = 0.9  # Rollback if health drops below 90%
    monitoring_duration_seconds: int = 300  # 5 minutes per stage
    
    # Results
    final_health_score: Optional[float] = None
    total_improvement: Optional[str] = None
    error_message: Optional[str] = None


class WorkflowRequest(BaseModel):
    """Request to start a workflow."""
    
    instance_id: str
    instance_type: str
    requires_approval: bool = True
    auto_rollout: bool = False  # If True, skip approval
    monitoring_duration_seconds: int = 300
    health_threshold: float = 0.9
```

---

### Step 2: LangGraph Workflow Definition (10 minutes)

#### 2.1 Create src/workflows/__init__.py

```python
"""Workflows for Performance Agent."""
```

#### 2.2 Create src/workflows/optimization_workflow.py

```python
"""
Optimization Workflow

LangGraph workflow for gradual optimization rollout.
"""

import logging
from typing import TypedDict, Annotated
from datetime import datetime
import asyncio

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.models.workflow import (
    WorkflowState,
    WorkflowStatus,
    RolloutStage,
    RolloutStatus
)
from src.collectors.vllm_collector import VLLMCollector
from src.collectors.tgi_collector import TGICollector
from src.collectors.sglang_collector import SGLangCollector
from src.analysis.engine import AnalysisEngine
from src.optimization.engine import OptimizationEngine

logger = logging.getLogger(__name__)


class OptimizationWorkflow:
    """LangGraph workflow for optimization rollout."""
    
    def __init__(self):
        """Initialize workflow."""
        self.analysis_engine = AnalysisEngine()
        self.optimization_engine = OptimizationEngine()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        # Define the graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("collect_metrics", self.collect_metrics)
        workflow.add_node("analyze_performance", self.analyze_performance)
        workflow.add_node("generate_optimizations", self.generate_optimizations)
        workflow.add_node("await_approval", self.await_approval)
        workflow.add_node("rollout_10", lambda state: self.rollout_stage(state, RolloutStage.STAGE_10))
        workflow.add_node("monitor_10", lambda state: self.monitor_stage(state, RolloutStage.STAGE_10))
        workflow.add_node("rollout_50", lambda state: self.rollout_stage(state, RolloutStage.STAGE_50))
        workflow.add_node("monitor_50", lambda state: self.monitor_stage(state, RolloutStage.STAGE_50))
        workflow.add_node("rollout_100", lambda state: self.rollout_stage(state, RolloutStage.STAGE_100))
        workflow.add_node("complete", self.complete)
        workflow.add_node("rollback", self.rollback)
        
        # Define edges
        workflow.set_entry_point("collect_metrics")
        workflow.add_edge("collect_metrics", "analyze_performance")
        workflow.add_edge("analyze_performance", "generate_optimizations")
        
        # Conditional: approval required?
        workflow.add_conditional_edges(
            "generate_optimizations",
            self.should_await_approval,
            {
                "await_approval": "await_approval",
                "rollout": "rollout_10"
            }
        )
        
        # Conditional: approved?
        workflow.add_conditional_edges(
            "await_approval",
            self.is_approved,
            {
                "approved": "rollout_10",
                "rejected": END
            }
        )
        
        # 10% stage
        workflow.add_edge("rollout_10", "monitor_10")
        workflow.add_conditional_edges(
            "monitor_10",
            self.is_healthy,
            {
                "healthy": "rollout_50",
                "unhealthy": "rollback"
            }
        )
        
        # 50% stage
        workflow.add_edge("rollout_50", "monitor_50")
        workflow.add_conditional_edges(
            "monitor_50",
            self.is_healthy,
            {
                "healthy": "rollout_100",
                "unhealthy": "rollback"
            }
        )
        
        # 100% stage
        workflow.add_edge("rollout_100", "complete")
        workflow.add_edge("complete", END)
        workflow.add_edge("rollback", END)
        
        return workflow.compile(checkpointer=MemorySaver())
    
    async def collect_metrics(self, state: WorkflowState) -> WorkflowState:
        """Collect metrics from instance."""
        logger.info(f"[{state.workflow_id}] Collecting metrics from {state.instance_id}")
        
        state.status = WorkflowStatus.COLLECTING
        state.updated_at = datetime.utcnow()
        
        # Collect based on instance type
        # (Implementation similar to analysis API)
        
        return state
    
    async def analyze_performance(self, state: WorkflowState) -> WorkflowState:
        """Analyze performance and detect bottlenecks."""
        logger.info(f"[{state.workflow_id}] Analyzing performance")
        
        state.status = WorkflowStatus.ANALYZING
        state.updated_at = datetime.utcnow()
        
        # Run analysis engine
        # state.analysis_result = self.analysis_engine.analyze(...)
        
        return state
    
    async def generate_optimizations(self, state: WorkflowState) -> WorkflowState:
        """Generate optimization recommendations."""
        logger.info(f"[{state.workflow_id}] Generating optimizations")
        
        state.status = WorkflowStatus.OPTIMIZING
        state.updated_at = datetime.utcnow()
        
        # Run optimization engine
        # state.optimization_plan = self.optimization_engine.generate_plan(...)
        
        return state
    
    async def await_approval(self, state: WorkflowState) -> WorkflowState:
        """Wait for human approval."""
        logger.info(f"[{state.workflow_id}] Awaiting approval")
        
        state.status = WorkflowStatus.AWAITING_APPROVAL
        state.updated_at = datetime.utcnow()
        
        # This is a human-in-the-loop step
        # Approval will be provided via API
        
        return state
    
    async def rollout_stage(self, state: WorkflowState, stage: RolloutStage) -> WorkflowState:
        """Roll out optimization to a percentage of traffic."""
        logger.info(f"[{state.workflow_id}] Rolling out to {stage.value}")
        
        state.status = WorkflowStatus.ROLLING_OUT
        state.current_stage = stage
        state.updated_at = datetime.utcnow()
        
        # Create rollout status
        rollout_status = RolloutStatus(
            stage=stage,
            status="in_progress",
            started_at=datetime.utcnow(),
            health_score_before=state.analysis_result.overall_health_score if state.analysis_result else 0.0
        )
        
        # Apply configuration changes (simulated)
        # In production, this would call infrastructure APIs
        logger.info(f"[{state.workflow_id}] Applying config changes for {stage.value}")
        
        rollout_status.status = "success"
        rollout_status.completed_at = datetime.utcnow()
        state.rollout_history.append(rollout_status)
        
        return state
    
    async def monitor_stage(self, state: WorkflowState, stage: RolloutStage) -> WorkflowState:
        """Monitor health after rollout stage."""
        logger.info(f"[{state.workflow_id}] Monitoring {stage.value} for {state.monitoring_duration_seconds}s")
        
        state.status = WorkflowStatus.MONITORING
        state.updated_at = datetime.utcnow()
        
        # Simulate monitoring period
        await asyncio.sleep(min(state.monitoring_duration_seconds, 5))  # Cap at 5s for demo
        
        # Collect new metrics and analyze
        # new_health_score = ...
        new_health_score = 0.95  # Simulated
        
        # Update rollout status
        if state.rollout_history:
            state.rollout_history[-1].health_score_after = new_health_score
        
        logger.info(f"[{state.workflow_id}] Health score after {stage.value}: {new_health_score}")
        
        return state
    
    async def complete(self, state: WorkflowState) -> WorkflowState:
        """Complete the workflow successfully."""
        logger.info(f"[{state.workflow_id}] Workflow completed successfully")
        
        state.status = WorkflowStatus.COMPLETED
        state.updated_at = datetime.utcnow()
        state.final_health_score = state.rollout_history[-1].health_score_after if state.rollout_history else None
        
        return state
    
    async def rollback(self, state: WorkflowState) -> WorkflowState:
        """Rollback changes due to health issues."""
        logger.warning(f"[{state.workflow_id}] Rolling back changes")
        
        state.status = WorkflowStatus.ROLLED_BACK
        state.updated_at = datetime.utcnow()
        state.error_message = "Health score dropped below threshold, rolled back changes"
        
        # Restore original configuration
        logger.info(f"[{state.workflow_id}] Restoring original configuration")
        
        return state
    
    def should_await_approval(self, state: WorkflowState) -> str:
        """Check if approval is required."""
        if state.requires_approval and not state.approved:
            return "await_approval"
        return "rollout"
    
    def is_approved(self, state: WorkflowState) -> str:
        """Check if workflow is approved."""
        if state.approved:
            return "approved"
        return "rejected"
    
    def is_healthy(self, state: WorkflowState) -> str:
        """Check if instance is healthy after rollout."""
        if not state.rollout_history:
            return "unhealthy"
        
        latest_rollout = state.rollout_history[-1]
        if latest_rollout.health_score_after is None:
            return "unhealthy"
        
        if latest_rollout.health_score_after >= state.health_threshold:
            return "healthy"
        
        return "unhealthy"
    
    async def run(self, initial_state: WorkflowState) -> WorkflowState:
        """Run the workflow."""
        logger.info(f"Starting workflow {initial_state.workflow_id}")
        
        # Execute workflow
        result = await self.graph.ainvoke(initial_state)
        
        return result
```

---

### Step 3: Workflow Manager (5 minutes)

#### 3.1 Create src/workflows/manager.py

```python
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
        self.workflows: Dict[str, WorkflowState] = {}
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
        
        state = WorkflowState(
            workflow_id=workflow_id,
            instance_id=request.instance_id,
            instance_type=request.instance_type,
            status=WorkflowStatus.PENDING,
            requires_approval=request.requires_approval,
            monitoring_duration_seconds=request.monitoring_duration_seconds,
            health_threshold=request.health_threshold
        )
        
        # Store state
        self.workflows[workflow_id] = state
        
        # Start workflow asynchronously
        logger.info(f"Starting workflow {workflow_id} for {request.instance_id}")
        
        # Run workflow (in background for production)
        result = await self.optimization_workflow.run(state)
        
        # Update stored state
        self.workflows[workflow_id] = result
        
        return result
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get workflow state by ID."""
        return self.workflows.get(workflow_id)
    
    def approve_workflow(self, workflow_id: str, approved_by: str) -> Optional[WorkflowState]:
        """Approve a workflow."""
        state = self.workflows.get(workflow_id)
        if not state:
            return None
        
        state.approved = True
        state.approved_by = approved_by
        state.approved_at = datetime.utcnow()
        state.status = WorkflowStatus.APPROVED
        
        logger.info(f"Workflow {workflow_id} approved by {approved_by}")
        
        return state
    
    def reject_workflow(self, workflow_id: str) -> Optional[WorkflowState]:
        """Reject a workflow."""
        state = self.workflows.get(workflow_id)
        if not state:
            return None
        
        state.approved = False
        state.status = WorkflowStatus.REJECTED
        
        logger.info(f"Workflow {workflow_id} rejected")
        
        return state
```

---

### Step 4: API Endpoints (5 minutes)

#### 4.1 Create src/api/workflows.py

```python
"""
Workflow Endpoints

API endpoints for LangGraph workflows.
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
import logging

from src.models.workflow import WorkflowRequest, WorkflowState
from src.workflows.manager import WorkflowManager

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize manager
workflow_manager = WorkflowManager()


@router.post(
    "/workflows",
    response_model=WorkflowState,
    status_code=status.HTTP_201_CREATED,
    tags=["workflows"]
)
async def start_workflow(request: WorkflowRequest) -> WorkflowState:
    """
    Start a new optimization workflow.
    
    Args:
        request: Workflow request
        
    Returns:
        Workflow state
    """
    try:
        state = await workflow_manager.start_workflow(request)
        return state
    
    except Exception as e:
        logger.error(f"Failed to start workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start workflow: {str(e)}"
        )


@router.get(
    "/workflows/{workflow_id}",
    response_model=WorkflowState,
    tags=["workflows"]
)
def get_workflow(workflow_id: str) -> WorkflowState:
    """Get workflow state by ID."""
    state = workflow_manager.get_workflow(workflow_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    return state


@router.post(
    "/workflows/{workflow_id}/approve",
    response_model=WorkflowState,
    tags=["workflows"]
)
def approve_workflow(workflow_id: str, approved_by: str = "user") -> WorkflowState:
    """Approve a workflow."""
    state = workflow_manager.approve_workflow(workflow_id, approved_by)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    return state


@router.post(
    "/workflows/{workflow_id}/reject",
    response_model=WorkflowState,
    tags=["workflows"]
)
def reject_workflow(workflow_id: str) -> WorkflowState:
    """Reject a workflow."""
    state = workflow_manager.reject_workflow(workflow_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow {workflow_id} not found"
        )
    return state
```

---

## Success Criteria

### Functional Requirements
- ✅ LangGraph workflow executes end-to-end
- ✅ Gradual rollout (10% → 50% → 100%)
- ✅ Health monitoring between stages
- ✅ Automatic rollback on health degradation
- ✅ Human approval gate (optional)
- ✅ State persistence and recovery

### Non-Functional Requirements
- ✅ Workflow completes in < 20 minutes (with monitoring)
- ✅ Type hints throughout
- ✅ Comprehensive docstrings
- ✅ Tests pass with >80% coverage

---

## Dependencies

### New Dependencies
```
langgraph>=0.0.20
```

### From Previous Phases
- **PHASE2-2.6**: Optimization Engine
- **PHASE2-2.5**: Analysis Engine
- **PHASE2-2.4**: SGLang collector
- **PHASE2-2.3**: TGI collector
- **PHASE2-2.2**: vLLM collector

---

## Next Phase

**PHASE2-2.8**: Integration Testing - End-to-end testing of complete Performance Agent

---

**Status**: Ready for implementation  
**Estimated Completion**: 55 minutes  
**Dependencies**: PHASE2-2.6, 2.5, 2.4, 2.3, 2.2, LangGraph library
