# PHASE2-2.5 PART1: Analysis Engine - Code Implementation Plan

**Phase**: PHASE2-2.5  
**Agent**: Performance Agent  
**Objective**: Implement bottleneck detection and SLO monitoring analysis engine  
**Estimated Time**: 30+20m (50 minutes total)  
**Priority**: HIGH  
**Dependencies**: PHASE2-2.4, 2.3, 2.2, 0.2c, 0.3

---

## Overview

This phase implements the Analysis Engine that processes collected metrics to detect bottlenecks and monitor SLOs (Service Level Objectives). The engine analyzes metrics from vLLM, TGI, and SGLang to identify performance issues and track SLO compliance.

---

## Analysis Engine Overview

### What is the Analysis Engine?
The Analysis Engine is the intelligence layer that:
- Analyzes collected metrics from all inference servers
- Detects performance bottlenecks
- Monitors SLO compliance
- Generates actionable insights
- Triggers optimization recommendations

### Key Components

#### 1. Bottleneck Detection
- **High Latency**: TTFT > threshold
- **Low Throughput**: Tokens/sec < threshold
- **Queue Buildup**: Waiting requests > threshold
- **Cache Inefficiency**: Cache hit rate < threshold
- **Memory Pressure**: GPU memory > threshold

#### 2. SLO Monitoring
- **P50 Latency**: 50th percentile response time
- **P95 Latency**: 95th percentile response time
- **P99 Latency**: 99th percentile response time
- **Availability**: Success rate %
- **Throughput**: Requests/tokens per second

#### 3. Analysis Types
- **Real-time Analysis**: Immediate bottleneck detection
- **Trend Analysis**: Historical pattern detection
- **Comparative Analysis**: Cross-instance comparison
- **Predictive Analysis**: Future bottleneck prediction

---

## Implementation Plan

### Step 1: Analysis Models (5 minutes)

#### 1.1 Create src/models/analysis.py

```python
"""
Analysis Models

Models for bottleneck detection and SLO monitoring.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class BottleneckType(str, Enum):
    """Types of bottlenecks."""
    HIGH_LATENCY = "high_latency"
    LOW_THROUGHPUT = "low_throughput"
    QUEUE_BUILDUP = "queue_buildup"
    CACHE_INEFFICIENCY = "cache_inefficiency"
    MEMORY_PRESSURE = "memory_pressure"
    BATCH_SIZE_SUBOPTIMAL = "batch_size_suboptimal"


class Severity(str, Enum):
    """Severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Bottleneck(BaseModel):
    """Detected bottleneck."""
    
    type: BottleneckType
    severity: Severity
    description: str
    metric_name: str
    current_value: float
    threshold_value: float
    recommendation: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SLOTarget(BaseModel):
    """SLO target definition."""
    
    name: str = Field(..., description="SLO name")
    metric: str = Field(..., description="Metric to monitor")
    target_value: float = Field(..., description="Target value")
    comparison: str = Field(..., description="Comparison operator: <, >, <=, >=")
    description: Optional[str] = None


class SLOStatus(BaseModel):
    """SLO compliance status."""
    
    target: SLOTarget
    current_value: float
    is_compliant: bool
    deviation_percent: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AnalysisResult(BaseModel):
    """Complete analysis result."""
    
    instance_id: str
    instance_type: str = Field(..., description="vllm, tgi, or sglang")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    bottlenecks: List[Bottleneck] = Field(default_factory=list)
    slo_statuses: List[SLOStatus] = Field(default_factory=list)
    overall_health_score: float = Field(..., ge=0.0, le=100.0)
    recommendations: List[str] = Field(default_factory=list)


class AnalysisRequest(BaseModel):
    """Request to analyze metrics."""
    
    instance_id: str
    instance_type: str = Field(..., description="vllm, tgi, or sglang")
    slo_targets: Optional[List[SLOTarget]] = None
```

---

### Step 2: Bottleneck Detector (8 minutes)

#### 2.1 Create src/analysis/bottleneck_detector.py

```python
"""
Bottleneck Detector

Detects performance bottlenecks from metrics.
"""

import logging
from typing import List, Optional
from datetime import datetime

from src.models.analysis import Bottleneck, BottleneckType, Severity
from src.models.metrics import (
    VLLMMetricsSnapshot,
    TGIMetricsSnapshot,
    SGLangMetricsSnapshot
)

logger = logging.getLogger(__name__)


class BottleneckDetector:
    """Detects performance bottlenecks."""
    
    # Default thresholds
    DEFAULT_THRESHOLDS = {
        "ttft_seconds": 0.1,  # 100ms
        "tpot_seconds": 0.05,  # 50ms
        "queue_size": 10,
        "cache_hit_rate": 0.7,  # 70%
        "memory_usage_percent": 0.85,  # 85%
        "throughput_tokens_per_second": 100,
    }
    
    def __init__(self, thresholds: Optional[dict] = None):
        """
        Initialize detector.
        
        Args:
            thresholds: Custom threshold values
        """
        self.thresholds = {**self.DEFAULT_THRESHOLDS, **(thresholds or {})}
    
    def detect_vllm_bottlenecks(
        self,
        metrics: VLLMMetricsSnapshot
    ) -> List[Bottleneck]:
        """Detect bottlenecks in vLLM metrics."""
        bottlenecks = []
        
        # Check TTFT
        if metrics.request_metrics.time_to_first_token_seconds > self.thresholds["ttft_seconds"]:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.HIGH_LATENCY,
                severity=self._calculate_severity(
                    metrics.request_metrics.time_to_first_token_seconds,
                    self.thresholds["ttft_seconds"],
                    higher_is_worse=True
                ),
                description="Time to First Token exceeds threshold",
                metric_name="time_to_first_token_seconds",
                current_value=metrics.request_metrics.time_to_first_token_seconds,
                threshold_value=self.thresholds["ttft_seconds"],
                recommendation="Consider reducing batch size or enabling prefix caching"
            ))
        
        # Check TPOT
        if metrics.request_metrics.time_per_output_token_seconds > self.thresholds["tpot_seconds"]:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.HIGH_LATENCY,
                severity=self._calculate_severity(
                    metrics.request_metrics.time_per_output_token_seconds,
                    self.thresholds["tpot_seconds"],
                    higher_is_worse=True
                ),
                description="Time per Output Token exceeds threshold",
                metric_name="time_per_output_token_seconds",
                current_value=metrics.request_metrics.time_per_output_token_seconds,
                threshold_value=self.thresholds["tpot_seconds"],
                recommendation="Check GPU utilization and consider quantization"
            ))
        
        # Check queue size
        if metrics.gpu_metrics.num_requests_waiting > self.thresholds["queue_size"]:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.QUEUE_BUILDUP,
                severity=self._calculate_severity(
                    metrics.gpu_metrics.num_requests_waiting,
                    self.thresholds["queue_size"],
                    higher_is_worse=True
                ),
                description="Request queue is building up",
                metric_name="num_requests_waiting",
                current_value=float(metrics.gpu_metrics.num_requests_waiting),
                threshold_value=float(self.thresholds["queue_size"]),
                recommendation="Scale horizontally or increase batch size"
            ))
        
        # Check cache usage
        if metrics.gpu_metrics.cache_usage_perc > self.thresholds["memory_usage_percent"] * 100:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.MEMORY_PRESSURE,
                severity=Severity.HIGH,
                description="GPU cache usage is high",
                metric_name="cache_usage_perc",
                current_value=metrics.gpu_metrics.cache_usage_perc,
                threshold_value=self.thresholds["memory_usage_percent"] * 100,
                recommendation="Reduce max sequence length or enable KV cache eviction"
            ))
        
        return bottlenecks
    
    def detect_tgi_bottlenecks(
        self,
        metrics: TGIMetricsSnapshot
    ) -> List[Bottleneck]:
        """Detect bottlenecks in TGI metrics."""
        bottlenecks = []
        
        # Check mean time per token
        if metrics.request_metrics.mean_time_per_token_seconds > self.thresholds["tpot_seconds"]:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.HIGH_LATENCY,
                severity=self._calculate_severity(
                    metrics.request_metrics.mean_time_per_token_seconds,
                    self.thresholds["tpot_seconds"],
                    higher_is_worse=True
                ),
                description="Mean time per token exceeds threshold",
                metric_name="mean_time_per_token_seconds",
                current_value=metrics.request_metrics.mean_time_per_token_seconds,
                threshold_value=self.thresholds["tpot_seconds"],
                recommendation="Enable tensor parallelism or use Flash Attention"
            ))
        
        # Check queue size
        if metrics.request_metrics.queue_size > self.thresholds["queue_size"]:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.QUEUE_BUILDUP,
                severity=self._calculate_severity(
                    metrics.request_metrics.queue_size,
                    self.thresholds["queue_size"],
                    higher_is_worse=True
                ),
                description="Request queue is building up",
                metric_name="queue_size",
                current_value=float(metrics.request_metrics.queue_size),
                threshold_value=float(self.thresholds["queue_size"]),
                recommendation="Increase max batch size or scale horizontally"
            ))
        
        # Check batch size efficiency
        if metrics.generation_metrics.batch_current_size < 4:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.BATCH_SIZE_SUBOPTIMAL,
                severity=Severity.MEDIUM,
                description="Batch size is suboptimal",
                metric_name="batch_current_size",
                current_value=float(metrics.generation_metrics.batch_current_size),
                threshold_value=4.0,
                recommendation="Increase max batch size for better GPU utilization"
            ))
        
        return bottlenecks
    
    def detect_sglang_bottlenecks(
        self,
        metrics: SGLangMetricsSnapshot
    ) -> List[Bottleneck]:
        """Detect bottlenecks in SGLang metrics."""
        bottlenecks = []
        
        # Check TTFT
        if metrics.request_metrics.time_to_first_token_seconds > self.thresholds["ttft_seconds"]:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.HIGH_LATENCY,
                severity=self._calculate_severity(
                    metrics.request_metrics.time_to_first_token_seconds,
                    self.thresholds["ttft_seconds"],
                    higher_is_worse=True
                ),
                description="Time to First Token exceeds threshold",
                metric_name="time_to_first_token_seconds",
                current_value=metrics.request_metrics.time_to_first_token_seconds,
                threshold_value=self.thresholds["ttft_seconds"],
                recommendation="Optimize RadixAttention cache configuration"
            ))
        
        # Check cache hit rate
        if metrics.cache_metrics.cache_hit_rate < self.thresholds["cache_hit_rate"]:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.CACHE_INEFFICIENCY,
                severity=self._calculate_severity(
                    metrics.cache_metrics.cache_hit_rate,
                    self.thresholds["cache_hit_rate"],
                    higher_is_worse=False
                ),
                description="Cache hit rate is below threshold",
                metric_name="cache_hit_rate",
                current_value=metrics.cache_metrics.cache_hit_rate,
                threshold_value=self.thresholds["cache_hit_rate"],
                recommendation="Increase RadixAttention cache size or review prompt patterns"
            ))
        
        # Check throughput
        if metrics.system_metrics.throughput_tokens_per_second < self.thresholds["throughput_tokens_per_second"]:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.LOW_THROUGHPUT,
                severity=self._calculate_severity(
                    metrics.system_metrics.throughput_tokens_per_second,
                    self.thresholds["throughput_tokens_per_second"],
                    higher_is_worse=False
                ),
                description="Token throughput is below threshold",
                metric_name="throughput_tokens_per_second",
                current_value=metrics.system_metrics.throughput_tokens_per_second,
                threshold_value=self.thresholds["throughput_tokens_per_second"],
                recommendation="Increase batch size or enable continuous batching"
            ))
        
        # Check queue
        if metrics.system_metrics.num_requests_waiting > self.thresholds["queue_size"]:
            bottlenecks.append(Bottleneck(
                type=BottleneckType.QUEUE_BUILDUP,
                severity=self._calculate_severity(
                    metrics.system_metrics.num_requests_waiting,
                    self.thresholds["queue_size"],
                    higher_is_worse=True
                ),
                description="Request queue is building up",
                metric_name="num_requests_waiting",
                current_value=float(metrics.system_metrics.num_requests_waiting),
                threshold_value=float(self.thresholds["queue_size"]),
                recommendation="Scale horizontally or optimize batch scheduling"
            ))
        
        return bottlenecks
    
    def _calculate_severity(
        self,
        current: float,
        threshold: float,
        higher_is_worse: bool = True
    ) -> Severity:
        """Calculate severity based on deviation from threshold."""
        if higher_is_worse:
            ratio = current / threshold
            if ratio >= 2.0:
                return Severity.CRITICAL
            elif ratio >= 1.5:
                return Severity.HIGH
            elif ratio >= 1.2:
                return Severity.MEDIUM
            else:
                return Severity.LOW
        else:
            ratio = threshold / current if current > 0 else float('inf')
            if ratio >= 2.0:
                return Severity.CRITICAL
            elif ratio >= 1.5:
                return Severity.HIGH
            elif ratio >= 1.2:
                return Severity.MEDIUM
            else:
                return Severity.LOW
```

---

### Step 3: SLO Monitor (7 minutes)

#### 3.1 Create src/analysis/slo_monitor.py

```python
"""
SLO Monitor

Monitors Service Level Objectives compliance.
"""

import logging
from typing import List
from datetime import datetime

from src.models.analysis import SLOTarget, SLOStatus
from src.models.metrics import (
    VLLMMetricsSnapshot,
    TGIMetricsSnapshot,
    SGLangMetricsSnapshot
)

logger = logging.getLogger(__name__)


class SLOMonitor:
    """Monitors SLO compliance."""
    
    def check_slos(
        self,
        metrics: any,
        targets: List[SLOTarget]
    ) -> List[SLOStatus]:
        """
        Check SLO compliance.
        
        Args:
            metrics: Metrics snapshot (vLLM, TGI, or SGLang)
            targets: List of SLO targets
            
        Returns:
            List of SLO statuses
        """
        statuses = []
        
        for target in targets:
            current_value = self._extract_metric_value(metrics, target.metric)
            
            if current_value is None:
                logger.warning(f"Metric {target.metric} not found in snapshot")
                continue
            
            is_compliant = self._check_compliance(
                current_value,
                target.target_value,
                target.comparison
            )
            
            deviation = self._calculate_deviation(
                current_value,
                target.target_value
            )
            
            statuses.append(SLOStatus(
                target=target,
                current_value=current_value,
                is_compliant=is_compliant,
                deviation_percent=deviation
            ))
        
        return statuses
    
    def _extract_metric_value(self, metrics: any, metric_path: str) -> float:
        """Extract metric value from snapshot using dot notation."""
        parts = metric_path.split('.')
        value = metrics
        
        for part in parts:
            if hasattr(value, part):
                value = getattr(value, part)
            else:
                return None
        
        return float(value) if value is not None else None
    
    def _check_compliance(
        self,
        current: float,
        target: float,
        comparison: str
    ) -> bool:
        """Check if current value meets target."""
        if comparison == "<":
            return current < target
        elif comparison == "<=":
            return current <= target
        elif comparison == ">":
            return current > target
        elif comparison == ">=":
            return current >= target
        elif comparison == "==":
            return abs(current - target) < 0.01
        else:
            logger.warning(f"Unknown comparison operator: {comparison}")
            return False
    
    def _calculate_deviation(self, current: float, target: float) -> float:
        """Calculate deviation percentage."""
        if target == 0:
            return 0.0
        return ((current - target) / target) * 100.0
```

---

### Step 4: Analysis Engine (5 minutes)

#### 4.1 Create src/analysis/engine.py

```python
"""
Analysis Engine

Main engine for bottleneck detection and SLO monitoring.
"""

import logging
from typing import List, Optional, Union
from datetime import datetime

from src.models.analysis import AnalysisResult, AnalysisRequest, SLOTarget
from src.models.metrics import (
    VLLMMetricsSnapshot,
    TGIMetricsSnapshot,
    SGLangMetricsSnapshot
)
from src.analysis.bottleneck_detector import BottleneckDetector
from src.analysis.slo_monitor import SLOMonitor

logger = logging.getLogger(__name__)


class AnalysisEngine:
    """Main analysis engine."""
    
    def __init__(self, custom_thresholds: Optional[dict] = None):
        """
        Initialize engine.
        
        Args:
            custom_thresholds: Custom threshold values
        """
        self.bottleneck_detector = BottleneckDetector(custom_thresholds)
        self.slo_monitor = SLOMonitor()
    
    def analyze(
        self,
        metrics: Union[VLLMMetricsSnapshot, TGIMetricsSnapshot, SGLangMetricsSnapshot],
        instance_type: str,
        slo_targets: Optional[List[SLOTarget]] = None
    ) -> AnalysisResult:
        """
        Analyze metrics and generate insights.
        
        Args:
            metrics: Metrics snapshot
            instance_type: Type of instance (vllm, tgi, sglang)
            slo_targets: Optional SLO targets
            
        Returns:
            Analysis result
        """
        logger.info(f"Analyzing metrics for {instance_type} instance {metrics.instance_id}")
        
        # Detect bottlenecks
        if instance_type == "vllm":
            bottlenecks = self.bottleneck_detector.detect_vllm_bottlenecks(metrics)
        elif instance_type == "tgi":
            bottlenecks = self.bottleneck_detector.detect_tgi_bottlenecks(metrics)
        elif instance_type == "sglang":
            bottlenecks = self.bottleneck_detector.detect_sglang_bottlenecks(metrics)
        else:
            raise ValueError(f"Unknown instance type: {instance_type}")
        
        # Check SLOs
        slo_statuses = []
        if slo_targets:
            slo_statuses = self.slo_monitor.check_slos(metrics, slo_targets)
        
        # Calculate health score
        health_score = self._calculate_health_score(bottlenecks, slo_statuses)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(bottlenecks, slo_statuses)
        
        return AnalysisResult(
            instance_id=metrics.instance_id,
            instance_type=instance_type,
            timestamp=datetime.utcnow(),
            bottlenecks=bottlenecks,
            slo_statuses=slo_statuses,
            overall_health_score=health_score,
            recommendations=recommendations
        )
    
    def _calculate_health_score(self, bottlenecks, slo_statuses) -> float:
        """Calculate overall health score (0-100)."""
        score = 100.0
        
        # Deduct points for bottlenecks
        for bottleneck in bottlenecks:
            if bottleneck.severity.value == "critical":
                score -= 25
            elif bottleneck.severity.value == "high":
                score -= 15
            elif bottleneck.severity.value == "medium":
                score -= 10
            else:
                score -= 5
        
        # Deduct points for SLO violations
        if slo_statuses:
            violations = sum(1 for s in slo_statuses if not s.is_compliant)
            score -= (violations / len(slo_statuses)) * 20
        
        return max(0.0, min(100.0, score))
    
    def _generate_recommendations(self, bottlenecks, slo_statuses) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Add bottleneck recommendations
        for bottleneck in bottlenecks:
            if bottleneck.recommendation not in recommendations:
                recommendations.append(bottleneck.recommendation)
        
        # Add SLO-specific recommendations
        for status in slo_statuses:
            if not status.is_compliant:
                rec = f"Address {status.target.name} SLO violation: current {status.current_value:.2f}, target {status.target.target_value:.2f}"
                if rec not in recommendations:
                    recommendations.append(rec)
        
        return recommendations
```

---

### Step 5: API Endpoints (3 minutes)

#### 5.1 Create src/api/analysis.py

```python
"""
Analysis Endpoints

API endpoints for analysis engine.
"""

from fastapi import APIRouter, HTTPException, status
import logging

from src.models.analysis import AnalysisRequest, AnalysisResult
from src.analysis.engine import AnalysisEngine
from src.collectors.vllm_collector import VLLMCollector
from src.collectors.tgi_collector import TGICollector
from src.collectors.sglang_collector import SGLangCollector

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize engine
analysis_engine = AnalysisEngine()


@router.post(
    "/analyze",
    response_model=AnalysisResult,
    status_code=status.HTTP_200_OK,
    tags=["analysis"]
)
async def analyze_instance(request: AnalysisRequest) -> AnalysisResult:
    """
    Analyze instance metrics and detect bottlenecks.
    
    Args:
        request: Analysis request
        
    Returns:
        Analysis result with bottlenecks and SLO status
    """
    try:
        # Collect metrics based on instance type
        if request.instance_type == "vllm":
            async with VLLMCollector() as collector:
                metrics = await collector.collect(
                    instance_id=request.instance_id,
                    endpoint=f"http://{request.instance_id}/metrics"
                )
        elif request.instance_type == "tgi":
            async with TGICollector() as collector:
                metrics = await collector.collect(
                    instance_id=request.instance_id,
                    endpoint=f"http://{request.instance_id}/metrics"
                )
        elif request.instance_type == "sglang":
            async with SGLangCollector() as collector:
                metrics = await collector.collect(
                    instance_id=request.instance_id,
                    endpoint=f"http://{request.instance_id}/metrics"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown instance type: {request.instance_type}"
            )
        
        # Analyze metrics
        result = analysis_engine.analyze(
            metrics=metrics,
            instance_type=request.instance_type,
            slo_targets=request.slo_targets
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )
```

#### 5.2 Update src/main.py

```python
from src.api import health, metrics, analysis

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])
app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])
```

---

### Step 6: Testing (12 minutes)

Tests will be created for:
- Bottleneck detector
- SLO monitor
- Analysis engine
- API endpoints

---

## Success Criteria

### Functional Requirements
- ✅ Bottleneck detection works for all instance types
- ✅ SLO monitoring tracks compliance
- ✅ Health score calculation is accurate
- ✅ Recommendations are actionable
- ✅ API endpoints work correctly

### Non-Functional Requirements
- ✅ Analysis completes in < 1 second
- ✅ Type hints throughout
- ✅ Comprehensive docstrings
- ✅ Tests pass with >80% coverage

---

## Dependencies

### From Previous Phases
- **PHASE2-2.4**: SGLang collector
- **PHASE2-2.3**: TGI collector
- **PHASE2-2.2**: vLLM collector

---

## Next Phase

**PHASE2-2.6**: Optimization Recommendations - Generate optimization strategies

---

**Status**: Ready for implementation  
**Estimated Completion**: 50 minutes  
**Dependencies**: PHASE2-2.4, 2.3, 2.2
