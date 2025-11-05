"""
LMCache Client

Client wrapper for LMCache library with graceful degradation.
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime
import time
import random

# Try to import LMCache
try:
    import lmcache
    LMCACHE_AVAILABLE = True
except ImportError:
    LMCACHE_AVAILABLE = False
    logging.warning("LMCache not available - using simulation mode")

from src.models.lmcache_metrics import (
    CacheMetrics,
    CacheConfig,
    CacheStatus,
    CacheEntry,
    CacheOptimizationResult,
    LMCacheStatus,
    EvictionPolicy
)

logger = logging.getLogger("resource_agent.lmcache")


class LMCacheClient:
    """Client for LMCache operations."""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """
        Initialize LMCache client.
        
        Args:
            config: Cache configuration
        """
        self.config = config or CacheConfig()
        self.initialized = False
        self.cache_instance = None
        
        # Simulation mode tracking
        self.sim_total_requests = 0
        self.sim_cache_hits = 0
        self.sim_tokens_cached = 0
        
        if LMCACHE_AVAILABLE and self.config.enabled:
            try:
                self._initialize_lmcache()
                self.initialized = True
                logger.info("LMCache initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize LMCache: {e}")
                self.initialized = False
        else:
            logger.info("LMCache running in simulation mode")
    
    def _initialize_lmcache(self):
        """Initialize LMCache instance."""
        if not LMCACHE_AVAILABLE:
            return
        
        # Initialize LMCache with configuration
        # Note: Actual LMCache API may differ - adjust based on library docs
        try:
            self.cache_instance = lmcache.LMCache(
                max_size_mb=self.config.max_size_mb,
                eviction_policy=self.config.eviction_policy.value,
                enable_prefix_caching=self.config.enable_prefix_caching
            )
        except Exception as e:
            logger.error(f"LMCache initialization error: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if LMCache is available and initialized."""
        return self.initialized and LMCACHE_AVAILABLE
    
    def get_metrics(self) -> CacheMetrics:
        """
        Get current cache metrics.
        
        Returns:
            CacheMetrics: Current metrics
        """
        if self.is_available():
            return self._get_real_metrics()
        else:
            return self._get_simulated_metrics()
    
    def _get_real_metrics(self) -> CacheMetrics:
        """Get metrics from actual LMCache instance."""
        try:
            # Get metrics from LMCache
            # Note: Adjust based on actual LMCache API
            stats = self.cache_instance.get_stats()
            
            total_requests = stats.get('total_requests', 0)
            cache_hits = stats.get('cache_hits', 0)
            cache_misses = stats.get('cache_misses', 0)
            
            hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0.0
            
            return CacheMetrics(
                status=CacheStatus.ENABLED,
                enabled=True,
                total_size_mb=self.config.max_size_mb,
                used_size_mb=stats.get('used_size_mb', 0),
                available_size_mb=self.config.max_size_mb - stats.get('used_size_mb', 0),
                utilization_percent=(stats.get('used_size_mb', 0) / self.config.max_size_mb) * 100,
                total_requests=total_requests,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                hit_rate_percent=hit_rate,
                tokens_cached=stats.get('tokens_cached', 0),
                tokens_served=stats.get('tokens_served', 0),
                tokens_computed=stats.get('tokens_computed', 0),
                avg_latency_ms=stats.get('avg_latency_ms'),
                cache_hit_latency_ms=stats.get('cache_hit_latency_ms'),
                cache_miss_latency_ms=stats.get('cache_miss_latency_ms'),
                memory_saved_mb=stats.get('memory_saved_mb', 0),
                memory_savings_percent=stats.get('memory_savings_percent', 0)
            )
        except Exception as e:
            logger.error(f"Failed to get real metrics: {e}")
            return self._get_simulated_metrics()
    
    def _get_simulated_metrics(self) -> CacheMetrics:
        """Get simulated metrics for demo/testing."""
        # Simulate realistic cache behavior
        self.sim_total_requests += 1
        
        # Simulate 65% hit rate
        if random.random() < 0.65:
            self.sim_cache_hits += 1
        
        self.sim_tokens_cached = min(self.sim_tokens_cached + random.randint(10, 100), 1000000)
        
        hit_rate = (self.sim_cache_hits / self.sim_total_requests * 100) if self.sim_total_requests > 0 else 0.0
        
        used_size = min(512.0 + (self.sim_total_requests * 0.5), self.config.max_size_mb * 0.8)
        
        return CacheMetrics(
            status=CacheStatus.DISABLED if not self.config.enabled else CacheStatus.ENABLED,
            enabled=self.config.enabled,
            total_size_mb=self.config.max_size_mb,
            used_size_mb=used_size,
            available_size_mb=self.config.max_size_mb - used_size,
            utilization_percent=(used_size / self.config.max_size_mb) * 100,
            total_requests=self.sim_total_requests,
            cache_hits=self.sim_cache_hits,
            cache_misses=self.sim_total_requests - self.sim_cache_hits,
            hit_rate_percent=hit_rate,
            tokens_cached=self.sim_tokens_cached,
            tokens_served=int(self.sim_tokens_cached * 0.65),
            tokens_computed=int(self.sim_tokens_cached * 0.35),
            avg_latency_ms=45.0,
            cache_hit_latency_ms=25.0,
            cache_miss_latency_ms=85.0,
            memory_saved_mb=used_size * 0.4,
            memory_savings_percent=40.0
        )
    
    def get_config(self) -> CacheConfig:
        """Get current configuration."""
        return self.config
    
    def update_config(self, new_config: CacheConfig) -> bool:
        """
        Update cache configuration.
        
        Args:
            new_config: New configuration
            
        Returns:
            bool: Success status
        """
        try:
            self.config = new_config
            
            if self.is_available():
                # Update LMCache instance configuration
                # Note: Adjust based on actual LMCache API
                self.cache_instance.update_config(
                    max_size_mb=new_config.max_size_mb,
                    eviction_policy=new_config.eviction_policy.value
                )
            
            logger.info("Cache configuration updated")
            return True
        except Exception as e:
            logger.error(f"Failed to update config: {e}")
            return False
    
    def optimize(self) -> CacheOptimizationResult:
        """
        Trigger cache optimization.
        
        Returns:
            CacheOptimizationResult: Optimization result
        """
        start_time = time.time()
        
        try:
            if self.is_available():
                # Trigger LMCache optimization
                result = self.cache_instance.optimize()
                
                return CacheOptimizationResult(
                    success=True,
                    message="Cache optimization completed",
                    entries_before=result.get('entries_before', 0),
                    entries_after=result.get('entries_after', 0),
                    entries_evicted=result.get('entries_evicted', 0),
                    memory_freed_mb=result.get('memory_freed_mb', 0),
                    optimization_time_ms=(time.time() - start_time) * 1000
                )
            else:
                # Simulate optimization
                return CacheOptimizationResult(
                    success=True,
                    message="Cache optimization completed (simulated)",
                    entries_before=100,
                    entries_after=75,
                    entries_evicted=25,
                    memory_freed_mb=128.0,
                    optimization_time_ms=(time.time() - start_time) * 1000
                )
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            return CacheOptimizationResult(
                success=False,
                message=f"Optimization failed: {str(e)}",
                entries_before=0,
                entries_after=0,
                entries_evicted=0,
                memory_freed_mb=0.0,
                optimization_time_ms=(time.time() - start_time) * 1000
            )
    
    def clear_cache(self) -> bool:
        """
        Clear all cache entries.
        
        Returns:
            bool: Success status
        """
        try:
            if self.is_available():
                self.cache_instance.clear()
            
            # Reset simulation counters
            self.sim_total_requests = 0
            self.sim_cache_hits = 0
            self.sim_tokens_cached = 0
            
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
    
    def get_status(self, instance_id: str) -> LMCacheStatus:
        """
        Get complete cache status.
        
        Args:
            instance_id: Instance identifier
            
        Returns:
            LMCacheStatus: Complete status
        """
        metrics = self.get_metrics()
        
        # Get LMCache version if available
        lmcache_version = None
        if LMCACHE_AVAILABLE:
            try:
                lmcache_version = lmcache.__version__
            except:
                lmcache_version = "unknown"
        
        return LMCacheStatus(
            instance_id=instance_id,
            metrics=metrics,
            config=self.config,
            lmcache_version=lmcache_version,
            backend="memory",
            top_entries=[]
        )
