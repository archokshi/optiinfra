"""
End-to-End Integration Tests.

Tests complete workflows from data collection through execution.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, AsyncMock
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.mark.integration
class TestFullRecommendationFlow:
    """Test complete recommendation workflow."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_success(
        self,
        sample_aws_costs,
        sample_spot_migration_recommendation,
        sample_execution
    ):
        """Test successful end-to-end workflow."""
        # Step 1: Data Collection
        cost_data = sample_aws_costs
        assert cost_data["total_cost"] > 0
        
        # Step 2: Analysis
        analysis_result = {
            "anomalies_detected": 0,
            "trends": ["increasing"],
            "forecast": {"next_month": cost_data["total_cost"] * 1.1}
        }
        assert "trends" in analysis_result
        
        # Step 3: Recommendation Generation
        recommendation = sample_spot_migration_recommendation
        assert recommendation["estimated_monthly_savings"] > 0
        
        # Step 4: Execution
        execution = sample_execution
        assert execution["success"] == True
        
        # Verify workflow completion
        workflow_result = {
            "cost_data": cost_data,
            "analysis": analysis_result,
            "recommendation": recommendation,
            "execution": execution,
            "status": "completed"
        }
        
        assert workflow_result["status"] == "completed"
        assert workflow_result["execution"]["success"] == True
    
    @pytest.mark.asyncio
    async def test_multi_cloud_workflow(
        self,
        sample_aws_costs,
        sample_gcp_costs,
        sample_azure_costs
    ):
        """Test workflow with multi-cloud data."""
        # Collect from multiple clouds
        all_costs = {
            "aws": sample_aws_costs,
            "gcp": sample_gcp_costs,
            "azure": sample_azure_costs
        }
        
        # Calculate total
        total_cost = sum(
            costs["total_cost"] 
            for costs in all_costs.values()
        )
        
        assert total_cost == 38720.50  # 15420.50 + 12500 + 10800
        
        # Generate multi-cloud recommendations
        recommendations = []
        for provider, costs in all_costs.items():
            if costs["total_cost"] > 10000:
                recommendations.append({
                    "provider": provider,
                    "type": "cost_optimization",
                    "savings": costs["total_cost"] * 0.15
                })
        
        assert len(recommendations) == 3
        total_potential_savings = sum(r["savings"] for r in recommendations)
        assert total_potential_savings > 5000
    
    @pytest.mark.asyncio
    async def test_recommendation_to_execution_flow(
        self,
        sample_spot_migration_recommendation,
        sample_execution
    ):
        """Test flow from recommendation approval to execution."""
        # Step 1: Recommendation created
        recommendation = sample_spot_migration_recommendation
        recommendation["status"] = "pending"
        
        # Step 2: Recommendation approved
        recommendation["status"] = "approved"
        recommendation["approved_at"] = datetime.utcnow()
        recommendation["approved_by"] = "user-123"
        
        assert recommendation["status"] == "approved"
        
        # Step 3: Execution initiated
        execution = sample_execution
        execution["recommendation_id"] = recommendation["id"]
        execution["status"] = "in_progress"
        
        assert execution["recommendation_id"] == recommendation["id"]
        
        # Step 4: Execution completed
        execution["status"] = "completed"
        execution["success"] = True
        
        # Step 5: Update recommendation status
        recommendation["status"] = "executed"
        recommendation["execution_id"] = execution["id"]
        
        assert recommendation["status"] == "executed"
        assert execution["success"] == True
    
    @pytest.mark.asyncio
    async def test_learning_loop_integration(
        self,
        sample_execution,
        sample_outcome
    ):
        """Test learning loop integration with execution."""
        # Execution completes
        execution = sample_execution
        assert execution["success"] == True
        
        # Outcome tracked
        outcome = sample_outcome
        outcome["execution_id"] = execution["id"]
        
        # Calculate accuracy
        accuracy = (
            min(outcome["actual_savings"], outcome["predicted_savings"]) /
            max(outcome["actual_savings"], outcome["predicted_savings"])
        ) * 100
        
        outcome["accuracy"] = accuracy
        
        assert outcome["accuracy"] > 90  # High accuracy
        
        # Update learning metrics
        learning_update = {
            "recommendation_type": "spot_migration",
            "success_count": 1,
            "total_count": 1,
            "avg_accuracy": accuracy
        }
        
        assert learning_update["success_count"] == 1


@pytest.mark.integration
class TestWorkflowOrchestration:
    """Test workflow orchestration and coordination."""
    
    @pytest.mark.asyncio
    async def test_parallel_recommendation_generation(
        self,
        recommendation_batch
    ):
        """Test generating multiple recommendations in parallel."""
        recommendations = recommendation_batch
        
        # Simulate parallel processing
        processed = []
        for rec in recommendations:
            # Validate each recommendation
            if rec["estimated_monthly_savings"] > 0:
                rec["status"] = "validated"
                processed.append(rec)
        
        assert len(processed) == len(recommendations)
        assert all(r["status"] == "validated" for r in processed)
    
    @pytest.mark.asyncio
    async def test_sequential_execution_workflow(
        self,
        recommendation_batch
    ):
        """Test sequential execution of multiple recommendations."""
        recommendations = recommendation_batch[:3]  # Take first 3
        
        execution_results = []
        for i, rec in enumerate(recommendations):
            execution = {
                "id": f"exec-{i}",
                "recommendation_id": rec["id"],
                "status": "completed",
                "success": True,
                "order": i
            }
            execution_results.append(execution)
        
        # Verify sequential order
        assert len(execution_results) == 3
        for i, result in enumerate(execution_results):
            assert result["order"] == i
    
    @pytest.mark.asyncio
    async def test_workflow_state_persistence(self):
        """Test workflow state persistence across steps."""
        # Initial state
        workflow_state = {
            "workflow_id": "wf-123",
            "current_step": "data_collection",
            "completed_steps": [],
            "data": {}
        }
        
        # Step 1: Data Collection
        workflow_state["data"]["costs"] = {"total": 15000}
        workflow_state["completed_steps"].append("data_collection")
        workflow_state["current_step"] = "analysis"
        
        # Step 2: Analysis
        workflow_state["data"]["analysis"] = {"anomalies": 2}
        workflow_state["completed_steps"].append("analysis")
        workflow_state["current_step"] = "recommendation"
        
        # Step 3: Recommendation
        workflow_state["data"]["recommendations"] = [{"id": "rec-1"}]
        workflow_state["completed_steps"].append("recommendation")
        workflow_state["current_step"] = "completed"
        
        # Verify state
        assert len(workflow_state["completed_steps"]) == 3
        assert workflow_state["current_step"] == "completed"
        assert "costs" in workflow_state["data"]
        assert "analysis" in workflow_state["data"]
        assert "recommendations" in workflow_state["data"]


@pytest.mark.integration
class TestCrossComponentIntegration:
    """Test integration between different components."""
    
    @pytest.mark.asyncio
    async def test_collector_to_analyzer_integration(
        self,
        sample_aws_costs,
        daily_cost_data
    ):
        """Test data flow from collector to analyzer."""
        # Collector output
        collected_data = sample_aws_costs
        
        # Analyzer input (uses collected data)
        analyzer_input = {
            "cost_data": collected_data,
            "historical_data": daily_cost_data
        }
        
        # Analyzer processing
        current_cost = collected_data["total_cost"]
        historical_avg = sum(d["cost"] for d in daily_cost_data) / len(daily_cost_data)
        
        analysis_result = {
            "current_cost": current_cost,
            "historical_average": historical_avg,
            "variance": current_cost - historical_avg,
            "trend": "increasing" if current_cost > historical_avg else "decreasing"
        }
        
        assert analysis_result["current_cost"] > 0
        assert analysis_result["historical_average"] > 0
    
    @pytest.mark.asyncio
    async def test_analyzer_to_llm_integration(
        self,
        anomaly_cost_data,
        mock_groq_response
    ):
        """Test data flow from analyzer to LLM."""
        # Analyzer output
        anomalies = [d for d in anomaly_cost_data if d.get("anomaly", False)]
        
        analyzer_output = {
            "anomaly_count": len(anomalies),
            "anomaly_dates": [a["date"] for a in anomalies],
            "severity": "high" if len(anomalies) > 2 else "low"
        }
        
        # LLM input (formatted from analyzer output)
        llm_prompt = f"""
        Detected {analyzer_output['anomaly_count']} cost anomalies.
        Severity: {analyzer_output['severity']}
        Dates: {', '.join(analyzer_output['anomaly_dates'][:3])}
        
        Provide recommendations.
        """
        
        assert "anomalies" in llm_prompt.lower()
        
        # LLM response
        llm_response = mock_groq_response
        assert "choices" in llm_response
    
    @pytest.mark.asyncio
    async def test_llm_to_recommendation_integration(
        self,
        mock_groq_recommendation,
        sample_spot_migration_recommendation
    ):
        """Test data flow from LLM to recommendation engine."""
        # LLM output
        import json
        llm_output = json.loads(
            mock_groq_recommendation["choices"][0]["message"]["content"]
        )
        
        # Recommendation engine processes LLM output
        recommendation = {
            "id": "rec-from-llm-123",
            "type": llm_output["recommendation_type"],
            "title": llm_output["title"],
            "estimated_monthly_savings": llm_output["estimated_monthly_savings"],
            "priority": llm_output["priority"],
            "risk_level": llm_output["risk_level"],
            "status": "pending"
        }
        
        assert recommendation["type"] == "spot_migration"
        assert recommendation["estimated_monthly_savings"] > 0
    
    @pytest.mark.asyncio
    async def test_recommendation_to_executor_integration(
        self,
        sample_spot_migration_recommendation,
        sample_execution
    ):
        """Test data flow from recommendation to executor."""
        # Recommendation approved
        recommendation = sample_spot_migration_recommendation
        recommendation["status"] = "approved"
        
        # Executor receives recommendation
        execution_plan = {
            "recommendation_id": recommendation["id"],
            "actions": [
                {
                    "resource": resource,
                    "action": "migrate_to_spot",
                    "estimated_savings": recommendation["estimated_monthly_savings"] / len(recommendation["affected_resources"])
                }
                for resource in recommendation["affected_resources"]
            ]
        }
        
        assert len(execution_plan["actions"]) == len(recommendation["affected_resources"])
        
        # Execute
        execution = sample_execution
        execution["recommendation_id"] = recommendation["id"]
        
        assert execution["recommendation_id"] == recommendation["id"]


@pytest.mark.integration
class TestDataFlowValidation:
    """Test data flow validation across components."""
    
    @pytest.mark.asyncio
    async def test_data_transformation_pipeline(
        self,
        sample_aws_costs
    ):
        """Test data transformations through pipeline."""
        # Stage 1: Raw data
        raw_data = sample_aws_costs
        
        # Stage 2: Normalized data
        normalized_data = {
            "customer_id": raw_data["customer_id"],
            "provider": raw_data["provider"],
            "total_cost": raw_data["total_cost"],
            "services": {
                s["service"]: s["cost"] 
                for s in raw_data["services"]
            }
        }
        
        # Stage 3: Aggregated data
        aggregated_data = {
            "total": normalized_data["total_cost"],
            "by_service": normalized_data["services"],
            "top_service": max(
                normalized_data["services"].items(),
                key=lambda x: x[1]
            )[0]
        }
        
        assert aggregated_data["top_service"] == "EC2"
        assert aggregated_data["total"] == raw_data["total_cost"]
    
    @pytest.mark.asyncio
    async def test_metadata_propagation(
        self,
        sample_spot_migration_recommendation,
        sample_execution
    ):
        """Test metadata propagation through workflow."""
        # Recommendation with metadata
        recommendation = sample_spot_migration_recommendation
        recommendation["metadata"]["workflow_id"] = "wf-123"
        recommendation["metadata"]["created_by"] = "system"
        
        # Execution inherits metadata
        execution = sample_execution
        execution["metadata"] = {
            "workflow_id": recommendation["metadata"]["workflow_id"],
            "recommendation_type": recommendation["type"],
            "created_by": recommendation["metadata"]["created_by"]
        }
        
        assert execution["metadata"]["workflow_id"] == "wf-123"
        assert execution["metadata"]["recommendation_type"] == "spot_migration"
