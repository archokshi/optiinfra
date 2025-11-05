"""
Configuration API Endpoints

Provides endpoints for configuration monitoring and optimization.
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from ..models.configuration import (
    ConfigurationSnapshot,
    ConfigurationChange,
    ParameterImpact,
    ConfigurationRecommendation,
    OptimizationRequest,
    OptimizationResult
)
from ..trackers.config_tracker import config_tracker
from ..analyzers.config_analyzer import config_analyzer
from ..optimizers.config_optimizer import config_optimizer
from ..core.logger import logger

router = APIRouter(prefix="/config", tags=["configuration"])


@router.get("/current", response_model=ConfigurationSnapshot, status_code=status.HTTP_200_OK)
async def get_current_configuration() -> ConfigurationSnapshot:
    """
    Get current configuration.
    
    Returns:
        Current configuration snapshot
    """
    try:
        logger.info("Getting current configuration")
        config = config_tracker.get_current_config()
        return config
        
    except Exception as e:
        logger.error(f"Failed to get current configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}"
        )


@router.get("/history", response_model=List[ConfigurationSnapshot], status_code=status.HTTP_200_OK)
async def get_configuration_history(
    limit: int = Query(default=10, ge=1, le=100)
) -> List[ConfigurationSnapshot]:
    """
    Get configuration history.
    
    Args:
        limit: Maximum number of snapshots to return
        
    Returns:
        List of configuration snapshots
    """
    try:
        logger.info(f"Getting configuration history (limit={limit})")
        history = config_tracker.get_config_history(limit=limit)
        return history
        
    except Exception as e:
        logger.error(f"Failed to get configuration history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get history: {str(e)}"
        )


@router.post("/analyze", response_model=ParameterImpact, status_code=status.HTTP_200_OK)
async def analyze_parameter(
    parameter: str,
    samples: int = Query(default=100, ge=10, le=1000)
) -> ParameterImpact:
    """
    Analyze parameter impact on metrics.
    
    Args:
        parameter: Parameter to analyze
        samples: Number of samples to analyze
        
    Returns:
        Parameter impact analysis
    """
    try:
        logger.info(f"Analyzing parameter: {parameter}")
        impact = config_analyzer.analyze_parameter_impact(parameter, samples)
        return impact
        
    except Exception as e:
        logger.error(f"Failed to analyze parameter: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/recommendations", response_model=List[ConfigurationRecommendation], status_code=status.HTTP_200_OK)
async def get_recommendations(
    strategy: str = Query(default="balanced")
) -> List[ConfigurationRecommendation]:
    """
    Get optimization recommendations.
    
    Args:
        strategy: Optimization strategy
        
    Returns:
        List of recommendations
    """
    try:
        logger.info(f"Getting recommendations (strategy={strategy})")
        current_config = config_tracker.get_current_config()
        recommendations = config_analyzer.generate_recommendations(current_config, strategy)
        return recommendations
        
    except Exception as e:
        logger.error(f"Failed to get recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )


@router.post("/optimize", response_model=OptimizationResult, status_code=status.HTTP_200_OK)
async def optimize_configuration(
    request: OptimizationRequest
) -> OptimizationResult:
    """
    Optimize configuration.
    
    Args:
        request: Optimization request
        
    Returns:
        Optimization result
    """
    try:
        logger.info(f"Optimizing configuration with strategy: {request.strategy}")
        current_config = config_tracker.get_current_config()
        result = config_optimizer.optimize(current_config, request)
        return result
        
    except Exception as e:
        logger.error(f"Failed to optimize configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization failed: {str(e)}"
        )
