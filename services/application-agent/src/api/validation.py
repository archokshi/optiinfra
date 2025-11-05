"""
Validation API Endpoints

Provides endpoints for validation engine and A/B testing.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, List
from ..models.validation import (
    ValidationRequest,
    ValidationResult,
    ABTestConfig,
    ABTestObservation,
    ABTestResult,
    ValidationHistory
)
from ..validators.ab_tester import ab_tester
from ..validators.approval_engine import approval_engine
from ..core.logger import logger

router = APIRouter(prefix="/validation", tags=["validation"])


@router.post("/create", response_model=ValidationResult, status_code=status.HTTP_201_CREATED)
async def create_validation(request: ValidationRequest) -> ValidationResult:
    """
    Create a validation request.
    
    Args:
        request: Validation request
        
    Returns:
        Validation result
    """
    try:
        logger.info(f"Creating validation: {request.name}")
        
        result = approval_engine.validate_change(request)
        
        return result
        
    except Exception as e:
        logger.error(f"Validation creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation creation failed: {str(e)}"
        )


@router.post("/ab-test", response_model=ABTestConfig, status_code=status.HTTP_201_CREATED)
async def setup_ab_test(
    name: str,
    control_group: str,
    treatment_group: str,
    metric: str = "overall_quality",
    sample_size: int = 100,
    significance_level: float = 0.05
) -> ABTestConfig:
    """
    Setup an A/B test.
    
    Args:
        name: Test name
        control_group: Control group identifier
        treatment_group: Treatment group identifier
        metric: Metric to compare
        sample_size: Target sample size per group
        significance_level: Significance level
        
    Returns:
        A/B test configuration
    """
    try:
        config = ab_tester.setup_test(
            name=name,
            control_group=control_group,
            treatment_group=treatment_group,
            metric=metric,
            sample_size=sample_size,
            significance_level=significance_level
        )
        
        return config
        
    except Exception as e:
        logger.error(f"A/B test setup failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"A/B test setup failed: {str(e)}"
        )


@router.post("/observation", status_code=status.HTTP_201_CREATED)
async def add_observation(observation: ABTestObservation) -> Dict[str, str]:
    """
    Add an observation to an A/B test.
    
    Args:
        observation: Test observation
        
    Returns:
        Success message
    """
    try:
        ab_tester.add_observation(observation)
        
        return {"status": "success", "message": "Observation added"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to add observation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add observation: {str(e)}"
        )


@router.get("/results/{test_id}", response_model=ABTestResult, status_code=status.HTTP_200_OK)
async def get_ab_test_results(test_id: str) -> ABTestResult:
    """
    Get A/B test results.
    
    Args:
        test_id: Test ID
        
    Returns:
        A/B test result
    """
    try:
        result = ab_tester.calculate_significance(test_id)
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get A/B test results: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get A/B test results: {str(e)}"
        )


@router.post("/decide", response_model=ValidationResult, status_code=status.HTTP_200_OK)
async def make_decision(
    name: str,
    model_name: str,
    baseline_quality: float,
    new_quality: float,
    p_value: float = None,
    effect_size: float = None
) -> ValidationResult:
    """
    Make a validation decision.
    
    Args:
        name: Validation name
        model_name: Model name
        baseline_quality: Baseline quality
        new_quality: New quality
        p_value: P-value from test (optional)
        effect_size: Effect size (optional)
        
    Returns:
        Validation result with decision
    """
    try:
        request = ValidationRequest(
            name=name,
            model_name=model_name,
            baseline_quality=baseline_quality,
            new_quality=new_quality
        )
        
        result = approval_engine.validate_change(
            request,
            p_value=p_value,
            effect_size=effect_size
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Decision making failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Decision making failed: {str(e)}"
        )


@router.get("/history", status_code=status.HTTP_200_OK)
async def get_validation_history(limit: int = 100) -> Dict[str, Any]:
    """
    Get validation history.
    
    Args:
        limit: Maximum number of records to return
        
    Returns:
        Validation history
    """
    try:
        history = approval_engine.get_validation_history(limit=limit)
        
        return {
            "total": len(history),
            "history": [
                {
                    "validation_id": h.validation_id,
                    "decision": h.decision,
                    "quality_change": h.quality_change,
                    "confidence": h.confidence,
                    "timestamp": h.timestamp.isoformat()
                }
                for h in history
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get validation history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get validation history: {str(e)}"
        )
