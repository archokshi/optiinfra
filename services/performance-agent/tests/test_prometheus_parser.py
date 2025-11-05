"""
Prometheus Parser Tests

Tests for Prometheus metrics parser.
"""

import pytest
from src.collectors.prometheus_parser import PrometheusParser
from src.models.metrics import MetricType


@pytest.fixture
def parser():
    """Parser fixture."""
    return PrometheusParser()


@pytest.fixture
def sample_metrics():
    """Sample Prometheus metrics."""
    return """
# HELP vllm:request_success_total Total successful requests
# TYPE vllm:request_success_total counter
vllm:request_success_total{model="llama-2-7b"} 150

# HELP vllm:time_to_first_token_seconds Time to first token
# TYPE vllm:time_to_first_token_seconds histogram
vllm:time_to_first_token_seconds{model="llama-2-7b",quantile="0.5"} 0.025
vllm:time_to_first_token_seconds{model="llama-2-7b",quantile="0.95"} 0.050

# HELP vllm:gpu_cache_usage_perc GPU cache usage percentage
# TYPE vllm:gpu_cache_usage_perc gauge
vllm:gpu_cache_usage_perc 75.5
"""


@pytest.mark.unit
def test_parse_metrics(parser, sample_metrics):
    """Test parsing Prometheus metrics."""
    metrics = parser.parse(sample_metrics)
    
    assert len(metrics) == 4
    assert all(m.name.startswith("vllm:") for m in metrics)


@pytest.mark.unit
def test_parse_counter(parser):
    """Test parsing counter metric."""
    text = 'vllm:request_success_total{model="test"} 100'
    metrics = parser.parse(text)
    
    assert len(metrics) == 1
    metric = metrics[0]
    assert metric.name == "vllm:request_success_total"
    assert metric.value == 100
    assert metric.labels == {"model": "test"}


@pytest.mark.unit
def test_parse_gauge(parser):
    """Test parsing gauge metric."""
    text = 'vllm:gpu_cache_usage_perc 75.5'
    metrics = parser.parse(text)
    
    assert len(metrics) == 1
    metric = metrics[0]
    assert metric.name == "vllm:gpu_cache_usage_perc"
    assert metric.value == 75.5
    assert metric.labels == {}


@pytest.mark.unit
def test_filter_by_prefix(parser, sample_metrics):
    """Test filtering metrics by prefix."""
    metrics = parser.parse(sample_metrics)
    filtered = parser.filter_metrics(metrics, prefix="vllm:time")
    
    assert len(filtered) == 2
    assert all(m.name.startswith("vllm:time") for m in filtered)


@pytest.mark.unit
def test_filter_by_labels(parser, sample_metrics):
    """Test filtering metrics by labels."""
    metrics = parser.parse(sample_metrics)
    filtered = parser.filter_metrics(
        metrics,
        labels={"model": "llama-2-7b"}
    )
    
    assert len(filtered) == 3
    assert all(m.labels.get("model") == "llama-2-7b" for m in filtered)
