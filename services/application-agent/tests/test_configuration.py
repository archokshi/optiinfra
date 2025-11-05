"""
Tests for configuration monitoring.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.trackers.config_tracker import config_tracker
from src.analyzers.config_analyzer import config_analyzer
from src.optimizers.config_optimizer import config_optimizer
from src.models.configuration import OptimizationStrategy, OptimizationRequest

client = TestClient(app)


def test_get_current_configuration():
    """Test getting current configuration."""
    response = client.get("/config/current")
    assert response.status_code == 200
    
    data = response.json()
    assert "snapshot_id" in data
    assert "model" in data
    assert data["model"] == "gpt-oss-20b"
    assert "temperature" in data
    assert "max_tokens" in data


def test_get_configuration_history():
    """Test getting configuration history."""
    # Track some configurations first
    config_tracker.track_configuration()
    config_tracker.track_configuration()
    
    response = client.get("/config/history?limit=5")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5


def test_analyze_parameter():
    """Test parameter impact analysis."""
    response = client.post("/config/analyze?parameter=temperature&samples=100")
    assert response.status_code == 200
    
    data = response.json()
    assert data["parameter"] == "temperature"
    assert "quality_correlation" in data
    assert "cost_correlation" in data
    assert "latency_correlation" in data


def test_get_recommendations():
    """Test getting optimization recommendations."""
    response = client.get("/config/recommendations?strategy=balanced")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)


def test_optimize_configuration():
    """Test configuration optimization."""
    request = {
        "strategy": "balanced",
        "constraints": {
            "min_quality": 80,
            "max_cost_per_request": 0.002
        }
    }
    
    response = client.post("/config/optimize", json=request)
    assert response.status_code == 200
    
    data = response.json()
    assert "original_config" in data
    assert "optimized_config" in data
    assert "changes" in data
    assert "expected_improvements" in data


def test_configuration_tracker():
    """Test configuration tracker."""
    # Get current config
    config = config_tracker.get_current_config()
    assert config.model == "gpt-oss-20b"
    
    # Track a change
    change = config_tracker.track_change(
        parameter="temperature",
        old_value=0.7,
        new_value=0.5,
        reason="Test change"
    )
    assert change.parameter == "temperature"
    assert change.new_value == 0.5


def test_configuration_analyzer():
    """Test configuration analyzer."""
    # Analyze temperature impact
    impact = config_analyzer.analyze_parameter_impact("temperature", samples=100)
    assert impact.parameter == "temperature"
    assert -1.0 <= impact.quality_correlation <= 1.0
    
    # Find optimal temperature
    optimal = config_analyzer.find_optimal_temperature(target_quality=85.0)
    assert "optimal_temperature" in optimal
    assert 0.0 <= optimal["optimal_temperature"] <= 1.0


def test_configuration_optimizer():
    """Test configuration optimizer."""
    current_config = config_tracker.get_current_config()
    
    # Test quality optimization
    quality_opt = config_optimizer.optimize_for_quality(current_config)
    assert quality_opt.temperature <= 0.5  # Lower for quality
    
    # Test cost optimization
    cost_opt = config_optimizer.optimize_for_cost(current_config)
    assert cost_opt.max_tokens <= 500  # Lower for cost
    
    # Test balanced optimization
    balanced_opt = config_optimizer.optimize_balanced(current_config)
    assert 0.3 <= balanced_opt.temperature <= 0.7
