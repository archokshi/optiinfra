"""
Wait helpers for polling asynchronous operations.
"""
import asyncio
from typing import Callable, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class WaitHelper:
    """Helper for waiting on conditions."""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    async def wait_for_recommendation(
        self,
        customer_id: str,
        recommendation_type: str,
        timeout: float = 60.0
    ) -> Optional[dict]:
        """Wait for a specific recommendation to appear."""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            try:
                recommendations = await self.api_client.get_recommendations(customer_id)
                
                for rec in recommendations:
                    if rec.get("type") == recommendation_type and rec.get("status") == "pending":
                        logger.info(f"✅ Found recommendation: {rec.get('id')}")
                        return rec
            except Exception as e:
                logger.debug(f"Error fetching recommendations: {e}")
            
            await asyncio.sleep(2)
        
        logger.warning(f"Recommendation {recommendation_type} not found within {timeout}s")
        return None
    
    async def wait_for_optimization_complete(
        self,
        optimization_id: str,
        timeout: float = 300.0
    ) -> dict:
        """Wait for optimization to complete."""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            try:
                status = await self.api_client.get_optimization_status(optimization_id)
                
                if status.get("status") in ["completed", "failed", "rolled_back"]:
                    logger.info(f"✅ Optimization {optimization_id} finished with status: {status.get('status')}")
                    return status
                
                logger.debug(f"Optimization {optimization_id} status: {status.get('status')}")
            except Exception as e:
                logger.debug(f"Error fetching optimization status: {e}")
            
            await asyncio.sleep(5)
        
        raise TimeoutError(f"Optimization {optimization_id} did not complete in time")
    
    async def wait_for_metric_change(
        self,
        customer_id: str,
        metric_type: str,
        condition: Callable[[Any], bool],
        timeout: float = 60.0
    ) -> bool:
        """Wait for a metric to meet a condition."""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            try:
                metrics = await self.api_client.get_customer_metrics(
                    customer_id,
                    metric_type,
                    start_time=datetime.now() - timedelta(minutes=5)
                )
                
                if metrics and condition(metrics[-1].get("value")):
                    logger.info(f"✅ Metric {metric_type} met condition")
                    return True
            except Exception as e:
                logger.debug(f"Error fetching metrics: {e}")
            
            await asyncio.sleep(5)
        
        logger.warning(f"Metric {metric_type} did not meet condition within {timeout}s")
        return False
    
    async def wait_for_condition(
        self,
        condition: Callable[[], bool],
        timeout: float = 60.0,
        poll_interval: float = 2.0
    ) -> bool:
        """Generic wait for condition."""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            try:
                if await condition() if asyncio.iscoroutinefunction(condition) else condition():
                    return True
            except Exception as e:
                logger.debug(f"Condition check failed: {e}")
            
            await asyncio.sleep(poll_interval)
        
        return False
