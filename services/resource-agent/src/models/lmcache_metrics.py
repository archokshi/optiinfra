"""
LMCache Metrics Models

Pydantic models for LMCache metrics and configuration.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum


class CacheStatus(str, Enum):
    """Cache status."""
    
    ENABLED = "enabled"
    DISABLED = "disabled"
    INITIALIZING = "initializing"
    ERROR = "error"


class EvictionPolicy(str, Enum):
    """Cache eviction policies."""
    
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out
    RANDOM = "random"


class CacheMetrics(BaseModel):
    """LMCache metrics."""
    
    # Cache status
    status: CacheStatus = Field(..., description="Cache status")
    enabled: bool = Field(..., description="Whether cache is enabled")
    
    # Size metrics
    total_size_mb: float = Field(..., ge=0, description="Total cache size (MB)")
    used_size_mb: float = Field(..., ge=0, description="Used cache size (MB)")
    available_size_mb: float = Field(..., ge=0, description="Available cache size (MB)")
    utilization_percent: float = Field(..., ge=0, le=100, description="Cache utilization %")
    
    # Hit/Miss metrics
    total_requests: int = Field(default=0, ge=0, description="Total cache requests")
    cache_hits: int = Field(default=0, ge=0, description="Cache hits")
    cache_misses: int = Field(default=0, ge=0, description="Cache misses")
    hit_rate_percent: float = Field(default=0.0, ge=0, le=100, description="Cache hit rate %")
    
    # Token metrics
    tokens_cached: int = Field(default=0, ge=0, description="Total tokens in cache")
    tokens_served: int = Field(default=0, ge=0, description="Tokens served from cache")
    tokens_computed: int = Field(default=0, ge=0, description="Tokens computed (not cached)")
    
    # Performance metrics
    avg_latency_ms: Optional[float] = Field(None, description="Average latency (ms)")
    cache_hit_latency_ms: Optional[float] = Field(None, description="Latency for cache hits (ms)")
    cache_miss_latency_ms: Optional[float] = Field(None, description="Latency for cache misses (ms)")
    
    # Memory savings
    memory_saved_mb: float = Field(default=0.0, ge=0, description="Memory saved by caching (MB)")
    memory_savings_percent: float = Field(default=0.0, ge=0, le=100, description="Memory savings %")


class CacheConfig(BaseModel):
    """LMCache configuration."""
    
    enabled: bool = Field(default=True, description="Enable/disable cache")
    max_size_mb: float = Field(default=1024.0, ge=0, description="Maximum cache size (MB)")
    eviction_policy: EvictionPolicy = Field(default=EvictionPolicy.LRU, description="Eviction policy")
    
    # Prefix caching
    enable_prefix_caching: bool = Field(default=True, description="Enable prefix caching")
    min_prefix_length: int = Field(default=10, ge=1, description="Minimum prefix length to cache")
    
    # Performance tuning
    cache_warmup: bool = Field(default=False, description="Enable cache warmup")
    auto_eviction: bool = Field(default=True, description="Enable automatic eviction")
    
    # Multi-tenant
    enable_sharing: bool = Field(default=True, description="Enable cache sharing across requests")
    max_concurrent_users: int = Field(default=100, ge=1, description="Max concurrent users")


class CacheEntry(BaseModel):
    """Individual cache entry information."""
    
    entry_id: str = Field(..., description="Cache entry ID")
    prefix_hash: str = Field(..., description="Hash of cached prefix")
    token_count: int = Field(..., ge=0, description="Number of tokens cached")
    size_mb: float = Field(..., ge=0, description="Entry size (MB)")
    hit_count: int = Field(default=0, ge=0, description="Number of hits")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)


class CacheOptimizationResult(BaseModel):
    """Result of cache optimization operation."""
    
    success: bool = Field(..., description="Whether optimization succeeded")
    message: str = Field(..., description="Result message")
    
    # Before/after metrics
    entries_before: int = Field(..., description="Cache entries before optimization")
    entries_after: int = Field(..., description="Cache entries after optimization")
    entries_evicted: int = Field(..., description="Entries evicted")
    
    memory_freed_mb: float = Field(..., ge=0, description="Memory freed (MB)")
    optimization_time_ms: float = Field(..., ge=0, description="Optimization time (ms)")


class LMCacheStatus(BaseModel):
    """Complete LMCache status."""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    instance_id: str = Field(..., description="Instance identifier")
    
    # Metrics and config
    metrics: CacheMetrics = Field(..., description="Cache metrics")
    config: CacheConfig = Field(..., description="Cache configuration")
    
    # Additional info
    lmcache_version: Optional[str] = Field(None, description="LMCache library version")
    backend: str = Field(default="memory", description="Cache backend (memory, redis, etc.)")
    
    # Top cache entries
    top_entries: List[CacheEntry] = Field(default_factory=list, description="Top cache entries by hits")
