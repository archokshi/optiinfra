"""
Tests for LangGraph Workflows (Updated for LangGraph 0.2.55)

Tests state management, workflow execution, checkpointing, and conditional routing.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from src.workflows.states import (
    OptimizationState,
    SpotMigrationState,
    create_initial_state
)
from src.workflows.base import BaseWorkflow
from src.workflows.graph_builder import WorkflowGraphBuilder, build_workflow_graph
from src.workflows.checkpointer_simple import SimpleMemoryCheckpointer


# ==================== Mock Workflow for Testing ====================

class MockOptimizationWorkflow(BaseWorkflow):
    """Mock workflow for testing"""
    
    def __init__(self):
        super().__init__("mock_optimization")
    
    async def analyze(self, state: OptimizationState) -> OptimizationState:
        """Mock analyze step"""
        state['analysis_results'] = {
            'idle_instances': 5,
            'underutilized_instances': 10,
            'total_waste': 1500.00
        }
        state['updated_at'] = datetime.now()
        return state
    
    async def generate_recommendations(self, state: OptimizationState) -> OptimizationState:
        """Mock recommendation generation"""
        state['recommendations'] = [
            {
                'type': 'spot_migration',
                'instance_id': 'i-123456',
                'estimated_savings': 500.00
            },
            {
                'type': 'right_sizing',
                'instance_id': 'i-789012',
                'estimated_savings': 300.00
            }
        ]
        state['estimated_savings'] = 800.00
        state['confidence_score'] = 0.85
        state['updated_at'] = datetime.now()
        return state
    
    async def execute(self, state: OptimizationState) -> OptimizationState:
        """Mock execution"""
        state['execution_results'] = {
            'migrated_instances': ['i-123456'],
            'resized_instances': ['i-789012'],
            'actual_savings': 750.00
        }
        state['execution_status'] = 'success'
        state['success'] = True
        state['updated_at'] = datetime.now()
        return state


# ==================== Test State Definitions ====================

class TestStates:
    """Test state definitions and creation"""
    
    def test_create_initial_state(self):
        """Test creating initial workflow state"""
        state = create_initial_state(
            customer_id="cust_123",
            workflow_type="spot_migration",
            infrastructure={"instances": []},
            current_costs={"total": 5000.00}
        )
        
        assert state['customer_id'] == "cust_123"
        assert state['workflow_type'] == "spot_migration"
        assert 'workflow_id' in state
        assert state['success'] is False
        assert state['errors'] == []
        assert state['requires_approval'] is True
    
    def test_spot_migration_state_fields(self):
        """Test SpotMigrationState has required fields"""
        # This is a type check - just verify the TypedDict structure
        state_keys = SpotMigrationState.__annotations__.keys()
        
        assert 'instances_to_migrate' in state_keys
        assert 'spot_availability' in state_keys
        assert 'migration_plan' in state_keys
        assert 'migrated_instances' in state_keys
        assert 'failed_instances' in state_keys


# ==================== Test Base Workflow ====================

@pytest.mark.asyncio
class TestBaseWorkflow:
    """Test base workflow functionality"""
    
    @pytest.fixture
    def workflow(self):
        """Create mock workflow"""
        return MockOptimizationWorkflow()
    
    @pytest.fixture
    def initial_state(self):
        """Create initial state"""
        return create_initial_state(
            customer_id="cust_123",
            workflow_type="mock_optimization",
            infrastructure={"instances": []},
            current_costs={"total": 5000.00}
        )
    
    async def test_analyze_node(self, workflow, initial_state):
        """Test analyze node"""
        result = await workflow.analyze(initial_state)
        
        assert 'analysis_results' in result
        assert result['analysis_results']['total_waste'] == 1500.00
    
    async def test_generate_recommendations_node(self, workflow, initial_state):
        """Test recommendation generation"""
        # First analyze
        state = await workflow.analyze(initial_state)
        
        # Then generate recommendations
        result = await workflow.generate_recommendations(state)
        
        assert 'recommendations' in result
        assert len(result['recommendations']) == 2
        assert result['estimated_savings'] == 800.00
        assert result['confidence_score'] == 0.85
    
    async def test_check_approval_needed_high_savings(self, workflow, initial_state):
        """Test approval check with high savings"""
        initial_state['estimated_savings'] = 2000.00
        initial_state['confidence_score'] = 0.9
        
        result = await workflow.check_approval_needed(initial_state)
        
        assert result['requires_approval'] is True
        assert result['approval_status'] == 'pending'
    
    async def test_check_approval_needed_low_confidence(self, workflow, initial_state):
        """Test approval check with low confidence"""
        initial_state['estimated_savings'] = 500.00
        initial_state['confidence_score'] = 0.7
        
        result = await workflow.check_approval_needed(initial_state)
        
        assert result['requires_approval'] is True
    
    async def test_check_approval_needed_auto_approve(self, workflow, initial_state):
        """Test auto-approval for low-risk changes"""
        initial_state['estimated_savings'] = 500.00
        initial_state['confidence_score'] = 0.9
        
        result = await workflow.check_approval_needed(initial_state)
        
        assert result['requires_approval'] is False
        assert result['approval_status'] == 'auto-approved'
    
    async def test_execute_node(self, workflow, initial_state):
        """Test execution node"""
        initial_state['approval_status'] = 'approved'
        
        result = await workflow.execute(initial_state)
        
        assert 'execution_results' in result
        assert result['success'] is True
        assert result['execution_status'] == 'success'
    
    async def test_learn_node(self, workflow, initial_state):
        """Test learning node"""
        initial_state['success'] = True
        initial_state['estimated_savings'] = 800.00
        initial_state['execution_results'] = {'actual_savings': 750.00}
        
        result = await workflow.learn(initial_state)
        
        assert result['learned'] is True
        assert 'outcome' in result
        assert result['outcome']['success'] is True
    
    def test_should_execute_routing(self, workflow, initial_state):
        """Test conditional routing for execution"""
        # Test approved
        initial_state['approval_status'] = 'approved'
        assert workflow.should_execute(initial_state) == "execute"
        
        # Test auto-approved
        initial_state['approval_status'] = 'auto-approved'
        assert workflow.should_execute(initial_state) == "execute"
        
        # Test rejected
        initial_state['approval_status'] = 'rejected'
        assert workflow.should_execute(initial_state) == "end"
        
        # Test pending
        initial_state['approval_status'] = 'pending'
        assert workflow.should_execute(initial_state) == "wait_approval"
    
    def test_should_rollback_routing(self, workflow, initial_state):
        """Test conditional routing for rollback"""
        # Test rollback needed
        initial_state['rollback_needed'] = True
        initial_state['rollback_completed'] = False
        assert workflow.should_rollback(initial_state) == "rollback"
        
        # Test no rollback needed
        initial_state['rollback_needed'] = False
        assert workflow.should_rollback(initial_state) == "learn"
        
        # Test rollback already completed
        initial_state['rollback_needed'] = True
        initial_state['rollback_completed'] = True
        assert workflow.should_rollback(initial_state) == "learn"


# ==================== Test Graph Builder ====================

@pytest.mark.asyncio
class TestGraphBuilder:
    """Test workflow graph construction"""
    
    @pytest.fixture
    def workflow(self):
        """Create mock workflow"""
        return MockOptimizationWorkflow()
    
    @pytest.fixture
    def checkpointer(self):
        """Create simple memory checkpointer"""
        return SimpleMemoryCheckpointer()
    
    def test_build_graph(self, workflow, checkpointer):
        """Test graph construction"""
        builder = WorkflowGraphBuilder(workflow, checkpointer)
        graph = builder.build()
        
        assert graph is not None
        # Graph is compiled and ready to execute
    
    def test_build_graph_without_checkpointer(self, workflow):
        """Test graph construction without checkpointer"""
        builder = WorkflowGraphBuilder(workflow, None)
        graph = builder.build()
        
        assert graph is not None


# ==================== Test Checkpointer ====================

@pytest.mark.asyncio
class TestSimpleCheckpointer:
    """Test simple memory checkpointing"""
    
    @pytest.fixture
    def checkpointer(self):
        """Create test checkpointer"""
        return SimpleMemoryCheckpointer()
    
    async def test_save_and_load_checkpoint(self, checkpointer):
        """Test checkpoint persistence"""
        workflow_id = "test_wf_123"
        
        checkpoint = {
            "id": "checkpoint_1",
            "data": {
                "customer_id": "cust_123",
                "workflow_id": workflow_id,
                "workflow_type": "test"
            }
        }
        
        metadata = {
            "customer_id": "cust_123",
            "workflow_type": "test"
        }
        
        config = {
            "configurable": {
                "thread_id": workflow_id
            }
        }
        
        # Save checkpoint
        checkpointer.put(config, checkpoint, metadata)
        
        # Load checkpoint
        loaded = checkpointer.get(config)
        
        assert loaded is not None
        assert loaded['data']['workflow_id'] == workflow_id
    
    async def test_list_checkpoints(self, checkpointer):
        """Test listing checkpoints"""
        workflow_id = "test_wf_list_123"
        
        # Save multiple checkpoints
        for i in range(3):
            checkpoint = {
                "id": f"checkpoint_{i}",
                "data": {
                    "workflow_id": workflow_id,
                    "step": i
                }
            }
            
            config = {
                "configurable": {
                    "thread_id": workflow_id
                }
            }
            
            checkpointer.put(config, checkpoint, {})
        
        # List checkpoints
        config = {
            "configurable": {
                "thread_id": workflow_id
            }
        }
        
        checkpoints = checkpointer.list(config, limit=10)
        
        assert len(checkpoints) == 3
    
    async def test_delete_checkpoints(self, checkpointer):
        """Test deleting checkpoints"""
        workflow_id = "test_wf_delete_123"
        
        # Save checkpoint
        checkpoint = {
            "id": "checkpoint_1",
            "data": {"workflow_id": workflow_id}
        }
        
        config = {
            "configurable": {
                "thread_id": workflow_id
            }
        }
        
        checkpointer.put(config, checkpoint, {})
        
        # Delete checkpoints
        checkpointer.delete(config)
        
        # Verify deleted
        loaded = checkpointer.get(config)
        assert loaded is None


# ==================== Integration Tests ====================

@pytest.mark.asyncio
@pytest.mark.integration
class TestWorkflowIntegration:
    """Integration tests for complete workflows"""
    
    async def test_full_workflow_execution(self):
        """Test complete workflow execution"""
        workflow = MockOptimizationWorkflow()
        checkpointer = SimpleMemoryCheckpointer()
        
        # Create initial state
        initial_state = create_initial_state(
            customer_id="cust_123",
            workflow_type="mock_optimization",
            infrastructure={"instances": []},
            current_costs={"total": 5000.00}
        )
        
        # Execute workflow steps manually
        state = initial_state
        
        # Step 1: Analyze
        state = await workflow.analyze(state)
        assert 'analysis_results' in state
        
        # Step 2: Generate recommendations
        state = await workflow.generate_recommendations(state)
        assert 'recommendations' in state
        
        # Step 3: Check approval
        state = await workflow.check_approval_needed(state)
        
        # Step 4: Auto-approve for testing
        if state['requires_approval']:
            state['approval_status'] = 'approved'
        
        # Step 5: Execute
        state = await workflow.execute(state)
        assert state['success'] is True
        
        # Step 6: Learn
        state = await workflow.learn(state)
        assert state['learned'] is True
        
        print(f"\n✅ Full workflow completed successfully!")
        print(f"   - Estimated Savings: ${state['estimated_savings']}")
        print(f"   - Actual Savings: ${state['execution_results']['actual_savings']}")
        print(f"   - Success: {state['success']}")
