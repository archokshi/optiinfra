"""
Analysis endpoint for cost optimization.
"""

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from langchain_core.runnables import RunnableConfig

from src.models.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    RecommendationResponse,
)
from src.workflows.cost_optimization import cost_optimization_workflow
from src.workflows.state import CostOptimizationState, ResourceInfo

router = APIRouter()
logger = logging.getLogger("cost_agent")


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_costs(request: AnalysisRequest) -> AnalysisResponse:
    """
    Analyze resources for cost optimization opportunities.

    This endpoint runs the LangGraph workflow to:
    1. Analyze resources for waste
    2. Generate recommendations
    3. Create executive summary

    Args:
        request: Analysis request with resources to analyze

    Returns:
        AnalysisResponse: Complete analysis with recommendations
    """
    request_id = f"req-{uuid.uuid4().hex[:8]}"
    logger.info(
        f"Starting cost analysis {request_id} for {len(request.resources)} resources"
    )

    try:
        # Convert request to workflow state
        resources: list[ResourceInfo] = [
            {
                "resource_id": r.resource_id,
                "resource_type": r.resource_type,
                "provider": r.provider,
                "region": r.region,
                "cost_per_month": r.cost_per_month,
                "utilization": r.utilization,
                "tags": r.tags,
            }
            for r in request.resources
        ]

        initial_state: CostOptimizationState = {
            "resources": resources,
            "request_id": request_id,
            "timestamp": datetime.utcnow(),
            "analysis_results": None,
            "total_waste_detected": 0.0,
            "recommendations": None,
            "total_potential_savings": 0.0,
            "summary": None,
            "workflow_status": "pending",
            "error_message": None,
        }

        # Run the workflow
        config = RunnableConfig(run_name=f"cost_analysis_{request_id}")
        result = cost_optimization_workflow.invoke(initial_state, config)

        # Convert workflow result to API response
        recommendations = [
            RecommendationResponse(**rec) for rec in result.get("recommendations", [])
        ]

        response = AnalysisResponse(
            request_id=result["request_id"],
            timestamp=result["timestamp"],
            resources_analyzed=len(result["resources"]),
            total_waste_detected=result.get("total_waste_detected", 0.0),
            total_potential_savings=result.get("total_potential_savings", 0.0),
            recommendations=recommendations,
            summary=result.get("summary", "No summary available"),
            workflow_status=result.get("workflow_status", "unknown"),
        )

        logger.info(f"Cost analysis {request_id} completed successfully")
        return response

    except Exception as e:
        logger.error(f"Cost analysis {request_id} failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
