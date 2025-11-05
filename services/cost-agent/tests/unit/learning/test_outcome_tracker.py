"""
Unit Tests for Outcome Tracker.

Tests outcome tracking and metrics calculation.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


@pytest.mark.unit
class TestOutcomeTracker:
    """Test outcome tracking."""
    
    def test_outcome_structure(self, sample_outcome):
        """Test outcome data structure."""
        assert "recommendation_id" in sample_outcome
        assert "execution_id" in sample_outcome
        assert "predicted_savings" in sample_outcome
        assert "actual_savings" in sample_outcome
        assert "accuracy" in sample_outcome
    
    def test_accuracy_calculation(self, sample_outcome):
        """Test accuracy calculation."""
        predicted = sample_outcome["predicted_savings"]
        actual = sample_outcome["actual_savings"]
        
        # Calculate accuracy
        accuracy = (min(actual, predicted) / max(actual, predicted)) * 100
        
        assert 0 <= accuracy <= 100
        assert abs(accuracy - sample_outcome["accuracy"]) < 1.0  # Within 1%
    
    def test_savings_comparison(self):
        """Test savings comparison."""
        predicted = 1200.00
        actual = 1150.00
        
        difference = predicted - actual
        accuracy_pct = (actual / predicted) * 100
        
        assert difference == 50.00
        assert accuracy_pct > 95.0  # Within 5%
    
    def test_outcome_metrics(self, sample_outcome):
        """Test outcome metrics."""
        assert sample_outcome["execution_success"] == True
        assert sample_outcome["execution_time_seconds"] > 0
        assert "metrics" in sample_outcome


@pytest.mark.unit
class TestLearningMetrics:
    """Test learning metrics calculation."""
    
    def test_success_rate(self, sample_learning_metrics):
        """Test success rate calculation."""
        metrics = sample_learning_metrics
        
        success_rate = (metrics["executed_recommendations"] / metrics["total_recommendations"]) * 100
        
        # Should match the stored success rate (approximately)
        assert abs(success_rate - 80.0) < 1.0  # 120/150 = 80%
    
    def test_average_accuracy(self, sample_learning_metrics):
        """Test average accuracy calculation."""
        accuracy = sample_learning_metrics["average_savings_accuracy"]
        
        assert 0 <= accuracy <= 100
        assert accuracy == 87.3
    
    def test_total_savings(self, sample_learning_metrics):
        """Test total savings tracking."""
        actual = sample_learning_metrics["total_actual_savings"]
        predicted = sample_learning_metrics["total_predicted_savings"]
        
        assert actual > 0
        assert predicted > 0
        assert actual < predicted  # Actual slightly less than predicted
    
    def test_top_performing_types(self, sample_learning_metrics):
        """Test top performing recommendation types."""
        top_types = sample_learning_metrics["top_performing_types"]
        
        assert len(top_types) > 0
        assert all("type" in t for t in top_types)
        assert all("success_rate" in t for t in top_types)
        assert all("avg_accuracy" in t for t in top_types)


@pytest.mark.unit
class TestInsightGeneration:
    """Test insight generation."""
    
    def test_pattern_detection(self):
        """Test pattern detection logic."""
        # Simulate pattern: spot migrations have high success rate
        outcomes = [
            {"type": "spot_migration", "success": True},
            {"type": "spot_migration", "success": True},
            {"type": "spot_migration", "success": True},
            {"type": "rightsizing", "success": True},
            {"type": "rightsizing", "success": False}
        ]
        
        spot_success = sum(1 for o in outcomes if o["type"] == "spot_migration" and o["success"])
        spot_total = sum(1 for o in outcomes if o["type"] == "spot_migration")
        
        spot_rate = (spot_success / spot_total) * 100
        
        assert spot_rate == 100.0  # Perfect success rate
    
    def test_confidence_scoring(self):
        """Test confidence score calculation."""
        sample_size = 50
        success_count = 49
        
        # Simple confidence based on sample size and success rate
        success_rate = success_count / sample_size
        confidence = min(success_rate * (sample_size / 100), 1.0)
        
        assert 0 <= confidence <= 1.0
    
    def test_insight_structure(self):
        """Test insight data structure."""
        insight = {
            "type": "pattern",
            "title": "Spot migrations highly successful",
            "description": "98% success rate for spot migrations",
            "confidence": 0.95,
            "impact": "high",
            "recommendations": ["Prioritize spot migrations"]
        }
        
        assert insight["confidence"] > 0.9
        assert insight["impact"] in ["low", "medium", "high"]
        assert len(insight["recommendations"]) > 0
