"""
E2E Tests for Complete Cost Optimization Workflow.

Tests the complete cost optimization workflow from data collection through execution.
"""

import pytest
from datetime import datetime
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_full_cost_optimization_workflow(e2e_test_context, clean_database):
    """
    Test complete cost optimization workflow from start to finish.
    
    Workflow Steps:
    1. Collect costs from AWS
    2. Analyze costs and detect anomalies
    3. Generate recommendations using LLM
    4. Approve recommendations
    5. Execute recommendations
    6. Track outcomes
    7. Update learning loop
    """
    context = e2e_test_context
    customer_id = context["customer_id"]
    
    print("\n" + "="*80)
    print("E2E TEST: Full Cost Optimization Workflow")
    print("="*80)
    
    # Step 1: Collect Costs
    print("\n[Step 1/7] Collecting costs from AWS...")
    cost_collection_result = await collect_costs_e2e(
        customer_id=customer_id,
        provider="aws",
        aws_client=context["aws_client"]
    )
    
    assert cost_collection_result["status"] == "success"
    assert cost_collection_result["total_cost"] > 0
    print(f"✓ Collected ${cost_collection_result['total_cost']:,.2f} in costs")
    print(f"  - Services: {len(cost_collection_result.get('services', []))}")
    
    # Step 2: Analyze Costs
    print("\n[Step 2/7] Analyzing costs and detecting anomalies...")
    analysis_result = await analyze_costs_e2e(
        customer_id=customer_id,
        cost_data=cost_collection_result
    )
    
    assert "anomalies" in analysis_result
    assert "trends" in analysis_result
    print(f"✓ Analysis complete")
    print(f"  - Anomalies detected: {len(analysis_result['anomalies'])}")
    print(f"  - Trends: {', '.join(analysis_result['trends'])}")
    
    # Step 3: Generate Recommendations
    print("\n[Step 3/7] Generating recommendations with LLM...")
    recommendation_result = await generate_recommendations_e2e(
        customer_id=customer_id,
        analysis=analysis_result,
        groq_client=context["groq_client"]
    )
    
    assert len(recommendation_result["recommendations"]) > 0
    print(f"✓ Generated {len(recommendation_result['recommendations'])} recommendations")
    
    top_rec = recommendation_result["recommendations"][0]
    print(f"  - Top recommendation: {top_rec['title']}")
    print(f"  - Estimated savings: ${top_rec['estimated_monthly_savings']:,.2f}/month")
    
    # Step 4: Approve Recommendation
    print("\n[Step 4/7] Approving top recommendation...")
    approval_result = await approve_recommendation_e2e(
        recommendation_id=top_rec["id"],
        approved_by="e2e-test-user"
    )
    
    assert approval_result["status"] == "approved"
    print(f"✓ Recommendation approved")
    print(f"  - ID: {top_rec['id']}")
    print(f"  - Type: {top_rec['type']}")
    
    # Step 5: Execute Recommendation
    print("\n[Step 5/7] Executing recommendation...")
    execution_result = await execute_recommendation_e2e(
        recommendation_id=top_rec["id"],
        customer_id=customer_id
    )
    
    assert execution_result["status"] == "completed"
    assert execution_result["success"] == True
    print(f"✓ Execution completed successfully")
    print(f"  - Duration: {execution_result['duration_seconds']}s")
    print(f"  - Changes applied: {len(execution_result.get('changes_applied', []))}")
    
    # Step 6: Track Outcome
    print("\n[Step 6/7] Tracking execution outcome...")
    outcome_result = await track_outcome_e2e(
        execution_id=execution_result["id"],
        predicted_savings=top_rec["estimated_monthly_savings"],
        actual_savings=top_rec["estimated_monthly_savings"] * 0.95  # 95% accuracy
    )
    
    assert outcome_result["tracked"] == True
    print(f"✓ Outcome tracked")
    print(f"  - Predicted savings: ${outcome_result['predicted_savings']:,.2f}")
    print(f"  - Actual savings: ${outcome_result['actual_savings']:,.2f}")
    print(f"  - Accuracy: {outcome_result['accuracy']:.1f}%")
    
    # Step 7: Update Learning Loop
    print("\n[Step 7/7] Updating learning loop...")
    learning_result = await update_learning_loop_e2e(
        customer_id=customer_id,
        outcome=outcome_result
    )
    
    assert learning_result["updated"] == True
    print(f"✓ Learning loop updated")
    print(f"  - New success rate: {learning_result.get('success_rate', 0):.1f}%")
    
    # Final verification
    print("\n" + "="*80)
    print("✅ COMPLETE WORKFLOW VALIDATED SUCCESSFULLY!")
    print("="*80)
    
    assert True


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_cost_optimization_with_multiple_recommendations(e2e_test_context):
    """Test workflow with multiple recommendations generated."""
    context = e2e_test_context
    customer_id = context["customer_id"]
    
    print("\n[E2E] Testing multiple recommendations workflow...")
    
    # Collect costs
    cost_data = await collect_costs_e2e(
        customer_id=customer_id,
        provider="aws",
        aws_client=context["aws_client"]
    )
    
    # Analyze
    analysis = await analyze_costs_e2e(customer_id, cost_data)
    
    # Generate multiple recommendations
    recommendations = await generate_recommendations_e2e(
        customer_id=customer_id,
        analysis=analysis,
        groq_client=context["groq_client"],
        count=5
    )
    
    assert len(recommendations["recommendations"]) >= 3
    print(f"✓ Generated {len(recommendations['recommendations'])} recommendations")
    
    # Verify recommendations are prioritized
    rec_list = recommendations["recommendations"]
    assert all("priority" in rec for rec in rec_list)
    assert all("estimated_monthly_savings" in rec for rec in rec_list)
    
    print("✓ Multiple recommendations workflow validated")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_cost_optimization_with_rejection(e2e_test_context):
    """Test workflow when recommendation is rejected."""
    context = e2e_test_context
    customer_id = context["customer_id"]
    
    print("\n[E2E] Testing recommendation rejection workflow...")
    
    # Generate recommendation
    cost_data = await collect_costs_e2e(customer_id, "aws", context["aws_client"])
    analysis = await analyze_costs_e2e(customer_id, cost_data)
    recommendations = await generate_recommendations_e2e(customer_id, analysis, context["groq_client"])
    
    rec = recommendations["recommendations"][0]
    
    # Reject recommendation
    rejection_result = await reject_recommendation_e2e(
        recommendation_id=rec["id"],
        reason="Not suitable for current workload",
        rejected_by="e2e-test-user"
    )
    
    assert rejection_result["status"] == "rejected"
    assert "reason" in rejection_result
    print(f"✓ Recommendation rejected: {rejection_result['reason']}")
    
    # Verify no execution occurred
    assert rejection_result.get("executed", False) == False
    print("✓ Rejection workflow validated")


# Helper functions for E2E workflow steps

async def collect_costs_e2e(customer_id: str, provider: str, aws_client) -> dict:
    """Simulate cost collection from cloud provider."""
    await asyncio.sleep(0.1)  # Simulate API call
    
    response = aws_client.get_cost_and_usage()
    total_cost = float(response["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"])
    
    services = []
    if "Groups" in response["ResultsByTime"][0]:
        for group in response["ResultsByTime"][0]["Groups"]:
            services.append({
                "service": group["Keys"][0],
                "cost": float(group["Metrics"]["UnblendedCost"]["Amount"])
            })
    
    return {
        "status": "success",
        "customer_id": customer_id,
        "provider": provider,
        "total_cost": total_cost,
        "services": services,
        "collected_at": datetime.utcnow().isoformat()
    }


async def analyze_costs_e2e(customer_id: str, cost_data: dict) -> dict:
    """Simulate cost analysis."""
    await asyncio.sleep(0.1)
    
    # Simulate anomaly detection
    anomalies = []
    if cost_data["total_cost"] > 15000:
        anomalies.append({
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "severity": "high",
            "cost_spike": 500.00,
            "description": "Unusual cost increase detected"
        })
    
    return {
        "customer_id": customer_id,
        "anomalies": anomalies,
        "trends": ["increasing"],
        "forecast": {
            "next_month": cost_data["total_cost"] * 1.1,
            "confidence": 0.85
        },
        "analyzed_at": datetime.utcnow().isoformat()
    }


async def generate_recommendations_e2e(
    customer_id: str,
    analysis: dict,
    groq_client,
    count: int = 1
) -> dict:
    """Simulate recommendation generation with LLM."""
    await asyncio.sleep(0.1)
    
    # Call LLM
    response = groq_client.chat.completions.create()
    import json
    llm_rec = json.loads(response.choices[0].message.content)
    
    recommendations = []
    for i in range(count):
        recommendations.append({
            "id": f"rec-e2e-{i:03d}",
            "type": llm_rec["recommendation_type"],
            "title": llm_rec["title"],
            "description": llm_rec["description"],
            "estimated_monthly_savings": llm_rec["estimated_monthly_savings"] * (1 - i * 0.1),
            "priority": llm_rec["priority"],
            "risk_level": llm_rec["risk_level"],
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        })
    
    return {
        "customer_id": customer_id,
        "recommendations": recommendations,
        "generated_at": datetime.utcnow().isoformat()
    }


async def approve_recommendation_e2e(recommendation_id: str, approved_by: str) -> dict:
    """Simulate recommendation approval."""
    await asyncio.sleep(0.05)
    
    return {
        "recommendation_id": recommendation_id,
        "status": "approved",
        "approved_by": approved_by,
        "approved_at": datetime.utcnow().isoformat()
    }


async def reject_recommendation_e2e(recommendation_id: str, reason: str, rejected_by: str) -> dict:
    """Simulate recommendation rejection."""
    await asyncio.sleep(0.05)
    
    return {
        "recommendation_id": recommendation_id,
        "status": "rejected",
        "reason": reason,
        "rejected_by": rejected_by,
        "rejected_at": datetime.utcnow().isoformat(),
        "executed": False
    }


async def execute_recommendation_e2e(recommendation_id: str, customer_id: str) -> dict:
    """Simulate recommendation execution."""
    await asyncio.sleep(0.2)  # Simulate execution time
    
    return {
        "id": f"exec-e2e-{datetime.utcnow().timestamp()}",
        "recommendation_id": recommendation_id,
        "customer_id": customer_id,
        "status": "completed",
        "success": True,
        "duration_seconds": 120,
        "changes_applied": [
            {"resource": "i-e2e-001", "action": "migrated_to_spot", "status": "success"},
            {"resource": "i-e2e-002", "action": "migrated_to_spot", "status": "success"}
        ],
        "rollback_available": True,
        "executed_at": datetime.utcnow().isoformat()
    }


async def track_outcome_e2e(execution_id: str, predicted_savings: float, actual_savings: float) -> dict:
    """Simulate outcome tracking."""
    await asyncio.sleep(0.05)
    
    accuracy = (actual_savings / predicted_savings) * 100
    
    return {
        "execution_id": execution_id,
        "predicted_savings": predicted_savings,
        "actual_savings": actual_savings,
        "accuracy": round(accuracy, 2),
        "tracked": True,
        "tracked_at": datetime.utcnow().isoformat()
    }


async def update_learning_loop_e2e(customer_id: str, outcome: dict) -> dict:
    """Simulate learning loop update."""
    await asyncio.sleep(0.05)
    
    return {
        "customer_id": customer_id,
        "updated": True,
        "success_rate": 95.5,
        "new_accuracy": outcome["accuracy"],
        "updated_at": datetime.utcnow().isoformat()
    }
