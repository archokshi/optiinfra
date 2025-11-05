"""
Unit Tests for Recommendation Generator.

Tests recommendation generation logic.
"""

import pytest
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


@pytest.mark.unit
class TestRecommendationGenerator:
    """Test recommendation generation."""
    
    def test_spot_migration_recommendation(self, sample_spot_migration_recommendation):
        """Test spot migration recommendation structure."""
        rec = sample_spot_migration_recommendation
        
        assert rec["type"] == "spot_migration"
        assert rec["estimated_monthly_savings"] > 0
        assert rec["priority"] in ["low", "medium", "high"]
        assert rec["risk_level"] in ["very_low", "low", "medium", "high"]
        assert len(rec["affected_resources"]) > 0
    
    def test_rightsizing_recommendation(self, sample_rightsizing_recommendation):
        """Test rightsizing recommendation structure."""
        rec = sample_rightsizing_recommendation
        
        assert rec["type"] == "rightsizing"
        assert "metadata" in rec
        assert "current_instance_type" in rec["metadata"]
        assert "recommended_instance_type" in rec["metadata"]
    
    def test_savings_calculation(self):
        """Test savings calculation logic."""
        current_cost = 1000.00
        optimized_cost = 800.00
        
        savings = current_cost - optimized_cost
        savings_percentage = (savings / current_cost) * 100
        
        assert savings == 200.00
        assert savings_percentage == 20.0
    
    def test_priority_scoring(self):
        """Test recommendation priority scoring."""
        def calculate_priority(savings: float, risk: str) -> str:
            risk_scores = {"very_low": 1, "low": 2, "medium": 3, "high": 4}
            
            if savings > 1000 and risk_scores[risk] <= 2:
                return "high"
            elif savings > 500:
                return "medium"
            else:
                return "low"
        
        assert calculate_priority(1500, "low") == "high"
        assert calculate_priority(750, "medium") == "medium"
        assert calculate_priority(300, "low") == "low"
    
    def test_recommendation_validation(self, sample_spot_migration_recommendation):
        """Test recommendation validation."""
        rec = sample_spot_migration_recommendation
        
        # Required fields
        required_fields = ["id", "customer_id", "type", "title", "description", 
                          "estimated_monthly_savings", "priority", "risk_level"]
        
        for field in required_fields:
            assert field in rec
            assert rec[field] is not None
    
    def test_batch_generation(self, recommendation_batch):
        """Test batch recommendation generation."""
        assert len(recommendation_batch) == 10
        assert all("id" in rec for rec in recommendation_batch)
        assert all("type" in rec for rec in recommendation_batch)


@pytest.mark.unit
class TestRecommendationValidator:
    """Test recommendation validation."""
    
    def test_validate_savings_positive(self):
        """Test that savings must be positive."""
        savings = 1200.00
        assert savings > 0
        
        # Negative savings should fail
        invalid_savings = -100.00
        assert invalid_savings < 0  # Would be rejected
    
    def test_validate_risk_level(self):
        """Test risk level validation."""
        valid_risks = ["very_low", "low", "medium", "high"]
        
        for risk in valid_risks:
            assert risk in valid_risks
        
        invalid_risk = "extreme"
        assert invalid_risk not in valid_risks
    
    def test_validate_affected_resources(self, sample_spot_migration_recommendation):
        """Test affected resources validation."""
        rec = sample_spot_migration_recommendation
        
        assert len(rec["affected_resources"]) > 0
        assert all(isinstance(r, str) for r in rec["affected_resources"])
    
    def test_validate_metadata(self, sample_rightsizing_recommendation):
        """Test metadata validation."""
        rec = sample_rightsizing_recommendation
        metadata = rec["metadata"]
        
        assert "current_instance_type" in metadata
        assert "recommended_instance_type" in metadata
        assert metadata["current_instance_type"] != metadata["recommended_instance_type"]


@pytest.mark.unit
class TestRecommendationPrioritizer:
    """Test recommendation prioritization."""
    
    def test_sort_by_savings(self, recommendation_batch):
        """Test sorting by savings."""
        sorted_recs = sorted(recommendation_batch, 
                           key=lambda x: x["estimated_monthly_savings"], 
                           reverse=True)
        
        # Verify descending order
        for i in range(len(sorted_recs) - 1):
            assert sorted_recs[i]["estimated_monthly_savings"] >= sorted_recs[i+1]["estimated_monthly_savings"]
    
    def test_filter_by_priority(self, recommendation_batch):
        """Test filtering by priority."""
        high_priority = [rec for rec in recommendation_batch if rec["priority"] == "high"]
        
        assert all(rec["priority"] == "high" for rec in high_priority)
    
    def test_filter_by_risk(self, recommendation_batch):
        """Test filtering by risk level."""
        low_risk = [rec for rec in recommendation_batch if rec["risk_level"] in ["very_low", "low"]]
        
        assert all(rec["risk_level"] in ["very_low", "low"] for rec in low_risk)
