"""
Workflows package for LangGraph-based optimization workflows.
"""

# Legacy workflows (from skeleton)
from src.workflows.cost_optimization import (
    cost_optimization_workflow,
    create_cost_optimization_workflow,
)
from src.workflows.spot_migration import (
    create_spot_migration_workflow,
    run_spot_migration_demo,
    spot_migration_workflow,
)

# New LangGraph components (PHASE1-1.5)
from .states import (
    OptimizationState,
    SpotMigrationState,
    ReservedInstanceState,
    RightSizingState,
    create_initial_state,
)
from .base import BaseWorkflow
from .checkpointer import PostgreSQLCheckpointer, create_checkpointer
from .graph_builder import WorkflowGraphBuilder, build_workflow_graph

__all__ = [
    # Legacy
    "create_cost_optimization_workflow",
    "cost_optimization_workflow",
    "create_spot_migration_workflow",
    "spot_migration_workflow",
    "run_spot_migration_demo",
    # New LangGraph
    "OptimizationState",
    "SpotMigrationState",
    "ReservedInstanceState",
    "RightSizingState",
    "create_initial_state",
    "BaseWorkflow",
    "PostgreSQLCheckpointer",
    "create_checkpointer",
    "WorkflowGraphBuilder",
    "build_workflow_graph",
]
