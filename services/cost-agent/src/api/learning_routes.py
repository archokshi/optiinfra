"""
Learning Loop API Routes.

FastAPI endpoints for learning and continuous improvement.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from src.learning.learning_loop import LearningLoop
from src.models.learning_loop import OutcomeData

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/learning", tags=["learning"])

# Initialize learning loop
learning_loop = LearningLoop()


@router.post("/track-outcome")
async def track_outcome(outcome_data: OutcomeData):
    """
    Track an execution outcome.
    
    Args:
        outcome_data: Outcome data to track
    
    Returns:
        Processing result
    """
    try:
        logger.info(f"Tracking outcome for execution {outcome_data.execution_id}")
        
        result = await learning_loop.process_execution_outcome(
            execution_id=outcome_data.execution_id,
            recommendation_id=outcome_data.recommendation_id,
            outcome_data=outcome_data.dict()
        )
        
        return result.dict()
        
    except Exception as e:
        logger.error(f"Error tracking outcome: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_learning_metrics():
    """
    Get overall learning metrics.
    
    Returns:
        Learning metrics
    """
    try:
        metrics = await learning_loop.get_learning_metrics()
        return metrics.dict()
        
    except Exception as e:
        logger.error(f"Error getting learning metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights")
async def get_learning_insights(
    lookback_days: int = Query(30, ge=1, le=365, description="Days to look back"),
    limit: int = Query(10, ge=1, le=100, description="Max insights to return")
):
    """
    Get learning insights.
    
    Args:
        lookback_days: Number of days to analyze
        limit: Maximum number of insights
    
    Returns:
        List of learning insights
    """
    try:
        insights = await learning_loop.feedback_analyzer.generate_learning_insights(
            lookback_days=lookback_days
        )
        
        # Limit results
        insights = insights[:limit]
        
        return {
            "total": len(insights),
            "insights": [i.dict() for i in insights]
        }
        
    except Exception as e:
        logger.error(f"Error getting insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar-cases/{recommendation_id}")
async def find_similar_cases(
    recommendation_id: str,
    limit: int = Query(10, ge=1, le=50, description="Max similar cases")
):
    """
    Find similar historical cases.
    
    Args:
        recommendation_id: Recommendation ID to find similar cases for
        limit: Maximum number of similar cases
    
    Returns:
        List of similar cases
    """
    try:
        # Get recommendation (would query from recommendation engine)
        # For now, use mock data
        recommendation = {
            "recommendation_id": recommendation_id,
            "recommendation_type": "terminate",
            "resource_type": "ec2",
            "region": "us-east-1",
            "monthly_savings": 50.0
        }
        
        similar_cases = await learning_loop.knowledge_store.find_similar_cases(
            recommendation=recommendation,
            limit=limit
        )
        
        return {
            "recommendation_id": recommendation_id,
            "total": len(similar_cases),
            "similar_cases": [c.dict() for c in similar_cases]
        }
        
    except Exception as e:
        logger.error(f"Error finding similar cases: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-cycle")
async def run_learning_cycle(force: bool = Query(False, description="Force run cycle")):
    """
    Run a learning cycle.
    
    Args:
        force: Force run even if recently run
    
    Returns:
        Learning cycle result
    """
    try:
        logger.info("Running learning cycle")
        
        result = await learning_loop.run_learning_cycle(force=force)
        
        return result.dict()
        
    except Exception as e:
        logger.error(f"Error running learning cycle: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accuracy/{recommendation_type}")
async def get_accuracy_metrics(recommendation_type: str):
    """
    Get accuracy metrics for a recommendation type.
    
    Args:
        recommendation_type: Type of recommendation
    
    Returns:
        Accuracy metrics
    """
    try:
        metrics = await learning_loop.feedback_analyzer.calculate_accuracy_metrics(
            recommendation_type=recommendation_type
        )
        
        return metrics.dict()
        
    except Exception as e:
        logger.error(f"Error getting accuracy metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/success-patterns/{recommendation_type}")
async def get_success_patterns(
    recommendation_type: str,
    lookback_days: int = Query(90, ge=1, le=365, description="Days to analyze")
):
    """
    Get success patterns for a recommendation type.
    
    Args:
        recommendation_type: Type of recommendation
        lookback_days: Number of days to analyze
    
    Returns:
        Success patterns
    """
    try:
        patterns = await learning_loop.feedback_analyzer.analyze_success_patterns(
            recommendation_type=recommendation_type,
            lookback_days=lookback_days
        )
        
        return patterns.dict()
        
    except Exception as e:
        logger.error(f"Error getting success patterns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/failure-patterns/{recommendation_type}")
async def get_failure_patterns(
    recommendation_type: str,
    lookback_days: int = Query(90, ge=1, le=365, description="Days to analyze")
):
    """
    Get failure patterns for a recommendation type.
    
    Args:
        recommendation_type: Type of recommendation
        lookback_days: Number of days to analyze
    
    Returns:
        Failure patterns
    """
    try:
        patterns = await learning_loop.feedback_analyzer.analyze_failure_patterns(
            recommendation_type=recommendation_type,
            lookback_days=lookback_days
        )
        
        return patterns.dict()
        
    except Exception as e:
        logger.error(f"Error getting failure patterns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/improvement-opportunities")
async def get_improvement_opportunities():
    """
    Get improvement opportunities.
    
    Returns:
        List of improvement opportunities
    """
    try:
        opportunities = await learning_loop.feedback_analyzer.identify_improvement_opportunities()
        
        return {
            "total": len(opportunities),
            "opportunities": [o.dict() for o in opportunities]
        }
        
    except Exception as e:
        logger.error(f"Error getting improvement opportunities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scoring-weights")
async def get_scoring_weights():
    """
    Get current scoring weights.
    
    Returns:
        Current scoring weights
    """
    try:
        weights = await learning_loop.improvement_engine.get_current_scoring_weights()
        return weights.dict()
        
    except Exception as e:
        logger.error(f"Error getting scoring weights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prediction-model/{recommendation_type}")
async def get_prediction_model(recommendation_type: str):
    """
    Get prediction model for a recommendation type.
    
    Args:
        recommendation_type: Type of recommendation
    
    Returns:
        Prediction model or 404
    """
    try:
        model = await learning_loop.improvement_engine.get_prediction_model(recommendation_type)
        
        if model is None:
            raise HTTPException(status_code=404, detail=f"No prediction model for {recommendation_type}")
        
        return model.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prediction model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-model/{recommendation_type}")
async def get_risk_model(recommendation_type: str):
    """
    Get risk model for a recommendation type.
    
    Args:
        recommendation_type: Type of recommendation
    
    Returns:
        Risk model or 404
    """
    try:
        model = await learning_loop.improvement_engine.get_risk_model(recommendation_type)
        
        if model is None:
            raise HTTPException(status_code=404, detail=f"No risk model for {recommendation_type}")
        
        return model.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting risk model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
