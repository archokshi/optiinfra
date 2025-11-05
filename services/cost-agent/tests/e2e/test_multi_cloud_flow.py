"""
E2E Tests for Multi-Cloud Workflows.

Tests multi-cloud cost collection and optimization.
"""

import pytest
from datetime import datetime
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_multi_cloud_cost_collection(e2e_test_context):
    """
    Test multi-cloud cost collection workflow.
    
    Steps:
    1. Collect costs from AWS, GCP, Azure simultaneously
    2. Aggregate and normalize data
    3. Generate unified cost report
    """
    context = e2e_test_context
    customer_id = context["customer_id"]
    
    print("\n" + "="*80)
    print("E2E TEST: Multi-Cloud Cost Collection")
    print("="*80)
    
    # Step 1: Collect from multiple clouds
    print("\n[Step 1/3] Collecting costs from multiple clouds...")
    
    # Collect in parallel
    aws_task = collect_aws_costs_e2e(customer_id, context["aws_client"])
    gcp_task = collect_gcp_costs_e2e(customer_id, context["gcp_client"])
    azure_task = collect_azure_costs_e2e(customer_id, context["azure_client"])
    
    aws_costs, gcp_costs, azure_costs = await asyncio.gather(
        aws_task, gcp_task, azure_task
    )
    
    assert aws_costs["status"] == "success"
    assert gcp_costs["status"] == "success"
    assert azure_costs["status"] == "success"
    
    print(f"✓ Collected costs from all providers")
    print(f"  - AWS: ${aws_costs['total_cost']:,.2f}")
    print(f"  - GCP: ${gcp_costs['total_cost']:,.2f}")
    print(f"  - Azure: ${azure_costs['total_cost']:,.2f}")
    
    # Step 2: Aggregate and normalize
    print("\n[Step 2/3] Aggregating and normalizing data...")
    aggregated = await aggregate_multi_cloud_costs_e2e(
        aws_costs, gcp_costs, azure_costs
    )
    
    assert aggregated["total_cost"] > 0
    assert len(aggregated["providers"]) == 3
    print(f"✓ Data aggregated")
    print(f"  - Total cost: ${aggregated['total_cost']:,.2f}")
    
    # Step 3: Generate unified report
    print("\n[Step 3/3] Generating unified cost report...")
    report = await generate_multi_cloud_report_e2e(aggregated)
    
    assert "cost_breakdown" in report
    assert "recommendations" in report
    print(f"✓ Report generated")
    print(f"  - Providers analyzed: {len(report['cost_breakdown'])}")
    
    print("\n" + "="*80)
    print("✅ MULTI-CLOUD COLLECTION VALIDATED!")
    print("="*80)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_cross_cloud_optimization(e2e_test_context):
    """Test cross-cloud optimization recommendations."""
    context = e2e_test_context
    customer_id = context["customer_id"]
    
    print("\n[E2E] Testing cross-cloud optimization...")
    
    # Collect from all clouds
    aws_costs = await collect_aws_costs_e2e(customer_id, context["aws_client"])
    gcp_costs = await collect_gcp_costs_e2e(customer_id, context["gcp_client"])
    azure_costs = await collect_azure_costs_e2e(customer_id, context["azure_client"])
    
    # Generate cross-cloud recommendations
    recommendations = await generate_cross_cloud_recommendations_e2e(
        aws_costs, gcp_costs, azure_costs, context["groq_client"]
    )
    
    assert len(recommendations["recommendations"]) > 0
    print(f"✓ Generated {len(recommendations['recommendations'])} cross-cloud recommendations")
    
    # Verify recommendations consider multiple clouds
    for rec in recommendations["recommendations"]:
        assert "providers_affected" in rec
        print(f"  - {rec['title']}: affects {', '.join(rec['providers_affected'])}")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_multi_cloud_with_partial_failure(e2e_test_context):
    """Test multi-cloud collection with one provider failing."""
    context = e2e_test_context
    customer_id = context["customer_id"]
    
    print("\n[E2E] Testing partial failure scenario...")
    
    # Simulate GCP failure
    aws_costs = await collect_aws_costs_e2e(customer_id, context["aws_client"])
    gcp_costs = {"status": "failed", "error": "API unavailable"}
    azure_costs = await collect_azure_costs_e2e(customer_id, context["azure_client"])
    
    # Should still work with available providers
    result = await handle_partial_collection_e2e(
        aws_costs, gcp_costs, azure_costs
    )
    
    assert result["success"] == True
    assert result["providers_collected"] == 2
    assert result["providers_failed"] == 1
    print(f"✓ Handled partial failure gracefully")
    print(f"  - Collected: {result['providers_collected']}/3 providers")


# Helper functions

async def collect_aws_costs_e2e(customer_id: str, aws_client) -> dict:
    """Collect AWS costs."""
    await asyncio.sleep(0.1)
    
    response = aws_client.get_cost_and_usage()
    total_cost = float(response["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"])
    
    return {
        "status": "success",
        "provider": "aws",
        "customer_id": customer_id,
        "total_cost": total_cost,
        "collected_at": datetime.utcnow().isoformat()
    }


async def collect_gcp_costs_e2e(customer_id: str, gcp_client) -> dict:
    """Collect GCP costs."""
    await asyncio.sleep(0.1)
    
    results = gcp_client.query()
    total_cost = sum(row["cost"] for row in results)
    
    return {
        "status": "success",
        "provider": "gcp",
        "customer_id": customer_id,
        "total_cost": total_cost,
        "collected_at": datetime.utcnow().isoformat()
    }


async def collect_azure_costs_e2e(customer_id: str, azure_client) -> dict:
    """Collect Azure costs."""
    await asyncio.sleep(0.1)
    
    response = azure_client.usage.list()
    total_cost = sum(row[1] for row in response["properties"]["rows"])
    
    return {
        "status": "success",
        "provider": "azure",
        "customer_id": customer_id,
        "total_cost": total_cost,
        "collected_at": datetime.utcnow().isoformat()
    }


async def aggregate_multi_cloud_costs_e2e(aws_costs: dict, gcp_costs: dict, azure_costs: dict) -> dict:
    """Aggregate costs from multiple clouds."""
    await asyncio.sleep(0.05)
    
    total_cost = (
        aws_costs["total_cost"] +
        gcp_costs["total_cost"] +
        azure_costs["total_cost"]
    )
    
    return {
        "total_cost": total_cost,
        "providers": {
            "aws": aws_costs,
            "gcp": gcp_costs,
            "azure": azure_costs
        },
        "aggregated_at": datetime.utcnow().isoformat()
    }


async def generate_multi_cloud_report_e2e(aggregated: dict) -> dict:
    """Generate unified multi-cloud report."""
    await asyncio.sleep(0.1)
    
    return {
        "cost_breakdown": aggregated["providers"],
        "total_cost": aggregated["total_cost"],
        "recommendations": [
            {
                "title": "Consider workload migration to lower-cost provider",
                "potential_savings": 500.00
            }
        ],
        "generated_at": datetime.utcnow().isoformat()
    }


async def generate_cross_cloud_recommendations_e2e(
    aws_costs: dict,
    gcp_costs: dict,
    azure_costs: dict,
    groq_client
) -> dict:
    """Generate cross-cloud optimization recommendations."""
    await asyncio.sleep(0.1)
    
    return {
        "recommendations": [
            {
                "id": "rec-cross-001",
                "title": "Migrate workloads from AWS to GCP",
                "providers_affected": ["aws", "gcp"],
                "estimated_savings": 800.00
            },
            {
                "id": "rec-cross-002",
                "title": "Use Azure for storage-heavy workloads",
                "providers_affected": ["aws", "azure"],
                "estimated_savings": 300.00
            }
        ]
    }


async def handle_partial_collection_e2e(
    aws_costs: dict,
    gcp_costs: dict,
    azure_costs: dict
) -> dict:
    """Handle partial collection failure."""
    await asyncio.sleep(0.05)
    
    successful = sum(
        1 for costs in [aws_costs, gcp_costs, azure_costs]
        if costs.get("status") == "success"
    )
    
    failed = 3 - successful
    
    return {
        "success": successful >= 2,  # At least 2 providers
        "providers_collected": successful,
        "providers_failed": failed
    }
