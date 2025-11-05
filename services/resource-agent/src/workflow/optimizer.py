"""
Resource Optimization Workflow

Orchestrates resource optimization using metrics collection, analysis, and LLM insights.
"""

import logging
import time
import uuid
from typing import Optional, List

from src.models.workflow import (
    WorkflowResult,
    WorkflowState,
    WorkflowStatus,
    OptimizationAction,
    OptimizationPriority
)
from src.collectors.gpu_collector import GPUCollector
from src.collectors.system_collector import SystemCollector
from src.lmcache.client import LMCacheClient
from src.analysis.analyzer import ResourceAnalyzer
from src.llm.llm_client import LLMClientFactory
from src.llm.prompt_templates import PromptTemplates
from src.config import settings

logger = logging.getLogger("resource_agent.workflow")


class OptimizationWorkflow:
    """Orchestrates resource optimization workflow."""
    
    def __init__(self):
        """Initialize workflow."""
        self.llm_client = LLMClientFactory.get_client()
        logger.info("Optimization workflow initialized")
    
    async def run(self, instance_id: Optional[str] = None) -> WorkflowResult:
        """
        Run optimization workflow.
        
        Args:
            instance_id: Instance identifier (defaults to agent_id)
        
        Returns:
            WorkflowResult: Workflow execution result
        """
        workflow_id = str(uuid.uuid4())
        instance_id = instance_id or settings.agent_id
        start_time = time.time()
        
        state = WorkflowState(
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING
        )
        
        try:
            # Step 1: Collect metrics
            logger.info(f"[{workflow_id}] Collecting metrics...")
            state.current_step = "collect_metrics"
            await self._collect_metrics(state, instance_id)
            
            # Step 2: Analyze resources
            logger.info(f"[{workflow_id}] Analyzing resources...")
            state.current_step = "analyze_resources"
            await self._analyze_resources(state, instance_id)
            
            # Step 3: Generate LLM insights
            logger.info(f"[{workflow_id}] Generating insights...")
            state.current_step = "generate_insights"
            await self._generate_insights(state)
            
            # Step 4: Create action plan
            logger.info(f"[{workflow_id}] Creating action plan...")
            state.current_step = "create_actions"
            actions = await self._create_actions(state)
            
            # Build result
            execution_time = (time.time() - start_time) * 1000
            
            result = WorkflowResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.COMPLETED,
                instance_id=instance_id,
                primary_bottleneck=state.analysis_result.get('primary_bottleneck') if state.analysis_result else None,
                health_score=state.analysis_result.get('health_score') if state.analysis_result else None,
                llm_insights=state.llm_insights,
                actions=actions,
                execution_time_ms=execution_time
            )
            
            logger.info(f"[{workflow_id}] Workflow completed in {execution_time:.0f}ms")
            return result
            
        except Exception as e:
            logger.error(f"[{workflow_id}] Workflow failed: {e}")
            execution_time = (time.time() - start_time) * 1000
            
            return WorkflowResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                instance_id=instance_id,
                actions=[],
                execution_time_ms=execution_time,
                error_message=str(e)
            )
    
    async def _collect_metrics(self, state: WorkflowState, instance_id: str):
        """Collect all metrics."""
        try:
            # GPU metrics
            with GPUCollector() as gpu_collector:
                if gpu_collector.is_available():
                    gpu_metrics = gpu_collector.collect(instance_id=instance_id)
                    state.gpu_metrics = gpu_metrics.model_dump()
                else:
                    state.gpu_metrics = {"gpu_count": 0, "available": False}
            
            # System metrics
            system_collector = SystemCollector()
            system_metrics = system_collector.collect(instance_id=instance_id)
            state.system_metrics = system_metrics.model_dump()
            
            # LMCache metrics
            lmcache_client = LMCacheClient()
            lmcache_status = lmcache_client.get_status(instance_id=instance_id)
            state.lmcache_metrics = lmcache_status.metrics.model_dump()
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            state.errors.append(f"Metrics collection: {str(e)}")
            raise
    
    async def _analyze_resources(self, state: WorkflowState, instance_id: str):
        """Analyze resource utilization."""
        try:
            analyzer = ResourceAnalyzer()
            
            # Convert metrics back to objects
            from src.models.system_metrics import SystemMetricsCollection
            from src.models.gpu_metrics import GPUMetricsCollection
            
            system_metrics = SystemMetricsCollection(**state.system_metrics)
            
            gpu_metrics = None
            if state.gpu_metrics and state.gpu_metrics.get('gpu_count', 0) > 0:
                gpu_metrics = GPUMetricsCollection(**state.gpu_metrics)
            
            # Run analysis
            analysis = analyzer.analyze(system_metrics, gpu_metrics)
            state.analysis_result = analysis.model_dump()
            
        except Exception as e:
            logger.error(f"Failed to analyze resources: {e}")
            state.errors.append(f"Analysis: {str(e)}")
            raise
    
    async def _generate_insights(self, state: WorkflowState):
        """Generate LLM insights."""
        try:
            if not self.llm_client.is_available():
                logger.warning("LLM client not available, skipping insights generation")
                state.llm_insights = "LLM insights not available (API key not configured)"
                return
            
            # Format prompt
            analysis_summary = self._format_analysis_summary(state.analysis_result)
            
            prompt = PromptTemplates.format_metrics_analysis(
                gpu_metrics=state.gpu_metrics or {},
                system_metrics=state.system_metrics or {},
                lmcache_metrics=state.lmcache_metrics or {},
                analysis_summary=analysis_summary
            )
            
            # Generate insights
            insights = await self.llm_client.generate(
                prompt=prompt,
                system_prompt=PromptTemplates.SYSTEM_PROMPT,
                max_tokens=1500,
                temperature=0.7
            )
            
            state.llm_insights = insights
            
        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            state.llm_insights = f"Failed to generate insights: {str(e)}"
            state.errors.append(f"LLM insights: {str(e)}")
    
    async def _create_actions(self, state: WorkflowState) -> List[OptimizationAction]:
        """Create optimization actions."""
        actions = []
        
        try:
            # Extract recommendations from analysis
            if state.analysis_result and 'recommendations' in state.analysis_result:
                for rec in state.analysis_result['recommendations']:
                    action = OptimizationAction(
                        title=rec.get('title', 'Optimization Action'),
                        description=rec.get('description', ''),
                        priority=OptimizationPriority(rec.get('priority', 'medium')),
                        expected_impact=rec.get('expected_impact', 'Unknown'),
                        implementation_effort=rec.get('implementation_effort', 'medium'),
                        category=rec.get('category', 'general'),
                        prerequisites=[]
                    )
                    actions.append(action)
            
            # Add LLM-suggested actions if available
            if state.llm_insights and "LLM insights not available" not in state.llm_insights:
                # Parse insights for additional actions
                # (In production, you'd use structured output or parsing)
                pass
            
        except Exception as e:
            logger.error(f"Failed to create actions: {e}")
            state.errors.append(f"Action creation: {str(e)}")
        
        return actions
    
    def _format_analysis_summary(self, analysis: dict) -> str:
        """Format analysis result as summary text."""
        if not analysis:
            return "No analysis available"
        
        summary_parts = [
            f"Primary Bottleneck: {analysis.get('primary_bottleneck', 'none')}",
            f"Health Score: {analysis.get('health_score', 0):.1f}/100",
            f"Overall Health: {analysis.get('overall_health', 'unknown')}"
        ]
        
        if 'bottlenecks' in analysis and analysis['bottlenecks']:
            summary_parts.append(f"Bottlenecks Detected: {len(analysis['bottlenecks'])}")
        
        if 'efficiency' in analysis:
            eff = analysis['efficiency']
            summary_parts.append(f"CPU Efficiency: {eff.get('cpu_efficiency', 0):.1f}/100")
            summary_parts.append(f"Memory Efficiency: {eff.get('memory_efficiency', 0):.1f}/100")
        
        return "\n".join(summary_parts)
