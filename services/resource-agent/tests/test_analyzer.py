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
