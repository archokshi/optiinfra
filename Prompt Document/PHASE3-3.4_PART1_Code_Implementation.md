# PHASE3-3.4 PART1: Analysis Engine - Code Implementation Plan

**Phase**: PHASE3-3.4  
**Agent**: Resource Agent  
**Objective**: Implement utilization analysis and bottleneck detection engine  
**Estimated Time**: 30+20m (50 minutes total)  
**Priority**: HIGH  
**Dependencies**: PHASE3-3.1, PHASE3-3.2, PHASE3-3.3

---

## Overview

This phase implements the Analysis Engine that processes GPU and system metrics to identify bottlenecks, analyze utilization patterns, and generate optimization recommendations. The engine uses rule-based analysis and threshold detection.

---

## Analysis Engine Overview

### What is the Analysis Engine?

The Analysis Engine is a component that:
- Analyzes resource utilization patterns
- Detects bottlenecks (CPU, GPU, memory, I/O)
- Identifies underutilized resources
- Generates optimization recommendations
- Calculates efficiency scores
- Tracks resource trends

### Key Analysis Types

#### Bottleneck Detection
- **CPU Bottleneck** - High CPU utilization (>80%)
- **GPU Bottleneck** - High GPU utilization (>90%)
- **Memory Bottleneck** - High memory usage (>85%)
- **Disk I/O Bottleneck** - High disk utilization
- **Network Bottleneck** - High network utilization

#### Utilization Analysis
- **Underutilization** - Resources not being used efficiently
- **Overutilization** - Resources at capacity
- **Balanced** - Optimal resource usage
- **Imbalanced** - Some resources overused, others idle

#### Efficiency Scoring
- **GPU Efficiency** - GPU utilization vs. power consumption
- **Memory Efficiency** - Memory usage vs. availability
- **Overall Efficiency** - Combined resource efficiency score

---

## Implementation Plan

### Step 1: Analysis Models (5 minutes)

#### 1.1 Create src/models/analysis.py

```python
"""
Analysis Models

Pydantic models for resource analysis results.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class BottleneckType(str, Enum):
    """Types of resource bottlenecks."""
    
    CPU = "cpu"
    GPU = "gpu"
    MEMORY = "memory"
    DISK_IO = "disk_io"
    NETWORK = "network"
    NONE = "none"


class UtilizationLevel(str, Enum):
    """Resource utilization levels."""
    
    IDLE = "idle"  # < 20%
    LOW = "low"  # 20-50%
    MODERATE = "moderate"  # 50-70%
    HIGH = "high"  # 70-90%
    CRITICAL = "critical"  # > 90%


class Severity(str, Enum):
    """Issue severity levels."""
    
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Bottleneck(BaseModel):
    """Bottleneck detection result."""
    
    type: BottleneckType = Field(..., description="Type of bottleneck")
    severity: Severity = Field(..., description="Severity level")
    utilization_percent: float = Field(..., ge=0, le=100, description="Current utilization %")
    threshold_percent: float = Field(..., description="Threshold that triggered detection")
    message: str = Field(..., description="Human-readable message")
    recommendations: List[str] = Field(default_factory=list, description="Optimization recommendations")


class ResourceUtilization(BaseModel):
    """Resource utilization summary."""
    
    resource_type: str = Field(..., description="Type of resource (cpu, gpu, memory, etc.)")
    current_percent: float = Field(..., ge=0, le=100, description="Current utilization %")
    level: UtilizationLevel = Field(..., description="Utilization level")
    is_bottleneck: bool = Field(default=False, description="Whether this is a bottleneck")


class EfficiencyScore(BaseModel):
    """Efficiency scoring."""
    
    overall_score: float = Field(..., ge=0, le=100, description="Overall efficiency score (0-100)")
    gpu_efficiency: Optional[float] = Field(None, ge=0, le=100, description="GPU efficiency score")
    cpu_efficiency: float = Field(..., ge=0, le=100, description="CPU efficiency score")
    memory_efficiency: float = Field(..., ge=0, le=100, description="Memory efficiency score")
    
    # Efficiency breakdown
    gpu_utilization_score: Optional[float] = Field(None, description="GPU utilization component")
    gpu_power_efficiency: Optional[float] = Field(None, description="GPU power efficiency component")
    cpu_balance_score: float = Field(..., description="CPU core balance score")
    memory_availability_score: float = Field(..., description="Memory availability score")


class OptimizationRecommendation(BaseModel):
    """Optimization recommendation."""
    
    priority: Severity = Field(..., description="Recommendation priority")
    category: str = Field(..., description="Category (scaling, optimization, etc.)")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    expected_impact: str = Field(..., description="Expected impact")
    implementation_effort: str = Field(..., description="Implementation effort (low, medium, high)")


class AnalysisResult(BaseModel):
    """Complete analysis result."""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    instance_id: str = Field(..., description="Instance identifier")
    
    # Bottleneck detection
    primary_bottleneck: BottleneckType = Field(..., description="Primary bottleneck")
    bottlenecks: List[Bottleneck] = Field(default_factory=list, description="All detected bottlenecks")
    
    # Utilization summary
    utilization_summary: List[ResourceUtilization] = Field(
        default_factory=list,
        description="Resource utilization summary"
    )
    
    # Efficiency scoring
    efficiency: EfficiencyScore = Field(..., description="Efficiency scores")
    
    # Recommendations
    recommendations: List[OptimizationRecommendation] = Field(
        default_factory=list,
        description="Optimization recommendations"
    )
    
    # Overall assessment
    overall_health: str = Field(..., description="Overall system health (healthy, degraded, critical)")
    health_score: float = Field(..., ge=0, le=100, description="Overall health score (0-100)")
```

---

### Step 2: Analysis Engine Implementation (15 minutes)

#### 2.1 Create src/analysis/__init__.py

```python
"""Analysis engine for resource optimization."""
```

#### 2.2 Create src/analysis/analyzer.py

```python
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
```

---

### Step 3: API Endpoint (5 minutes)

#### 3.1 Create src/api/analysis.py

```python
"""
Analysis API

Endpoints for resource analysis and recommendations.
"""

from fastapi import APIRouter, HTTPException, status

from src.models.analysis import AnalysisResult
from src.collectors.system_collector import SystemCollector
from src.collectors.gpu_collector import GPUCollector
from src.analysis.analyzer import ResourceAnalyzer
from src.config import settings

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get(
    "/",
    response_model=AnalysisResult,
    status_code=status.HTTP_200_OK,
    summary="Get resource analysis"
)
async def get_analysis() -> AnalysisResult:
    """
    Analyze current resource utilization and generate recommendations.
    
    Returns:
        AnalysisResult: Analysis results with bottlenecks and recommendations
        
    Raises:
        HTTPException: If analysis fails
    """
    try:
        # Collect metrics
        system_collector = SystemCollector()
        system_metrics = system_collector.collect(instance_id=settings.agent_id)
        
        # Collect GPU metrics if available
        gpu_metrics = None
        with GPUCollector() as gpu_collector:
            if gpu_collector.is_available():
                gpu_metrics = gpu_collector.collect(instance_id=settings.agent_id)
        
        # Analyze
        analyzer = ResourceAnalyzer()
        analysis = analyzer.analyze(system_metrics, gpu_metrics)
        
        return analysis
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze resources: {str(e)}"
        )


@router.get(
    "/health-score",
    status_code=status.HTTP_200_OK,
    summary="Get health score only"
)
async def get_health_score() -> dict:
    """
    Get overall health score.
    
    Returns:
        dict: Health score and status
    """
    try:
        system_collector = SystemCollector()
        system_metrics = system_collector.collect(instance_id=settings.agent_id)
        
        gpu_metrics = None
        with GPUCollector() as gpu_collector:
            if gpu_collector.is_available():
                gpu_metrics = gpu_collector.collect(instance_id=settings.agent_id)
        
        analyzer = ResourceAnalyzer()
        analysis = analyzer.analyze(system_metrics, gpu_metrics)
        
        return {
            "health_score": analysis.health_score,
            "overall_health": analysis.overall_health,
            "primary_bottleneck": analysis.primary_bottleneck.value
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get health score: {str(e)}"
        )
```

---

### Step 4: Update Main Application (2 minutes)

#### 4.1 Update src/main.py

Add analysis router:

```python
# Add import
from src.api import health, gpu, system, analysis

# Include router
app.include_router(analysis.router)
```

---

### Step 5: Testing (5 minutes)

#### 5.1 Create tests/test_analyzer.py

```python
"""
Analyzer Tests

Tests for resource analysis engine.
"""

import pytest
from src.analysis.analyzer import ResourceAnalyzer
from src.collectors.system_collector import SystemCollector
from src.collectors.gpu_collector import GPUCollector
from src.config import settings


def test_analyzer_initialization():
    """Test analyzer initialization."""
    analyzer = ResourceAnalyzer()
    assert analyzer is not None


def test_analyze_system_metrics():
    """Test analyzing system metrics."""
    # Collect real metrics
    system_collector = SystemCollector()
    system_metrics = system_collector.collect(instance_id="test")
    
    # Analyze
    analyzer = ResourceAnalyzer()
    result = analyzer.analyze(system_metrics)
    
    assert result is not None
    assert result.instance_id == "test"
    assert result.primary_bottleneck is not None
    assert result.overall_health in ["healthy", "degraded", "critical"]
    assert 0 <= result.health_score <= 100
    assert result.efficiency is not None


def test_analyze_with_gpu_metrics():
    """Test analyzing with GPU metrics."""
    system_collector = SystemCollector()
    system_metrics = system_collector.collect(instance_id="test")
    
    gpu_metrics = None
    with GPUCollector() as gpu_collector:
        if gpu_collector.is_available():
            gpu_metrics = gpu_collector.collect(instance_id="test")
    
    analyzer = ResourceAnalyzer()
    result = analyzer.analyze(system_metrics, gpu_metrics)
    
    assert result is not None
    assert len(result.utilization_summary) >= 2  # At least CPU and memory


def test_utilization_levels():
    """Test utilization level classification."""
    analyzer = ResourceAnalyzer()
    
    from src.models.analysis import UtilizationLevel
    
    assert analyzer._get_utilization_level(10) == UtilizationLevel.IDLE
    assert analyzer._get_utilization_level(30) == UtilizationLevel.LOW
    assert analyzer._get_utilization_level(60) == UtilizationLevel.MODERATE
    assert analyzer._get_utilization_level(80) == UtilizationLevel.HIGH
    assert analyzer._get_utilization_level(95) == UtilizationLevel.CRITICAL


def test_efficiency_scores():
    """Test efficiency score calculation."""
    system_collector = SystemCollector()
    system_metrics = system_collector.collect(instance_id="test")
    
    analyzer = ResourceAnalyzer()
    result = analyzer.analyze(system_metrics)
    
    assert 0 <= result.efficiency.overall_score <= 100
    assert 0 <= result.efficiency.cpu_efficiency <= 100
    assert 0 <= result.efficiency.memory_efficiency <= 100
```

#### 5.2 Create tests/test_analysis_api.py

```python
"""
Analysis API Tests

Tests for analysis API endpoints.
"""

import pytest
from fastapi import status


def test_get_analysis(client):
    """Test analysis endpoint."""
    response = client.get("/analysis/")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "primary_bottleneck" in data
    assert "overall_health" in data
    assert "health_score" in data
    assert "efficiency" in data
    assert "recommendations" in data


def test_get_health_score(client):
    """Test health score endpoint."""
    response = client.get("/analysis/health-score")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "health_score" in data
    assert "overall_health" in data
    assert "primary_bottleneck" in data
    assert 0 <= data["health_score"] <= 100
```

---

## Expected Outcomes

After completing this phase:

1. ✅ **Bottleneck Detection**
   - CPU, GPU, memory bottleneck detection
   - Severity classification
   - Threshold-based alerts

2. ✅ **Utilization Analysis**
   - Resource utilization levels
   - Utilization patterns
   - Imbalance detection

3. ✅ **Efficiency Scoring**
   - Overall efficiency score
   - Per-resource efficiency
   - Power efficiency (GPU)

4. ✅ **Recommendations**
   - Actionable optimization recommendations
   - Priority-based suggestions
   - Impact assessment

5. ✅ **API Endpoints**
   - `GET /analysis/` - Complete analysis
   - `GET /analysis/health-score` - Health score only

---

## Success Criteria

- [ ] Analyzer initializes successfully
- [ ] Bottleneck detection works
- [ ] Efficiency scores calculated
- [ ] Recommendations generated
- [ ] API endpoints return valid data
- [ ] Tests pass (8+ tests)
- [ ] Documentation complete

---

## Next Steps

After Analysis Engine is complete:

- **PHASE3-3.5**: KVOptkit Integration (KV cache optimization)
- **PHASE3-3.6**: LangGraph Workflow (orchestration)

---

**Ready to implement intelligent resource analysis!** 🚀
