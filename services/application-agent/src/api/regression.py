"""
Regression Detection API Endpoints

Provides endpoints for baseline tracking and regression detection.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, List, Optional
from ..models.baseline import (
    Baseline,
    BaselineConfig,
    RegressionResult,
    RegressionDetectionRequest,
    RegressionAlert,
    AlertLevel,
    BaselineStatus
)
from ..analyzers.regression_detector import regression_detector
from ..storage.baseline_storage import baseline_storage
from ..core.logger import logger

router = APIRouter(prefix="/regression", tags=["regression"])


@router.post("/baseline", response_model=Baseline, status_code=status.HTTP_201_CREATED)
async def establish_baseline(config: BaselineConfig) -> Baseline:
    """
    Establish a new quality baseline.
    
    Args:
        config: Baseline configuration
        
    Returns:
        Created baseline
    """
    try:
        logger.info(f"Establishing baseline for {config.model_name}")
        
        baseline = regression_detector.establish_baseline(config)
        
        return baseline
        
    except ValueError as e:
        logger.error(f"Failed to establish baseline: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Baseline establishment failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Baseline establishment failed: {str(e)}"
        )


@router.post("/detect", response_model=RegressionResult, status_code=status.HTTP_200_OK)
async def detect_regression(request: RegressionDetectionRequest) -> RegressionResult:
    """
    Detect quality regression.
    
    Args:
        request: Regression detection request
        
    Returns:
        Regression detection result
    """
    try:
        logger.info(f"Detecting regression for {request.model_name}")
        
        result = regression_detector.detect_regression(request)
        
        return result
        
    except ValueError as e:
        logger.error(f"Regression detection failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Regression detection failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Regression detection failed: {str(e)}"
        )


@router.get("/baselines", status_code=status.HTTP_200_OK)
async def list_baselines(
    model_name: Optional[str] = None,
    status_filter: Optional[BaselineStatus] = None
) -> Dict[str, Any]:
    """
    List all baselines.
    
    Args:
        model_name: Filter by model name
        status_filter: Filter by status
        
    Returns:
        List of baselines
    """
    try:
        baselines = baseline_storage.list_all(
            model_name=model_name,
            status=status_filter
        )
        
        return {
            "total": len(baselines),
            "baselines": [
                {
                    "baseline_id": b.baseline_id,
                    "model_name": b.model_name,
                    "config_hash": b.config_hash,
                    "average_quality": b.metrics.average_quality,
                    "sample_size": b.sample_size,
                    "created_at": b.created_at.isoformat(),
                    "status": b.status
                }
                for b in baselines
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to list baselines: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list baselines: {str(e)}"
        )


@router.get("/baselines/{baseline_id}", response_model=Baseline, status_code=status.HTTP_200_OK)
async def get_baseline(baseline_id: str) -> Baseline:
    """
    Get baseline by ID.
    
    Args:
        baseline_id: Baseline ID
        
    Returns:
        Baseline
    """
    baseline = baseline_storage.get(baseline_id)
    
    if not baseline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Baseline {baseline_id} not found"
        )
    
    return baseline


@router.get("/alerts", status_code=status.HTTP_200_OK)
async def get_alerts(
    limit: int = 100,
    level: Optional[AlertLevel] = None
) -> Dict[str, Any]:
    """
    Get regression alerts.
    
    Args:
        limit: Maximum number of alerts to return
        level: Filter by alert level
        
    Returns:
        List of alerts
    """
    try:
        alerts = regression_detector.get_alerts(limit=limit, level=level)
        
        return {
            "total": len(alerts),
            "alerts": [
                {
                    "alert_id": a.alert_id,
                    "level": a.level,
                    "message": a.message,
                    "severity": a.severity,
                    "quality_drop": a.quality_drop,
                    "baseline_quality": a.baseline_quality,
                    "current_quality": a.current_quality,
                    "timestamp": a.timestamp.isoformat()
                }
                for a in alerts
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alerts: {str(e)}"
        )


@router.get("/history", status_code=status.HTTP_200_OK)
async def get_regression_history(
    model_name: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get regression detection history.
    
    Args:
        model_name: Filter by model name
        limit: Maximum number of records to return
        
    Returns:
        Regression history
    """
    try:
        # Get alerts (which represent regression history)
        alerts = regression_detector.get_alerts(limit=limit)
        
        # Filter by model if specified
        if model_name:
            # Note: We'd need to store model_name in alerts for this to work properly
            # For now, return all alerts
            pass
        
        return {
            "total": len(alerts),
            "history": [
                {
                    "alert_id": a.alert_id,
                    "severity": a.severity,
                    "quality_drop": a.quality_drop,
                    "timestamp": a.timestamp.isoformat()
                }
                for a in alerts
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get regression history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get regression history: {str(e)}"
        )
