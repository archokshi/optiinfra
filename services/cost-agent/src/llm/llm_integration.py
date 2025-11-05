"""
LLM Integration Layer for Cost Agent.

Main orchestration layer that coordinates LLM operations,
caching, and integration with the Analysis Engine.
"""

import logging
import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime

from src.llm.llm_client import LLMClient, LLMClientFactory
from src.llm.insight_generator import (
    generate_insights,
    enhance_recommendations,
    generate_executive_summary,
    handle_query
)
from src.config import get_settings

logger = logging.getLogger(__name__)


class LLMIntegrationLayer:
    """
    Main LLM integration layer for Cost Agent.
    
    Orchestrates all LLM operations with caching and error handling.
    """
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        enable_caching: bool = True
    ):
        """
        Initialize LLM integration layer.
        
        Args:
            llm_client: LLM client instance (creates default if None)
            enable_caching: Enable response caching
        """
        self.settings = get_settings()
        self.llm_client = llm_client or LLMClientFactory.get_client()
        self.enable_caching = enable_caching
        self._cache: Dict[str, Any] = {}
        
        logger.info("LLM integration layer initialized")
    
    async def enhance_report(
        self,
        technical_report: Dict[str, Any],
        enable_llm: bool = True
    ) -> Dict[str, Any]:
        """
        Enhance technical report with LLM insights.
        
        Args:
            technical_report: Technical analysis report
            enable_llm: Enable LLM enhancement (feature flag)
        
        Returns:
            Enhanced report with LLM insights
        """
        # Check feature flag
        if not enable_llm or not self.settings.llm_enabled:
            logger.info("LLM enhancement disabled")
            return technical_report
        
        logger.info("Enhancing report with LLM insights")
        
        try:
            # Check cache
            cache_key = self._generate_cache_key(technical_report)
            if self.enable_caching and cache_key in self._cache:
                logger.info("Cache hit for LLM enhancement")
                return self._cache[cache_key]
            
            # Generate insights
            insights = await self._generate_insights_with_fallback(
                technical_report
            )
            
            # Enhance recommendations
            enhanced_recs = await self._enhance_recommendations_with_fallback(
                technical_report.get("recommendations", [])
            )
            
            # Generate executive summary
            summary = await self._generate_summary_with_fallback(
                technical_report,
                insights
            )
            
            # Build enhanced report
            enhanced_report = {
                **technical_report,
                "llm_insights": insights,
                "enhanced_recommendations": enhanced_recs,
                "executive_summary": summary,
                "llm_metadata": {
                    "model": self.llm_client.model,
                    "generated_at": datetime.utcnow().isoformat(),
                    "cache_hit": False
                }
            }
            
            # Cache result
            if self.enable_caching:
                self._cache[cache_key] = enhanced_report
            
            logger.info("Report enhanced successfully")
            return enhanced_report
            
        except Exception as e:
            logger.error(f"Failed to enhance report: {e}")
            # Graceful degradation - return technical report
            return {
                **technical_report,
                "llm_error": str(e),
                "llm_metadata": {
                    "model": self.llm_client.model,
                    "generated_at": datetime.utcnow().isoformat(),
                    "error": True
                }
            }
    
    async def answer_query(
        self,
        query: str,
        analysis_report: Dict[str, Any]
    ) -> str:
        """
        Answer natural language query about analysis.
        
        Args:
            query: User query
            analysis_report: Analysis report data
        
        Returns:
            Answer to query
        """
        logger.info(f"Answering query: {query[:50]}...")
        
        try:
            # Check cache
            cache_key = self._generate_query_cache_key(query, analysis_report)
            if self.enable_caching and cache_key in self._cache:
                logger.info("Cache hit for query")
                return self._cache[cache_key]
            
            # Handle query
            answer = await handle_query(
                query=query,
                analysis_report=analysis_report,
                llm_client=self.llm_client
            )
            
            # Cache result
            if self.enable_caching:
                self._cache[cache_key] = answer
            
            return answer
            
        except Exception as e:
            logger.error(f"Failed to answer query: {e}")
            return f"I apologize, but I encountered an error processing your query: {str(e)}"
    
    async def _generate_insights_with_fallback(
        self,
        technical_report: Dict[str, Any]
    ) -> str:
        """Generate insights with fallback to basic summary."""
        try:
            return await generate_insights(
                analysis_report=technical_report,
                llm_client=self.llm_client
            )
        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            return self._generate_basic_insights(technical_report)
    
    async def _enhance_recommendations_with_fallback(
        self,
        recommendations: list
    ) -> list:
        """Enhance recommendations with fallback to original."""
        try:
            return await enhance_recommendations(
                recommendations=recommendations,
                llm_client=self.llm_client
            )
        except Exception as e:
            logger.error(f"Failed to enhance recommendations: {e}")
            return recommendations
    
    async def _generate_summary_with_fallback(
        self,
        technical_report: Dict[str, Any],
        insights: str
    ) -> str:
        """Generate executive summary with fallback to basic summary."""
        try:
            return await generate_executive_summary(
                analysis_report=technical_report,
                insights=insights,
                llm_client=self.llm_client
            )
        except Exception as e:
            logger.error(f"Failed to generate executive summary: {e}")
            return self._generate_basic_summary(technical_report)
    
    def _generate_basic_insights(
        self,
        technical_report: Dict[str, Any]
    ) -> str:
        """Generate basic insights without LLM (fallback)."""
        idle_count = len(technical_report.get("idle_resources", []))
        monthly_waste = technical_report.get("total_monthly_waste", 0)
        anomaly_count = len(technical_report.get("anomalies", []))
        
        return (
            f"Analysis identified {idle_count} idle resources wasting "
            f"${monthly_waste:,.2f} per month. "
            f"Detected {anomaly_count} cost anomalies requiring attention. "
            f"Review recommendations for optimization opportunities."
        )
    
    def _generate_basic_summary(
        self,
        technical_report: Dict[str, Any]
    ) -> str:
        """Generate basic executive summary without LLM (fallback)."""
        monthly_waste = technical_report.get("total_monthly_waste", 0)
        annual_waste = monthly_waste * 12
        
        return (
            f"Executive Summary: Identified ${monthly_waste:,.2f} in monthly "
            f"optimization opportunities (${annual_waste:,.2f} annually). "
            f"Immediate action recommended on idle resources and cost anomalies. "
            f"See detailed recommendations for implementation guidance."
        )
    
    def _generate_cache_key(self, data: Dict[str, Any]) -> str:
        """
        Generate cache key from data.
        
        Args:
            data: Data to generate key from
        
        Returns:
            Cache key (hash)
        """
        # Convert to JSON and hash
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def _generate_query_cache_key(
        self,
        query: str,
        analysis_report: Dict[str, Any]
    ) -> str:
        """Generate cache key for query."""
        combined = f"{query}:{self._generate_cache_key(analysis_report)}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def clear_cache(self):
        """Clear LLM response cache."""
        self._cache.clear()
        logger.info("LLM cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics
        """
        return {
            "cache_size": len(self._cache),
            "cache_enabled": self.enable_caching
        }
