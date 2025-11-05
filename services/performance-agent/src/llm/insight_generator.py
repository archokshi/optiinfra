"""Insight generator for performance data."""

import logging
from typing import Dict, List, Any
from src.llm.llm_client import LLMClient
from src.llm.prompt_templates import (
    PERFORMANCE_EXPERT_SYSTEM_PROMPT,
    PERFORMANCE_INSIGHT_PROMPT,
    BOTTLENECK_EXPLANATION_PROMPT,
    OPTIMIZATION_ENHANCEMENT_PROMPT,
    EXECUTIVE_SUMMARY_PROMPT,
    ROI_ANALYSIS_PROMPT
)

logger = logging.getLogger(__name__)


class InsightGenerator:
    """Generate natural language insights from performance data."""
    
    def __init__(self, llm_client: LLMClient):
        """Initialize insight generator."""
        self.llm_client = llm_client
    
    async def generate_performance_insights(
        self,
        instance_id: str,
        instance_type: str,
        metrics: Dict[str, Any],
        bottlenecks: List[Dict[str, Any]]
    ) -> str:
        """Generate comprehensive performance insights."""
        metrics_str = self._format_metrics(metrics)
        bottlenecks_str = self._format_bottlenecks(bottlenecks)
        
        prompt = PERFORMANCE_INSIGHT_PROMPT.format(
            instance_id=instance_id,
            instance_type=instance_type,
            metrics=metrics_str,
            bottlenecks=bottlenecks_str
        )
        
        try:
            response = await self.llm_client.generate(
                prompt=prompt,
                system_prompt=PERFORMANCE_EXPERT_SYSTEM_PROMPT,
                max_tokens=1500,
                temperature=0.7
            )
            
            logger.info(f"Generated insights for {instance_id}")
            return response["content"]
            
        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            return "Unable to generate insights at this time."
    
    async def explain_bottleneck(self, bottleneck: Dict[str, Any]) -> str:
        """Explain bottleneck in business-friendly language."""
        prompt = BOTTLENECK_EXPLANATION_PROMPT.format(
            bottleneck_type=bottleneck.get("type", "UNKNOWN"),
            severity=bottleneck.get("severity", "UNKNOWN"),
            metric_name=bottleneck.get("metric_name", "unknown"),
            current_value=bottleneck.get("current_value", 0),
            threshold_value=bottleneck.get("threshold_value", 0),
            description=bottleneck.get("description", "No description")
        )
        
        try:
            response = await self.llm_client.generate(
                prompt=prompt,
                system_prompt=PERFORMANCE_EXPERT_SYSTEM_PROMPT,
                max_tokens=800,
                temperature=0.6
            )
            return response["content"]
        except Exception as e:
            logger.error(f"Failed to explain bottleneck: {e}")
            return bottleneck.get("description", "Unknown issue")
    
    async def enhance_optimization(
        self,
        optimization: Dict[str, Any],
        current_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance optimization recommendation with business context."""
        prompt = OPTIMIZATION_ENHANCEMENT_PROMPT.format(
            optimization_type=optimization.get("type", "UNKNOWN"),
            priority=optimization.get("priority", "MEDIUM"),
            description=optimization.get("description", "No description"),
            current_config=str(current_config),
            config_changes=str(optimization.get("config_changes", {}))
        )
        
        try:
            response = await self.llm_client.generate(
                prompt=prompt,
                system_prompt=PERFORMANCE_EXPERT_SYSTEM_PROMPT,
                max_tokens=1000,
                temperature=0.6
            )
            
            enhanced = optimization.copy()
            enhanced["business_context"] = response["content"]
            enhanced["llm_enhanced"] = True
            return enhanced
        except Exception as e:
            logger.error(f"Failed to enhance optimization: {e}")
            return optimization
    
    async def generate_executive_summary(
        self,
        instance_id: str,
        instance_type: str,
        metrics: Dict[str, Any],
        bottlenecks: List[Dict[str, Any]],
        optimizations: List[Dict[str, Any]]
    ) -> str:
        """Generate executive summary."""
        metrics_summary = self._format_metrics_summary(metrics)
        bottlenecks_summary = self._format_bottlenecks_summary(bottlenecks)
        optimizations_summary = self._format_optimizations_summary(optimizations)
        
        prompt = EXECUTIVE_SUMMARY_PROMPT.format(
            instance_id=instance_id,
            instance_type=instance_type,
            metrics_summary=metrics_summary,
            bottlenecks_summary=bottlenecks_summary,
            optimizations_summary=optimizations_summary
        )
        
        try:
            response = await self.llm_client.generate(
                prompt=prompt,
                system_prompt=PERFORMANCE_EXPERT_SYSTEM_PROMPT,
                max_tokens=2000,
                temperature=0.7
            )
            logger.info(f"Generated executive summary for {instance_id}")
            return response["content"]
        except Exception as e:
            logger.error(f"Failed to generate executive summary: {e}")
            return "Unable to generate executive summary at this time."
    
    def _format_metrics(self, metrics: Dict[str, Any]) -> str:
        """Format metrics for prompt."""
        lines = []
        if "request_metrics" in metrics:
            rm = metrics["request_metrics"]
            lines.append(f"Request Metrics:")
            lines.append(f"  - Success: {rm.get('success_total', 0)} requests")
            lines.append(f"  - Failures: {rm.get('failure_total', 0)} requests")
            lines.append(f"  - TTFT: {rm.get('time_to_first_token_seconds', 0):.3f}s")
            lines.append(f"  - Latency: {rm.get('e2e_request_latency_seconds', 0):.3f}s")
        
        if "gpu_metrics" in metrics:
            gm = metrics["gpu_metrics"]
            lines.append(f"GPU Metrics:")
            lines.append(f"  - Cache Usage: {gm.get('cache_usage_perc', 0):.1f}%")
            lines.append(f"  - Memory: {gm.get('memory_usage_bytes', 0) / 1e9:.2f}GB")
            lines.append(f"  - Running: {gm.get('num_requests_running', 0)}")
            lines.append(f"  - Waiting: {gm.get('num_requests_waiting', 0)}")
        
        if "throughput_metrics" in metrics:
            tm = metrics["throughput_metrics"]
            lines.append(f"Throughput Metrics:")
            lines.append(f"  - Tokens/sec: {tm.get('tokens_per_second', 0):.1f}")
        
        return "\n".join(lines)
    
    def _format_bottlenecks(self, bottlenecks: List[Dict[str, Any]]) -> str:
        """Format bottlenecks for prompt."""
        if not bottlenecks:
            return "No bottlenecks detected"
        
        lines = []
        for i, b in enumerate(bottlenecks, 1):
            lines.append(f"{i}. {b.get('type', 'UNKNOWN')} ({b.get('severity', 'UNKNOWN')})")
            lines.append(f"   {b.get('description', 'No description')}")
            lines.append(f"   Recommendation: {b.get('recommendation', 'None')}")
        return "\n".join(lines)
    
    def _format_metrics_summary(self, metrics: Dict[str, Any]) -> str:
        """Format metrics summary."""
        return self._format_metrics(metrics)
    
    def _format_bottlenecks_summary(self, bottlenecks: List[Dict[str, Any]]) -> str:
        """Format bottlenecks summary."""
        if not bottlenecks:
            return "No critical issues detected"
        return f"{len(bottlenecks)} issues: " + ", ".join([b.get("type", "UNKNOWN") for b in bottlenecks])
    
    def _format_optimizations_summary(self, optimizations: List[Dict[str, Any]]) -> str:
        """Format optimizations summary."""
        if not optimizations:
            return "No optimizations recommended"
        return f"{len(optimizations)} optimizations: " + ", ".join([o.get("type", "UNKNOWN") for o in optimizations])
