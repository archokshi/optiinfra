"""
Optimization Engine Tests

Tests for optimization engine.
"""

import pytest
from src.optimization.engine import OptimizationEngine
from src.models.analysis import AnalysisResult, Bottleneck, BottleneckType, Severity


@pytest.fixture
def engine():
    """Optimization engine fixture."""
    return OptimizationEngine()


@pytest.fixture
def sample_analysis():
    """Sample analysis result with bottlenecks."""
    return AnalysisResult(
        instance_id="test",
        instance_type="vllm",
        bottlenecks=[
            Bottleneck(
                type=BottleneckType.HIGH_LATENCY,
                severity=Severity.HIGH,
                description="High latency",
                metric_name="ttft",
                current_value=0.15,
                threshold_value=0.1,
                recommendation="Reduce latency"
            ),
            Bottleneck(
                type=BottleneckType.QUEUE_BUILDUP,
                severity=Severity.MEDIUM,
                description="Queue buildup",
                metric_name="queue_size",
                current_value=12.0,
                threshold_value=10.0,
                recommendation="Increase batch size"
            )
        ],
        slo_statuses=[],
        overall_health_score=70.0,
        recommendations=[]
    )


@pytest.mark.unit
def test_generate_plan(engine, sample_analysis):
    """Test optimization plan generation."""
    plan = engine.generate_plan(
        sample_analysis,
        current_config={"max_batch_size": 32, "quantization": "none"}
    )
    
    assert plan.instance_id == "test"
    assert plan.instance_type == "vllm"
    assert len(plan.optimizations) > 0
    assert plan.estimated_total_improvement != "No optimizations recommended"


@pytest.mark.unit
def test_prioritization(engine, sample_analysis):
    """Test optimization prioritization."""
    plan = engine.generate_plan(sample_analysis, current_config={})
    
    assert len(plan.priority_order) == len(plan.optimizations)
    # Higher impact optimizations should come first
    if len(plan.optimizations) > 1:
        first_opt = plan.optimizations[0]
        last_opt = plan.optimizations[-1]
        impact_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        assert impact_order[first_opt.expected_impact.value] >= impact_order[last_opt.expected_impact.value]


@pytest.mark.unit
def test_total_improvement_estimation(engine):
    """Test total improvement estimation."""
    # High impact bottlenecks
    high_impact_analysis = AnalysisResult(
        instance_id="test",
        instance_type="vllm",
        bottlenecks=[
            Bottleneck(
                type=BottleneckType.MEMORY_PRESSURE,
                severity=Severity.CRITICAL,
                description="Critical memory",
                metric_name="memory",
                current_value=95.0,
                threshold_value=85.0,
                recommendation="Reduce memory"
            )
        ],
        slo_statuses=[],
        overall_health_score=50.0,
        recommendations=[]
    )
    
    plan = engine.generate_plan(high_impact_analysis, current_config={"quantization": "none"})
    
    assert "50-70%" in plan.estimated_total_improvement or "30-50%" in plan.estimated_total_improvement


@pytest.mark.unit
def test_no_optimizations(engine):
    """Test when no optimizations are needed."""
    perfect_analysis = AnalysisResult(
        instance_id="test",
        instance_type="vllm",
        bottlenecks=[],
        slo_statuses=[],
        overall_health_score=100.0,
        recommendations=[]
    )
    
    plan = engine.generate_plan(perfect_analysis, current_config={})
    
    assert len(plan.optimizations) == 0
    assert plan.estimated_total_improvement == "No optimizations recommended"
