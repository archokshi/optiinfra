"""
Test StateGraph Compilation and Execution

Tests the full LangGraph StateGraph with conditional routing.
"""

import asyncio
from datetime import datetime
from src.workflows.states import create_initial_state, OptimizationState
from src.workflows.base import BaseWorkflow
from src.workflows.graph_builder import build_workflow_graph

# Use our custom MemoryCheckpointer (compatible with LangGraph 0.2.55)
from src.workflows.checkpointer_memory import MemoryCheckpointer


class TestOptimizationWorkflow(BaseWorkflow):
    """Test workflow for graph execution"""
    
    def __init__(self):
        super().__init__("test_optimization")
        self.execution_log = []
    
    async def analyze(self, state: OptimizationState) -> OptimizationState:
        """Analyze infrastructure"""
        self.execution_log.append("analyze")
        state['analysis_results'] = {
            "idle_instances": 3,
            "underutilized_instances": 5,
            "total_waste": 800.00
        }
        state['updated_at'] = datetime.now()
        print("   ✓ Analyze complete")
        return state
    
    async def generate_recommendations(self, state: OptimizationState) -> OptimizationState:
        """Generate recommendations"""
        self.execution_log.append("generate_recommendations")
        state['recommendations'] = [
            {"type": "spot_migration", "instance_id": "i-123", "savings": 400},
            {"type": "right_sizing", "instance_id": "i-456", "savings": 400}
        ]
        state['estimated_savings'] = 800.00
        state['confidence_score'] = 0.9
        state['updated_at'] = datetime.now()
        print("   ✓ Recommendations generated")
        return state
    
    async def execute(self, state: OptimizationState) -> OptimizationState:
        """Execute optimizations"""
        self.execution_log.append("execute")
        state['execution_results'] = {
            "migrated": ["i-123"],
            "resized": ["i-456"],
            "actual_savings": 750.00
        }
        state['execution_status'] = 'success'
        state['success'] = True
        state['updated_at'] = datetime.now()
        print("   ✓ Execution complete")
        return state


async def test_graph_compilation():
    """Test 1: Graph Compilation"""
    print("\n" + "="*60)
    print("TEST 1: StateGraph Compilation")
    print("="*60)
    
    try:
        workflow = TestOptimizationWorkflow()
        checkpointer = MemoryCheckpointer()
        
        # Build graph
        graph = build_workflow_graph(workflow, checkpointer)
        
        print("✅ StateGraph compiled successfully")
        print(f"   - Workflow type: {workflow.workflow_type}")
        print(f"   - Checkpointer: {type(checkpointer).__name__}")
        return True
    except Exception as e:
        print(f"❌ Graph compilation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_graph_execution_auto_approved():
    """Test 2: Graph Execution (Auto-Approved)"""
    print("\n" + "="*60)
    print("TEST 2: Graph Execution (Auto-Approved)")
    print("="*60)
    
    try:
        workflow = TestOptimizationWorkflow()
        checkpointer = MemoryCheckpointer()
        graph = build_workflow_graph(workflow, checkpointer)
        
        # Create initial state
        initial_state = create_initial_state(
            customer_id="test_customer",
            workflow_type="test_optimization",
            infrastructure={"instances": [{"id": "i-123"}]},
            current_costs={"total": 2000.00}
        )
        
        # Configure for auto-approval (low savings, high confidence)
        initial_state['estimated_savings'] = 800.00
        initial_state['confidence_score'] = 0.9
        
        config = {"configurable": {"thread_id": "test_auto_approved"}}
        
        print("\n   → Executing workflow...")
        
        # Execute graph
        final_state = None
        async for event in graph.astream(initial_state, config):
            # Each event is a dict with node name as key
            for node_name, node_state in event.items():
                print(f"   → Node: {node_name}")
                final_state = node_state
        
        # Verify execution
        assert final_state is not None, "No final state"
        assert final_state['success'] is True, "Workflow did not succeed"
        assert final_state['learned'] is True, "Learning did not complete"
        assert 'analysis_results' in final_state, "No analysis results"
        assert 'recommendations' in final_state, "No recommendations"
        assert 'execution_results' in final_state, "No execution results"
        
        print("\n✅ Graph execution completed successfully!")
        print(f"\n   📊 Results:")
        print(f"   - Workflow ID: {final_state['workflow_id']}")
        print(f"   - Customer ID: {final_state['customer_id']}")
        print(f"   - Analysis: ${final_state['analysis_results']['total_waste']} waste found")
        print(f"   - Recommendations: {len(final_state['recommendations'])} optimizations")
        print(f"   - Estimated Savings: ${final_state['estimated_savings']}")
        print(f"   - Actual Savings: ${final_state['execution_results']['actual_savings']}")
        print(f"   - Success: {final_state['success']}")
        print(f"   - Learned: {final_state['learned']}")
        print(f"   - Execution Log: {workflow.execution_log}")
        
        return True
    except Exception as e:
        print(f"\n❌ Graph execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_conditional_routing():
    """Test 3: Conditional Routing"""
    print("\n" + "="*60)
    print("TEST 3: Conditional Routing (High Savings → Approval Required)")
    print("="*60)
    
    try:
        workflow = TestOptimizationWorkflow()
        
        # Create state requiring approval
        state = create_initial_state(
            customer_id="test_customer",
            workflow_type="test_optimization",
            infrastructure={"instances": []},
            current_costs={"total": 5000.00}
        )
        
        # High savings should require approval
        state['estimated_savings'] = 2000.00
        state['confidence_score'] = 0.9
        
        result = await workflow.check_approval_needed(state)
        
        assert result['requires_approval'] is True, "Should require approval for high savings"
        assert result['approval_status'] == 'pending', "Should be pending approval"
        
        # Test routing decision
        route = workflow.should_execute(result)
        assert route == "wait_approval", f"Should route to wait_approval, got {route}"
        
        print("✅ Conditional routing works correctly")
        print(f"   - High savings (${state['estimated_savings']}) → Requires approval")
        print(f"   - Approval status: {result['approval_status']}")
        print(f"   - Route decision: {route}")
        
        return True
    except Exception as e:
        print(f"❌ Conditional routing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_checkpointing():
    """Test 4: Checkpointing"""
    print("\n" + "="*60)
    print("TEST 4: Checkpointing")
    print("="*60)
    
    try:
        checkpointer = MemoryCheckpointer()
        
        # Save checkpoint
        workflow_id = "test_checkpoint_123"
        checkpoint_data = {
            "id": "checkpoint_1",
            "v": 1,
            "ts": "2024-10-22T00:00:00Z",
            "channel_values": {
                "workflow_id": workflow_id,
                "step": "analyze",
                "progress": 0.5
            }
        }
        
        metadata = {"step": "analyze", "user": "test"}
        new_versions = {"channel1": 1}
        
        config = {"configurable": {"thread_id": workflow_id}}
        
        # Test put (with new_versions parameter)
        checkpointer.put(config, checkpoint_data, metadata, new_versions)
        print("   ✓ Checkpoint saved")
        
        # Test get
        loaded = checkpointer.get(config)
        assert loaded is not None, "Checkpoint not found"
        assert loaded['channel_values']['workflow_id'] == workflow_id, "Workflow ID mismatch"
        print("   ✓ Checkpoint retrieved")
        
        # Test get_tuple
        tuple_data = checkpointer.get_tuple(config)
        assert tuple_data is not None, "Checkpoint tuple not found"
        assert tuple_data['checkpoint']['channel_values']['workflow_id'] == workflow_id
        print("   ✓ Checkpoint tuple retrieved")
        
        # Test list
        checkpoints = list(checkpointer.list(config))
        assert len(checkpoints) == 1, f"Expected 1 checkpoint, got {len(checkpoints)}"
        print("   ✓ Checkpoints listed")
        
        # Test put_writes
        writes = [("channel1", {"value": 123}), ("channel2", {"value": 456})]
        checkpointer.put_writes(config, writes, "task_1", "path/to/task")
        print("   ✓ Writes stored")
        
        # Test delete_thread
        checkpointer.delete_thread(config)
        loaded_after_delete = checkpointer.get(config)
        assert loaded_after_delete is None, "Checkpoint should be deleted"
        print("   ✓ Thread deleted")
        
        print("\n✅ Checkpointing works correctly")
        print(f"   - Save: ✓")
        print(f"   - Load: ✓")
        print(f"   - List: ✓")
        print(f"   - Delete: ✓")
        
        return True
    except Exception as e:
        print(f"❌ Checkpointing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PHASE1-1.5: StateGraph Execution Tests")
    print("="*60)
    
    results = []
    
    # Test 1: Graph Compilation
    results.append(await test_graph_compilation())
    
    # Test 2: Graph Execution
    results.append(await test_graph_execution_auto_approved())
    
    # Test 3: Conditional Routing
    results.append(await test_conditional_routing())
    
    # Test 4: Checkpointing
    results.append(await test_checkpointing())
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    print(f"\n1. Graph Compilation: {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"2. Graph Execution: {'✅ PASS' if results[1] else '❌ FAIL'}")
    print(f"3. Conditional Routing: {'✅ PASS' if results[2] else '❌ FAIL'}")
    print(f"4. Checkpointing: {'✅ PASS' if results[3] else '❌ FAIL'}")
    
    if all(results):
        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED!")
        print("="*60)
        print("\n✅ LangGraph StateGraph is fully functional:")
        print("   • Graph compilation ✓")
        print("   • Workflow execution ✓")
        print("   • Conditional routing ✓")
        print("   • Checkpointing ✓")
        print("\n🚀 Ready for PHASE1-1.6 (Spot Migration Workflow)")
        return 0
    else:
        print("\n" + "="*60)
        print("❌ SOME TESTS FAILED")
        print("="*60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
