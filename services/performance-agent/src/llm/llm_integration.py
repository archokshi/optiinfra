"""LLM integration layer for Performance Agent."""

import logging
import hashlib
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from src.llm.llm_client import LLMClient
from src.llm.insight_generator import InsightGenerator

logger = logging.getLogger(__name__)


class LLMIntegrationLayer:
    """Main LLM integration layer with caching and orchestration."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-oss-20b",
        enable_cache: bool = True,
        cache_ttl: int = 3600
    ):
        """Initialize LLM integration layer."""
        self.llm_client = LLMClient(api_key=api_key, model=model)
        self.insight_generator = InsightGenerator(self.llm_client)
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info("LLM integration layer initialized")
    
    async def enhance_analysis_report(
        self,
        instance_id: str,
        instance_type: str,
        metrics: Dict[str, Any],
        bottlenecks: List[Dict[str, Any]],
        optimizations: List[Dict[str, Any]],
        enable_llm: bool = True
    ) -> Dict[str, Any]:
        """Enhance analysis report with LLM insights."""
        if not enable_llm:
            logger.info("LLM enhancement disabled")
            return {
                "instance_id": instance_id,
                "metrics": metrics,
                "bottlenecks": bottlenecks,
                "optimizations": optimizations,
                "llm_enhanced": False
            }
        
        try:
            # Check cache
            cache_key = self._generate_cache_key(instance_id, metrics, bottlenecks)
            cached = self._get_from_cache(cache_key)
            if cached:
                logger.info(f"Cache hit for {instance_id}")
                return cached
            
            # Generate insights
            logger.info(f"Generating LLM insights for {instance_id}")
            
            insights = await self.insight_generator.generate_performance_insights(
                instance_id=instance_id,
                instance_type=instance_type,
                metrics=metrics,
                bottlenecks=bottlenecks
            )
            
            # Explain each bottleneck
            explained_bottlenecks = []
            for bottleneck in bottlenecks:
                explanation = await self.insight_generator.explain_bottleneck(bottleneck)
                explained_bottleneck = bottleneck.copy()
                explained_bottleneck["business_explanation"] = explanation
                explained_bottlenecks.append(explained_bottleneck)
            
            # Enhance optimizations
            enhanced_optimizations = []
            for optimization in optimizations:
                enhanced = await self.insight_generator.enhance_optimization(
                    optimization,
                    current_config={}
                )
                enhanced_optimizations.append(enhanced)
            
            # Generate executive summary
            executive_summary = await self.insight_generator.generate_executive_summary(
                instance_id=instance_id,
                instance_type=instance_type,
                metrics=metrics,
                bottlenecks=bottlenecks,
                optimizations=optimizations
            )
            
            # Build enhanced report
            enhanced_report = {
                "instance_id": instance_id,
                "instance_type": instance_type,
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": metrics,
                "bottlenecks": explained_bottlenecks,
                "optimizations": enhanced_optimizations,
                "llm_insights": {
                    "performance_insights": insights,
                    "executive_summary": executive_summary
                },
                "llm_enhanced": True,
                "cache_hit": False
            }
            
            # Cache result
            self._add_to_cache(cache_key, enhanced_report)
            
            logger.info(f"Successfully enhanced report for {instance_id}")
            return enhanced_report
            
        except Exception as e:
            logger.error(f"LLM enhancement failed: {e}")
            # Graceful degradation
            return {
                "instance_id": instance_id,
                "metrics": metrics,
                "bottlenecks": bottlenecks,
                "optimizations": optimizations,
                "llm_enhanced": False,
                "error": str(e)
            }
    
    def _generate_cache_key(
        self,
        instance_id: str,
        metrics: Dict[str, Any],
        bottlenecks: List[Dict[str, Any]]
    ) -> str:
        """Generate cache key from inputs."""
        data = {
            "instance_id": instance_id,
            "metrics": metrics,
            "bottlenecks": [b.get("type") for b in bottlenecks]
        }
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get from cache if not expired."""
        if not self.enable_cache:
            return None
        
        if key in self._cache:
            entry = self._cache[key]
            if datetime.utcnow() < entry["expires_at"]:
                entry["data"]["cache_hit"] = True
                return entry["data"]
            else:
                del self._cache[key]
        
        return None
    
    def _add_to_cache(self, key: str, data: Dict[str, Any]) -> None:
        """Add to cache with TTL."""
        if not self.enable_cache:
            return
        
        self._cache[key] = {
            "data": data,
            "expires_at": datetime.utcnow() + timedelta(seconds=self.cache_ttl)
        }
