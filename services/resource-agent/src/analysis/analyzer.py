"""
Resource Analysis Engine

Analyzes GPU and system metrics to detect bottlenecks and generate recommendations.
"""

import logging
from typing import List, Optional, Tuple
from datetime import datetime

from src.models.analysis import (
    AnalysisResult,
    Bottleneck,
    BottleneckType,
    ResourceUtilization,
    UtilizationLevel,
    EfficiencyScore,
    OptimizationRecommendation,
    Severity
)
from src.models.gpu_metrics import GPUMetricsCollection
from src.models.system_metrics import SystemMetricsCollection

logger = logging.getLogger("resource_agent.analyzer")


class ResourceAnalyzer:
    """Analyzer for resource utilization and bottleneck detection."""
    
    # Thresholds for bottleneck detection
    CPU_BOTTLENECK_THRESHOLD = 80.0
    GPU_BOTTLENECK_THRESHOLD = 90.0
    MEMORY_BOTTLENECK_THRESHOLD = 85.0
    DISK_BOTTLENECK_THRESHOLD = 80.0
    NETWORK_BOTTLENECK_THRESHOLD = 75.0
    
    # Thresholds for utilization levels
    IDLE_THRESHOLD = 20.0
    LOW_THRESHOLD = 50.0
    MODERATE_THRESHOLD = 70.0
    HIGH_THRESHOLD = 90.0
    
    def __init__(self):
        """Initialize analyzer."""
        logger.info("Resource analyzer initialized")
    
    def _get_utilization_level(self, percent: float) -> UtilizationLevel:
        """
        Get utilization level from percentage.
        
        Args:
            percent: Utilization percentage
            
        Returns:
            UtilizationLevel
        """
        if percent < self.IDLE_THRESHOLD:
            return UtilizationLevel.IDLE
        elif percent < self.LOW_THRESHOLD:
            return UtilizationLevel.LOW
        elif percent < self.MODERATE_THRESHOLD:
            return UtilizationLevel.MODERATE
        elif percent < self.HIGH_THRESHOLD:
            return UtilizationLevel.HIGH
        else:
            return UtilizationLevel.CRITICAL
    
    def _detect_cpu_bottleneck(self, cpu_metrics) -> Optional[Bottleneck]:
        """Detect CPU bottleneck."""
        util = cpu_metrics.utilization_percent
        
        if util >= self.CPU_BOTTLENECK_THRESHOLD:
            severity = Severity.CRITICAL if util >= 95 else Severity.WARNING
            
            recommendations = []
            if util >= 95:
                recommendations.append("Consider scaling to instances with more CPU cores")
                recommendations.append("Optimize CPU-intensive workloads")
            else:
                recommendations.append("Monitor CPU usage trends")
                recommendations.append("Consider workload optimization")
            
            return Bottleneck(
                type=BottleneckType.CPU,
                severity=severity,
                utilization_percent=util,
                threshold_percent=self.CPU_BOTTLENECK_THRESHOLD,
                message=f"CPU utilization at {util:.1f}% (threshold: {self.CPU_BOTTLENECK_THRESHOLD}%)",
                recommendations=recommendations
            )
        
        return None
    
    def _detect_gpu_bottleneck(self, gpu_metrics: Optional[GPUMetricsCollection]) -> Optional[Bottleneck]:
        """Detect GPU bottleneck."""
        if not gpu_metrics or gpu_metrics.gpu_count == 0:
            return None
        
        avg_util = gpu_metrics.average_gpu_utilization
        
        if avg_util >= self.GPU_BOTTLENECK_THRESHOLD:
            severity = Severity.CRITICAL if avg_util >= 98 else Severity.WARNING
            
            recommendations = []
            if avg_util >= 98:
                recommendations.append("Add more GPUs to distribute workload")
                recommendations.append("Optimize GPU kernels for better efficiency")
            else:
                recommendations.append("Monitor GPU usage patterns")
                recommendations.append("Consider batch size optimization")
            
            return Bottleneck(
                type=BottleneckType.GPU,
                severity=severity,
                utilization_percent=avg_util,
                threshold_percent=self.GPU_BOTTLENECK_THRESHOLD,
                message=f"GPU utilization at {avg_util:.1f}% (threshold: {self.GPU_BOTTLENECK_THRESHOLD}%)",
                recommendations=recommendations
            )
        
        return None
    
    def _detect_memory_bottleneck(self, memory_metrics) -> Optional[Bottleneck]:
        """Detect memory bottleneck."""
        util = memory_metrics.utilization_percent
        
        if util >= self.MEMORY_BOTTLENECK_THRESHOLD:
            severity = Severity.CRITICAL if util >= 95 else Severity.WARNING
            
            recommendations = []
            if util >= 95:
                recommendations.append("Upgrade to instances with more RAM")
                recommendations.append("Optimize memory usage in applications")
                recommendations.append("Enable memory compression if available")
            else:
                recommendations.append("Monitor memory usage trends")
                recommendations.append("Consider memory optimization")
            
            return Bottleneck(
                type=BottleneckType.MEMORY,
                severity=severity,
                utilization_percent=util,
                threshold_percent=self.MEMORY_BOTTLENECK_THRESHOLD,
                message=f"Memory utilization at {util:.1f}% (threshold: {self.MEMORY_BOTTLENECK_THRESHOLD}%)",
                recommendations=recommendations
            )
        
        return None
    
    def _calculate_efficiency_scores(
        self,
        system_metrics: SystemMetricsCollection,
        gpu_metrics: Optional[GPUMetricsCollection]
    ) -> EfficiencyScore:
        """Calculate efficiency scores."""
        
        # CPU efficiency (based on utilization and core balance)
        cpu_util = system_metrics.cpu.utilization_percent
        per_core = system_metrics.cpu.per_core_utilization
        
        # CPU balance score (how evenly distributed across cores)
        if per_core:
            avg_core = sum(per_core) / len(per_core)
            variance = sum((x - avg_core) ** 2 for x in per_core) / len(per_core)
            cpu_balance_score = max(0, 100 - variance)
        else:
            cpu_balance_score = 50.0
        
        # CPU efficiency (prefer 60-80% utilization)
        if 60 <= cpu_util <= 80:
            cpu_efficiency = 100.0
        elif cpu_util < 60:
            cpu_efficiency = (cpu_util / 60) * 100
        else:
            cpu_efficiency = max(0, 100 - (cpu_util - 80) * 2)
        
        # Memory efficiency (prefer 60-80% utilization)
        mem_util = system_metrics.memory.utilization_percent
        if 60 <= mem_util <= 80:
            memory_efficiency = 100.0
        elif mem_util < 60:
            memory_efficiency = (mem_util / 60) * 100
        else:
            memory_efficiency = max(0, 100 - (mem_util - 80) * 2)
        
        memory_availability_score = 100 - mem_util
        
        # GPU efficiency
        gpu_efficiency = None
        gpu_utilization_score = None
        gpu_power_efficiency = None
        
        if gpu_metrics and gpu_metrics.gpu_count > 0:
            gpu_util = gpu_metrics.average_gpu_utilization
            
            # GPU utilization score (prefer 70-90%)
            if 70 <= gpu_util <= 90:
                gpu_utilization_score = 100.0
            elif gpu_util < 70:
                gpu_utilization_score = (gpu_util / 70) * 100
            else:
                gpu_utilization_score = max(0, 100 - (gpu_util - 90) * 2)
            
            # GPU power efficiency (utilization per watt)
            if gpu_metrics.total_power_draw_watts > 0:
                power_per_util = gpu_metrics.total_power_draw_watts / max(gpu_util, 1)
                # Lower is better, normalize to 0-100
                gpu_power_efficiency = max(0, 100 - power_per_util)
            else:
                gpu_power_efficiency = 50.0
            
            gpu_efficiency = (gpu_utilization_score + gpu_power_efficiency) / 2
        
        # Overall score
        if gpu_efficiency is not None:
            overall_score = (cpu_efficiency + memory_efficiency + gpu_efficiency) / 3
        else:
            overall_score = (cpu_efficiency + memory_efficiency) / 2
        
        return EfficiencyScore(
            overall_score=overall_score,
            gpu_efficiency=gpu_efficiency,
            cpu_efficiency=cpu_efficiency,
            memory_efficiency=memory_efficiency,
            gpu_utilization_score=gpu_utilization_score,
            gpu_power_efficiency=gpu_power_efficiency,
            cpu_balance_score=cpu_balance_score,
            memory_availability_score=memory_availability_score
        )
    
    def _generate_recommendations(
        self,
        bottlenecks: List[Bottleneck],
        efficiency: EfficiencyScore,
        system_metrics: SystemMetricsCollection,
        gpu_metrics: Optional[GPUMetricsCollection]
    ) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Recommendations based on bottlenecks
        for bottleneck in bottlenecks:
            if bottleneck.severity == Severity.CRITICAL:
                for rec in bottleneck.recommendations:
                    recommendations.append(OptimizationRecommendation(
                        priority=Severity.CRITICAL,
                        category="bottleneck_resolution",
                        title=f"Resolve {bottleneck.type.value.upper()} Bottleneck",
                        description=rec,
                        expected_impact="High - will significantly improve performance",
                        implementation_effort="medium"
                    ))
        
        # Recommendations based on efficiency
        if efficiency.overall_score < 50:
            recommendations.append(OptimizationRecommendation(
                priority=Severity.WARNING,
                category="efficiency_improvement",
                title="Improve Overall Resource Efficiency",
                description="Overall efficiency is low. Review resource allocation and workload distribution.",
                expected_impact="Medium - will improve resource utilization",
                implementation_effort="medium"
            ))
        
        # GPU-specific recommendations
        if gpu_metrics and gpu_metrics.gpu_count > 0:
            if efficiency.gpu_efficiency and efficiency.gpu_efficiency < 60:
                recommendations.append(OptimizationRecommendation(
                    priority=Severity.INFO,
                    category="gpu_optimization",
                    title="Optimize GPU Utilization",
                    description="GPU efficiency is below optimal. Consider batch size tuning or model optimization.",
                    expected_impact="Medium - will improve GPU efficiency",
                    implementation_effort="low"
                ))
        
        # CPU balance recommendations
        if efficiency.cpu_balance_score < 70:
            recommendations.append(OptimizationRecommendation(
                priority=Severity.INFO,
                category="cpu_optimization",
                title="Improve CPU Core Balance",
                description="CPU load is unevenly distributed across cores. Review thread affinity and parallelization.",
                expected_impact="Low - will improve CPU efficiency",
                implementation_effort="medium"
            ))
        
        return recommendations
    
    def analyze(
        self,
        system_metrics: SystemMetricsCollection,
        gpu_metrics: Optional[GPUMetricsCollection] = None
    ) -> AnalysisResult:
        """
        Analyze resource metrics and generate insights.
        
        Args:
            system_metrics: System metrics
            gpu_metrics: GPU metrics (optional)
            
        Returns:
            AnalysisResult: Analysis results with bottlenecks and recommendations
        """
        try:
            # Detect bottlenecks
            bottlenecks = []
            
            cpu_bottleneck = self._detect_cpu_bottleneck(system_metrics.cpu)
            if cpu_bottleneck:
                bottlenecks.append(cpu_bottleneck)
            
            gpu_bottleneck = self._detect_gpu_bottleneck(gpu_metrics)
            if gpu_bottleneck:
                bottlenecks.append(gpu_bottleneck)
            
            memory_bottleneck = self._detect_memory_bottleneck(system_metrics.memory)
            if memory_bottleneck:
                bottlenecks.append(memory_bottleneck)
            
            # Determine primary bottleneck
            if bottlenecks:
                # Sort by severity and utilization
                bottlenecks.sort(key=lambda x: (
                    x.severity == Severity.CRITICAL,
                    x.utilization_percent
                ), reverse=True)
                primary_bottleneck = bottlenecks[0].type
            else:
                primary_bottleneck = BottleneckType.NONE
            
            # Create utilization summary
            utilization_summary = [
                ResourceUtilization(
                    resource_type="cpu",
                    current_percent=system_metrics.cpu.utilization_percent,
                    level=self._get_utilization_level(system_metrics.cpu.utilization_percent),
                    is_bottleneck=cpu_bottleneck is not None
                ),
                ResourceUtilization(
                    resource_type="memory",
                    current_percent=system_metrics.memory.utilization_percent,
                    level=self._get_utilization_level(system_metrics.memory.utilization_percent),
                    is_bottleneck=memory_bottleneck is not None
                )
            ]
            
            if gpu_metrics and gpu_metrics.gpu_count > 0:
                utilization_summary.append(ResourceUtilization(
                    resource_type="gpu",
                    current_percent=gpu_metrics.average_gpu_utilization,
                    level=self._get_utilization_level(gpu_metrics.average_gpu_utilization),
                    is_bottleneck=gpu_bottleneck is not None
                ))
            
            # Calculate efficiency scores
            efficiency = self._calculate_efficiency_scores(system_metrics, gpu_metrics)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                bottlenecks,
                efficiency,
                system_metrics,
                gpu_metrics
            )
            
            # Determine overall health
            health_score = efficiency.overall_score
            if health_score >= 70:
                overall_health = "healthy"
            elif health_score >= 50:
                overall_health = "degraded"
            else:
                overall_health = "critical"
            
            # Adjust health based on critical bottlenecks
            if any(b.severity == Severity.CRITICAL for b in bottlenecks):
                overall_health = "critical"
                health_score = min(health_score, 40)
            
            return AnalysisResult(
                instance_id=system_metrics.instance_id,
                primary_bottleneck=primary_bottleneck,
                bottlenecks=bottlenecks,
                utilization_summary=utilization_summary,
                efficiency=efficiency,
                recommendations=recommendations,
                overall_health=overall_health,
                health_score=health_score
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze metrics: {e}")
            raise
