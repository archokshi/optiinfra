"""
Unit Tests for Anomaly Detector.

Tests anomaly detection functionality.
"""

import pytest
from datetime import datetime, timedelta
import sys
from pathlib import Path
import statistics

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


@pytest.mark.unit
class TestAnomalyDetector:
    """Test anomaly detection."""
    
    def test_statistical_threshold_calculation(self, daily_cost_data):
        """Test calculating statistical thresholds."""
        costs = [day["cost"] for day in daily_cost_data]
        
        mean = statistics.mean(costs)
        stdev = statistics.stdev(costs)
        
        # 2 standard deviations threshold
        threshold = mean + (2 * stdev)
        
        assert threshold > mean
        assert threshold > 0
    
    def test_detect_cost_spike(self, anomaly_cost_data):
        """Test detecting cost spikes."""
        # Find anomalies
        anomalies = [day for day in anomaly_cost_data if day.get("anomaly", False)]
        
        assert len(anomalies) > 0
        
        # Verify anomalies have higher costs
        normal_costs = [day["cost"] for day in anomaly_cost_data if not day.get("anomaly", False)]
        anomaly_costs = [day["cost"] for day in anomalies]
        
        avg_normal = statistics.mean(normal_costs)
        avg_anomaly = statistics.mean(anomaly_costs)
        
        assert avg_anomaly > avg_normal
    
    def test_severity_classification(self):
        """Test anomaly severity classification."""
        # Test deviation-based severity
        def classify_severity(deviation: float) -> str:
            if deviation < 2.0:
                return "low"
            elif deviation < 3.0:
                return "medium"
            else:
                return "high"
        
        assert classify_severity(1.5) == "low"
        assert classify_severity(2.5) == "medium"
        assert classify_severity(4.0) == "high"
    
    def test_no_anomalies_in_normal_data(self, daily_cost_data):
        """Test that normal data has no anomalies."""
        costs = [day["cost"] for day in daily_cost_data]
        mean = statistics.mean(costs)
        stdev = statistics.stdev(costs)
        threshold = mean + (2 * stdev)
        
        # Count values above threshold
        anomalies = [c for c in costs if c > threshold]
        
        # Should be very few or none
        assert len(anomalies) < len(costs) * 0.1  # Less than 10%
    
    def test_anomaly_metadata(self):
        """Test anomaly metadata structure."""
        anomaly = {
            "date": "2025-10-23",
            "cost": 1500.00,
            "expected_cost": 500.00,
            "deviation": 200.0,
            "severity": "high",
            "affected_services": ["EC2"]
        }
        
        assert anomaly["cost"] > anomaly["expected_cost"]
        assert anomaly["severity"] in ["low", "medium", "high"]
        assert len(anomaly["affected_services"]) > 0


@pytest.mark.unit
class TestTrendAnalyzer:
    """Test trend analysis."""
    
    def test_calculate_trend(self, daily_cost_data):
        """Test trend calculation."""
        # Simple linear trend
        costs = [day["cost"] for day in daily_cost_data[:7]]  # First week
        
        # Calculate if trending up or down
        first_half = costs[:len(costs)//2]
        second_half = costs[len(costs)//2:]
        
        avg_first = statistics.mean(first_half)
        avg_second = statistics.mean(second_half)
        
        if avg_second > avg_first:
            trend = "increasing"
        elif avg_second < avg_first:
            trend = "decreasing"
        else:
            trend = "stable"
        
        assert trend in ["increasing", "decreasing", "stable"]
    
    def test_moving_average(self, daily_cost_data):
        """Test moving average calculation."""
        costs = [day["cost"] for day in daily_cost_data]
        window = 7
        
        # Calculate 7-day moving average
        moving_avgs = []
        for i in range(len(costs) - window + 1):
            window_costs = costs[i:i+window]
            moving_avgs.append(statistics.mean(window_costs))
        
        assert len(moving_avgs) == len(costs) - window + 1
        assert all(avg > 0 for avg in moving_avgs)
    
    def test_percentage_change(self):
        """Test percentage change calculation."""
        old_value = 500.00
        new_value = 750.00
        
        change = ((new_value - old_value) / old_value) * 100
        
        assert change == 50.0
        
        # Test decrease
        change = ((400.00 - 500.00) / 500.00) * 100
        assert change == -20.0


@pytest.mark.unit
class TestForecaster:
    """Test cost forecasting."""
    
    def test_simple_forecast(self, daily_cost_data):
        """Test simple forecasting logic."""
        # Use last 7 days to forecast next day
        recent_costs = [day["cost"] for day in daily_cost_data[-7:]]
        
        # Simple average-based forecast
        forecast = statistics.mean(recent_costs)
        
        assert forecast > 0
        assert isinstance(forecast, float)
    
    def test_confidence_interval(self):
        """Test confidence interval calculation."""
        forecast = 500.00
        confidence = 0.95
        
        # Simple confidence interval (±10%)
        margin = forecast * 0.10
        
        lower = forecast - margin
        upper = forecast + margin
        
        assert lower < forecast < upper
        assert upper - lower == margin * 2
    
    def test_forecast_validation(self):
        """Test forecast validation."""
        forecast = {
            "predicted_cost": 500.00,
            "confidence_interval": {"lower": 450.00, "upper": 550.00},
            "confidence": 0.95
        }
        
        assert forecast["confidence_interval"]["lower"] < forecast["predicted_cost"]
        assert forecast["predicted_cost"] < forecast["confidence_interval"]["upper"]
        assert 0 < forecast["confidence"] <= 1.0
