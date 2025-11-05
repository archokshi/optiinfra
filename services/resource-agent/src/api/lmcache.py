"""
LMCache API

Endpoints for LMCache management and monitoring.
"""

from fastapi import APIRouter, HTTPException, status

from src.models.lmcache_metrics import (
    LMCacheStatus,
    CacheConfig,
    CacheOptimizationResult
)
from src.lmcache.client import LMCacheClient
from src.config import settings

router = APIRouter(prefix="/lmcache", tags=["lmcache"])

# Global LMCache client instance
lmcache_client = LMCacheClient()


@router.get(
    "/status",
    response_model=LMCacheStatus,
    status_code=status.HTTP_200_OK,
    summary="Get LMCache status"
)
async def get_lmcache_status() -> LMCacheStatus:
    """
    Get current LMCache status including metrics and configuration.
    
    Returns:
        LMCacheStatus: Complete cache status
    """
    try:
        return lmcache_client.get_status(instance_id=settings.agent_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache status: {str(e)}"
        )


@router.get(
    "/config",
    response_model=CacheConfig,
    status_code=status.HTTP_200_OK,
    summary="Get cache configuration"
)
async def get_cache_config() -> CacheConfig:
    """
    Get current cache configuration.
    
    Returns:
        CacheConfig: Current configuration
    """
    return lmcache_client.get_config()


@router.post(
    "/config",
    response_model=CacheConfig,
    status_code=status.HTTP_200_OK,
    summary="Update cache configuration"
)
async def update_cache_config(config: CacheConfig) -> CacheConfig:
    """
    Update cache configuration.
    
    Args:
        config: New configuration
        
    Returns:
        CacheConfig: Updated configuration
    """
    success = lmcache_client.update_config(config)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update cache configuration"
        )
    
    return lmcache_client.get_config()


@router.post(
    "/optimize",
    response_model=CacheOptimizationResult,
    status_code=status.HTTP_200_OK,
    summary="Optimize cache"
)
async def optimize_cache() -> CacheOptimizationResult:
    """
    Trigger cache optimization (eviction, compaction, etc.).
    
    Returns:
        CacheOptimizationResult: Optimization result
    """
    result = lmcache_client.optimize()
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.message
        )
    
    return result


@router.delete(
    "/clear",
    status_code=status.HTTP_200_OK,
    summary="Clear cache"
)
async def clear_cache() -> dict:
    """
    Clear all cache entries.
    
    Returns:
        dict: Success message
    """
    success = lmcache_client.clear_cache()
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        )
    
    return {"message": "Cache cleared successfully"}
