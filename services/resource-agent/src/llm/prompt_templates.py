"""
Prompt Templates for Resource Optimization

Templates for generating LLM prompts for resource analysis and optimization.
"""

from typing import Dict, Any


class PromptTemplates:
    """Prompt templates for resource optimization."""
    
    SYSTEM_PROMPT = """You are an expert resource optimization AI assistant for cloud infrastructure.
Your role is to analyze GPU, CPU, memory, and cache metrics to provide actionable optimization recommendations.

Focus on:
- Identifying resource bottlenecks
- Optimizing GPU/CPU utilization
- Improving memory efficiency
- Maximizing LMCache hit rates
- Reducing infrastructure costs

Provide specific, actionable recommendations with expected impact and implementation effort."""

    METRICS_ANALYSIS_PROMPT = """Analyze the following resource metrics and provide optimization insights:

**GPU Metrics:**
{gpu_metrics}

**System Metrics:**
{system_metrics}

**LMCache Metrics:**
{lmcache_metrics}

**Current Analysis:**
{analysis_summary}

Provide:
1. Key findings and bottlenecks
2. Top 3 optimization recommendations
3. Expected impact for each recommendation
4. Implementation priority (high/medium/low)

Format as clear, actionable bullet points."""

    RECOMMENDATION_PROMPT = """Based on the resource analysis, generate detailed optimization recommendations:

**Bottlenecks Detected:**
{bottlenecks}

**Efficiency Scores:**
{efficiency_scores}

**Current Utilization:**
{utilization_summary}

Generate specific recommendations for:
1. Immediate actions (quick wins)
2. Short-term optimizations (1-2 weeks)
3. Long-term improvements (1-3 months)

For each recommendation, include:
- Action description
- Expected impact (cost/performance)
- Implementation effort
- Prerequisites"""

    @staticmethod
    def format_metrics_analysis(
        gpu_metrics: Dict[str, Any],
        system_metrics: Dict[str, Any],
        lmcache_metrics: Dict[str, Any],
        analysis_summary: str
    ) -> str:
        """
        Format metrics analysis prompt.
        
        Args:
            gpu_metrics: GPU metrics dictionary
            system_metrics: System metrics dictionary
            lmcache_metrics: LMCache metrics dictionary
            analysis_summary: Analysis summary text
        
        Returns:
            Formatted prompt
        """
        return PromptTemplates.METRICS_ANALYSIS_PROMPT.format(
            gpu_metrics=PromptTemplates._format_gpu_metrics(gpu_metrics),
            system_metrics=PromptTemplates._format_system_metrics(system_metrics),
            lmcache_metrics=PromptTemplates._format_lmcache_metrics(lmcache_metrics),
            analysis_summary=analysis_summary
        )
    
    @staticmethod
    def format_recommendation_prompt(
        bottlenecks: str,
        efficiency_scores: Dict[str, float],
        utilization_summary: str
    ) -> str:
        """
        Format recommendation prompt.
        
        Args:
            bottlenecks: Bottleneck description
            efficiency_scores: Efficiency scores dictionary
            utilization_summary: Utilization summary text
        
        Returns:
            Formatted prompt
        """
        return PromptTemplates.RECOMMENDATION_PROMPT.format(
            bottlenecks=bottlenecks,
            efficiency_scores=PromptTemplates._format_efficiency(efficiency_scores),
            utilization_summary=utilization_summary
        )
    
    @staticmethod
    def _format_gpu_metrics(metrics: Dict[str, Any]) -> str:
        """Format GPU metrics for prompt."""
        if not metrics or metrics.get('gpu_count', 0) == 0:
            return "No GPU detected"
        
        return f"""- GPU Count: {metrics.get('gpu_count', 0)}
- Average Utilization: {metrics.get('average_gpu_utilization', 0):.1f}%
- Average Memory Utilization: {metrics.get('average_memory_utilization', 0):.1f}%
- Total Memory: {metrics.get('total_memory_total_mb', 0):.0f} MB
- Memory Used: {metrics.get('total_memory_used_mb', 0):.0f} MB
- Average Temperature: {metrics.get('average_temperature', 0):.1f}°C
- Total Power Draw: {metrics.get('total_power_draw_watts', 0):.1f}W"""
    
    @staticmethod
    def _format_system_metrics(metrics: Dict[str, Any]) -> str:
        """Format system metrics for prompt."""
        cpu = metrics.get('cpu', {})
        memory = metrics.get('memory', {})
        
        return f"""- CPU Utilization: {cpu.get('utilization_percent', 0):.1f}%
- CPU Cores: {cpu.get('cpu_count', 0)} ({cpu.get('physical_cores', 0)} physical)
- Memory Utilization: {memory.get('utilization_percent', 0):.1f}%
- Memory Total: {memory.get('total_mb', 0):.0f} MB
- Memory Available: {memory.get('available_mb', 0):.0f} MB"""
    
    @staticmethod
    def _format_lmcache_metrics(metrics: Dict[str, Any]) -> str:
        """Format LMCache metrics for prompt."""
        if not metrics or not metrics.get('enabled', False):
            return "LMCache not enabled"
        
        return f"""- Status: {metrics.get('status', 'unknown')}
- Hit Rate: {metrics.get('hit_rate_percent', 0):.1f}%
- Cache Utilization: {metrics.get('utilization_percent', 0):.1f}%
- Total Size: {metrics.get('total_size_mb', 0):.0f} MB
- Used Size: {metrics.get('used_size_mb', 0):.0f} MB
- Memory Saved: {metrics.get('memory_saved_mb', 0):.0f} MB ({metrics.get('memory_savings_percent', 0):.1f}%)
- Tokens Cached: {metrics.get('tokens_cached', 0):,}
- Cache Hits: {metrics.get('cache_hits', 0):,}"""
    
    @staticmethod
    def _format_efficiency(scores: Dict[str, float]) -> str:
        """Format efficiency scores for prompt."""
        return f"""- Overall: {scores.get('overall_score', 0):.1f}/100
- CPU: {scores.get('cpu_efficiency', 0):.1f}/100
- Memory: {scores.get('memory_efficiency', 0):.1f}/100
- GPU: {scores.get('gpu_efficiency', 'N/A') if scores.get('gpu_efficiency') else 'N/A'}"""
