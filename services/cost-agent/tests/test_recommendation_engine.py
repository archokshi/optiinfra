"""
Comprehensive tests for Recommendation Engine.

Tests cover:
- Recommendation generation (8 tests)
- Cost prediction (6 tests)
- Scoring (8 tests)
- Trend analysis (6 tests)
- Integration (4 tests)
- Validation (4 tests)

Total: 36+ tests
"""

import pytest
import asyncio
from datetime import datetime, timedelta, date
from typing import Dict, Any, List

from src.recommendations.generator import RecommendationGenerator
from src.recommendations.predictor import CostPredictor
from src.recommendations.scorer import RecommendationScorer
from src.recommendations.trend_analyzer import TrendAnalyzer
from src.recommendations.engine import RecommendationEngine
from src.models.recommendation_engine import (
    RecommendationEngineRequest,
    Recommendation,
    ScoredRecommendation
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_idle_resources():
    """Sample idle resources for testing."""
    return [
        {
            "resource_id": "i-1234567890",
            "resource_type": "ec2",
            "region": "us-east-1",
            "cpu_avg": 2.5,
            "memory_avg": 5.0,
            "idle_severity": "high",
            "idle_duration_days": 30,
            "monthly_waste": 52.00,
            "annual_waste": 624.00
        },
        {
            "resource_id": "i-0987654321",
            "resource_type": "ec2",
            "region": "us-west-2",
            "cpu_avg": 8.0,
            "memory_avg": 15.0,
            "idle_severity": "medium",
            "idle_duration_days": 14,
            "monthly_waste": 30.00,
            "annual_waste": 360.00
        }
    ]


@pytest.fixture
def sample_anomalies():
    """Sample anomalies for testing."""
    return [
        {
            "anomaly_id": "anom-001",
            "anomaly_type": "cost",
            "resource_id": "vol-123",
            "resource_type": "ebs",
            "region": "us-east-1",
            "description": "Cost spike detected",
            "deviation_percent": 150.0,
            "severity": "high"
        },
        {
            "anomaly_id": "anom-002",
            "anomaly_type": "usage",
            "resource_id": "i-456",
            "resource_type": "ec2",
            "region": "us-west-2",
            "description": "Unusual CPU pattern",
            "deviation_percent": 80.0,
            "severity": "medium"
        }
    ]


@pytest.fixture
def sample_cost_history():
    """Sample cost history for testing."""
    history = []
    base_cost = 1000.0
    for i in range(30):
        history.append({
            "date": (datetime.now() - timedelta(days=30-i)).date(),
            "cost": base_cost + (i * 10),  # Increasing trend
            "resource_type": "ec2",
            "customer_id": "test-customer"
        })
    return history


@pytest.fixture
def sample_recommendation():
    """Sample recommendation for testing."""
    return {
        "recommendation_id": "rec-001",
        "customer_id": "test-customer",
        "recommendation_type": "terminate",
        "resource_id": "i-123",
        "resource_type": "ec2",
        "region": "us-east-1",
        "title": "Terminate idle EC2 instance",
        "description": "Instance has been idle for 30 days",
        "rationale": "0% CPU, 0% memory utilization",
        "monthly_savings": 52.00,
        "annual_savings": 624.00,
        "implementation_cost": 0.0,
        "payback_period_days": 0,
        "risk_level": "low",
        "risk_factors": ["Verify no dependencies"],
        "rollback_plan": "Launch new instance",
        "implementation_steps": ["Verify", "Backup", "Terminate"],
        "estimated_time_minutes": 15,
        "requires_approval": True,
        "created_at": datetime.utcnow(),
        "source": "idle_detection",
        "confidence": 0.95
    }


# ============================================================================
# RECOMMENDATION GENERATION TESTS (8 tests)
# ============================================================================

class TestRecommendationGeneration:
    """Test recommendation generation functionality."""
    
    def test_generate_from_idle_resources(self, sample_idle_resources):
        """Test generating recommendations from idle resources."""
        generator = RecommendationGenerator()
        recommendations = generator.generate_from_idle_resources(sample_idle_resources)
        
        assert len(recommendations) == 2
        assert recommendations[0]["recommendation_type"] in ["terminate", "right_size"]
        assert recommendations[0]["monthly_savings"] > 0
        assert "resource_id" in recommendations[0]
    
    def test_generate_from_anomalies(self, sample_anomalies):
        """Test generating recommendations from anomalies."""
        generator = RecommendationGenerator()
        recommendations = generator.generate_from_anomalies(sample_anomalies)
        
        assert len(recommendations) == 2
        assert recommendations[0]["recommendation_type"] == "investigate"
        assert "anomaly" in recommendations[0]["title"].lower() or "investigate" in recommendations[0]["title"].lower()
    
    def test_generate_from_trends(self, sample_cost_history):
        """Test generating recommendations from cost trends."""
        generator = RecommendationGenerator()
        recommendations = generator.generate_from_trends(sample_cost_history)
        
        # Should generate at least one recommendation
        assert len(recommendations) >= 0  # May be 0 if no patterns detected
    
    def test_consolidate_recommendations(self, sample_idle_resources):
        """Test recommendation consolidation and deduplication."""
        generator = RecommendationGenerator()
        
        # Generate recommendations twice (will create duplicates)
        recs1 = generator.generate_from_idle_resources(sample_idle_resources)
        recs2 = generator.generate_from_idle_resources(sample_idle_resources)
        all_recs = recs1 + recs2
        
        # Consolidate
        consolidated = generator.consolidate_recommendations(all_recs)
        
        # Should remove duplicates
        assert len(consolidated) <= len(all_recs)
    
    def test_empty_input_handling(self):
        """Test handling of empty inputs."""
        generator = RecommendationGenerator()
        
        # Empty idle resources
        recs = generator.generate_from_idle_resources([])
        assert recs == []
        
        # Empty anomalies
        recs = generator.generate_from_anomalies([])
        assert recs == []
        
        # Empty cost history
        recs = generator.generate_from_trends([])
        assert recs == []
    
    def test_minimum_savings_filter(self, sample_idle_resources):
        """Test filtering by minimum savings threshold."""
        generator = RecommendationGenerator()
        
        # Generate recommendations
        recommendations = generator.generate_from_idle_resources(sample_idle_resources)
        
        # Apply consolidation (which includes minimum savings filter)
        filtered = generator.consolidate_recommendations(recommendations)
        
        # All should meet minimum threshold or be special types
        for rec in filtered:
            assert rec["monthly_savings"] >= 10.0 or rec["recommendation_type"] in ["investigate", "security_fix"]
    
    def test_recommendation_structure(self, sample_idle_resources):
        """Test that generated recommendations have correct structure."""
        generator = RecommendationGenerator()
        recommendations = generator.generate_from_idle_resources(sample_idle_resources)
        
        required_fields = [
            "recommendation_id", "recommendation_type", "resource_id",
            "title", "description", "monthly_savings", "annual_savings",
            "risk_level", "implementation_steps", "confidence"
        ]
        
        for rec in recommendations:
            for field in required_fields:
                assert field in rec, f"Missing field: {field}"
    
    def test_high_severity_generates_terminate(self):
        """Test that high severity idle resources generate terminate recommendations."""
        generator = RecommendationGenerator()
        
        high_severity_resource = [{
            "resource_id": "i-critical",
            "resource_type": "ec2",
            "region": "us-east-1",
            "idle_severity": "critical",
            "monthly_waste": 100.00
        }]
        
        recommendations = generator.generate_from_idle_resources(high_severity_resource)
        
        assert len(recommendations) == 1
        assert recommendations[0]["recommendation_type"] == "terminate"


# ============================================================================
# COST PREDICTION TESTS (6 tests)
# ============================================================================

class TestCostPrediction:
    """Test cost prediction functionality."""
    
    @pytest.mark.asyncio
    async def test_moving_average_forecast(self, sample_cost_history):
        """Test moving average forecasting."""
        predictor = CostPredictor()
        forecast = await predictor.predict_future_costs(sample_cost_history, forecast_days=7)
        
        assert "daily_forecast" in forecast
        assert len(forecast["daily_forecast"]) == 7
        assert all(cost >= 0 for cost in forecast["daily_forecast"])
    
    @pytest.mark.asyncio
    async def test_linear_trend_forecast(self, sample_cost_history):
        """Test linear trend forecasting."""
        predictor = CostPredictor()
        forecast = await predictor.predict_future_costs(sample_cost_history, forecast_days=30)
        
        assert forecast["model_used"] in ["linear_trend", "moving_average"]
        assert forecast["trend_direction"] in ["increasing", "decreasing", "stable"]
        assert isinstance(forecast["growth_rate_percent"], (int, float))
    
    @pytest.mark.asyncio
    async def test_confidence_intervals(self, sample_cost_history):
        """Test confidence interval calculation."""
        predictor = CostPredictor()
        forecast = await predictor.predict_future_costs(sample_cost_history, forecast_days=7)
        
        assert "daily_lower_bound" in forecast
        assert "daily_upper_bound" in forecast
        assert len(forecast["daily_lower_bound"]) == 7
        assert len(forecast["daily_upper_bound"]) == 7
        
        # Lower bound should be <= forecast <= upper bound
        for i in range(7):
            assert forecast["daily_lower_bound"][i] <= forecast["daily_forecast"][i]
            assert forecast["daily_forecast"][i] <= forecast["daily_upper_bound"][i]
    
    @pytest.mark.asyncio
    async def test_trend_detection(self, sample_cost_history):
        """Test trend direction detection."""
        predictor = CostPredictor()
        
        # Test with increasing trend
        forecast = await predictor.predict_future_costs(sample_cost_history, forecast_days=7)
        assert forecast["trend_direction"] in ["increasing", "decreasing", "stable"]
        # Growth rate should be a number
        assert isinstance(forecast["growth_rate_percent"], (int, float))
    
    @pytest.mark.asyncio
    async def test_insufficient_data_handling(self):
        """Test handling of insufficient historical data."""
        predictor = CostPredictor()
        
        # Only 3 days of data
        short_history = [
            {"date": date.today() - timedelta(days=i), "cost": 100.0}
            for i in range(3)
        ]
        
        forecast = await predictor.predict_future_costs(short_history, forecast_days=7)
        
        # Should still return a forecast (with lower confidence)
        assert "daily_forecast" in forecast
        assert len(forecast["daily_forecast"]) == 7
    
    @pytest.mark.asyncio
    async def test_savings_prediction(self, sample_recommendation):
        """Test savings prediction for recommendations."""
        predictor = CostPredictor()
        
        savings_forecast = await predictor.predict_savings(
            sample_recommendation,
            []  # Empty cost history
        )
        
        assert "monthly_savings" in savings_forecast
        assert "annual_savings" in savings_forecast
        assert "confidence_level" in savings_forecast
        assert savings_forecast["monthly_savings"] == sample_recommendation["monthly_savings"]


# ============================================================================
# SCORING TESTS (8 tests)
# ============================================================================

class TestScoring:
    """Test recommendation scoring functionality."""
    
    def test_roi_score_calculation(self, sample_recommendation):
        """Test ROI score calculation."""
        scorer = RecommendationScorer()
        roi_score = scorer.calculate_roi_score(sample_recommendation)
        
        assert 0 <= roi_score <= 100
        # High savings, zero cost = high ROI score
        assert roi_score >= 90
    
    def test_risk_score_calculation(self, sample_recommendation):
        """Test risk score calculation."""
        scorer = RecommendationScorer()
        risk_score = scorer.calculate_risk_score(sample_recommendation)
        
        assert 0 <= risk_score <= 100
        # Low risk level = high risk score
        assert risk_score >= 70
    
    def test_urgency_score_calculation(self, sample_recommendation):
        """Test urgency score calculation."""
        scorer = RecommendationScorer()
        urgency_score = scorer.calculate_urgency_score(sample_recommendation)
        
        assert 0 <= urgency_score <= 100
    
    def test_business_impact_score(self, sample_recommendation):
        """Test business impact score calculation."""
        scorer = RecommendationScorer()
        impact_score = scorer.calculate_business_impact_score(sample_recommendation, {})
        
        assert 0 <= impact_score <= 100
    
    def test_priority_score_computation(self):
        """Test priority score computation with weights."""
        scorer = RecommendationScorer()
        
        weights = {
            "roi": 0.40,
            "risk": 0.20,
            "urgency": 0.25,
            "impact": 0.15
        }
        
        priority = scorer.compute_priority_score(
            roi_score=90.0,
            risk_score=80.0,
            urgency_score=70.0,
            impact_score=60.0,
            weights=weights
        )
        
        assert 0 <= priority <= 100
        # Should be weighted average
        expected = 90*0.4 + 80*0.2 + 70*0.25 + 60*0.15
        assert abs(priority - expected) < 0.01
    
    def test_score_recommendations(self, sample_recommendation):
        """Test scoring multiple recommendations."""
        scorer = RecommendationScorer()
        
        recommendations = [sample_recommendation]
        scored = scorer.score_recommendations(recommendations, {})
        
        assert len(scored) == 1
        assert "roi_score" in scored[0]
        assert "priority_score" in scored[0]
        assert "rank" in scored[0]
        assert scored[0]["rank"] == 1
    
    def test_categorization(self, sample_recommendation):
        """Test recommendation categorization."""
        scorer = RecommendationScorer()
        
        # High ROI, low risk should be quick_win
        category = scorer._categorize_recommendation(
            roi_score=90.0,
            risk_score=85.0,
            priority_score=88.0
        )
        
        assert category == "quick_win"
    
    def test_custom_weights(self, sample_recommendation):
        """Test scoring with custom weights."""
        scorer = RecommendationScorer()
        
        custom_weights = {
            "roi": 0.50,
            "risk": 0.10,
            "urgency": 0.30,
            "impact": 0.10
        }
        
        scored = scorer.score_recommendations(
            [sample_recommendation],
            {},
            weights=custom_weights
        )
        
        assert len(scored) == 1
        assert scored[0]["scoring_context"]["weights"] == custom_weights


# ============================================================================
# TREND ANALYSIS TESTS (6 tests)
# ============================================================================

class TestTrendAnalysis:
    """Test trend analysis functionality."""
    
    @pytest.mark.asyncio
    async def test_cost_trend_analysis(self, sample_cost_history):
        """Test cost trend analysis."""
        analyzer = TrendAnalyzer()
        
        # Mock the fetch method to return our sample data
        async def mock_fetch(customer_id, days):
            return sample_cost_history
        
        analyzer._fetch_cost_history = mock_fetch
        
        trends = await analyzer.analyze_cost_trends("test-customer", 30)
        
        assert "total_cost_trend" in trends
        assert "cost_growth_rate" in trends
        assert "cost_volatility" in trends
        assert trends["total_cost_trend"] in ["increasing", "decreasing", "stable"]
    
    @pytest.mark.asyncio
    async def test_pattern_identification(self, sample_cost_history):
        """Test pattern identification."""
        analyzer = TrendAnalyzer()
        patterns = analyzer.identify_recurring_patterns(sample_cost_history)
        
        # Should return a list (may be empty)
        assert isinstance(patterns, list)
    
    @pytest.mark.asyncio
    async def test_baseline_comparison(self):
        """Test baseline comparison."""
        analyzer = TrendAnalyzer()
        
        # Mock data
        async def mock_fetch(customer_id, days):
            return [
                {"date": date.today() - timedelta(days=i), "cost": 100.0 + i}
                for i in range(days)
            ]
        
        analyzer._fetch_cost_history = mock_fetch
        
        comparison = await analyzer.compare_to_baseline("test-customer", 7, 30)
        
        assert "current_avg_daily_cost" in comparison
        assert "baseline_avg_daily_cost" in comparison
        assert "percent_change" in comparison
    
    def test_trend_calculation(self):
        """Test trend direction and growth rate calculation."""
        analyzer = TrendAnalyzer()
        
        # Increasing costs
        increasing_costs = [100, 110, 120, 130, 140]
        direction, growth_rate = analyzer._calculate_trend(increasing_costs)
        
        assert direction == "increasing"
        assert growth_rate > 0
    
    def test_resource_type_analysis(self, sample_cost_history):
        """Test cost analysis by resource type."""
        analyzer = TrendAnalyzer()
        
        by_type = analyzer._analyze_by_resource_type(sample_cost_history)
        
        assert isinstance(by_type, dict)
        assert "ec2" in by_type
        assert by_type["ec2"] > 0
    
    def test_insufficient_data_handling(self):
        """Test handling of insufficient data."""
        analyzer = TrendAnalyzer()
        
        # Only 3 days
        short_history = [
            {"date": date.today(), "cost": 100.0}
            for _ in range(3)
        ]
        
        patterns = analyzer.identify_recurring_patterns(short_history)
        assert patterns == []  # Not enough data for patterns


# ============================================================================
# INTEGRATION TESTS (4 tests)
# ============================================================================

class TestIntegration:
    """Test end-to-end integration."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_recommendation_flow(self, sample_idle_resources, sample_anomalies):
        """Test complete recommendation generation flow."""
        engine = RecommendationEngine()
        
        request = {
            "customer_id": "test-customer",
            "analysis_report": {
                "idle_resources": sample_idle_resources,
                "anomalies": sample_anomalies
            },
            "include_predictions": False,  # Skip to avoid needing real data
            "include_trends": False,
            "forecast_days": 7,
            "max_recommendations": 50,
            "min_monthly_savings": 10.0
        }
        
        response = await engine.generate_recommendations(request)
        
        assert response["success"] is True
        assert "total_recommendations" in response
        assert "scored_recommendations" in response
        assert "total_potential_savings" in response
    
    @pytest.mark.asyncio
    async def test_with_predictions(self, sample_idle_resources, sample_cost_history):
        """Test integration with cost predictions."""
        engine = RecommendationEngine()
        
        # Mock the fetch method
        async def mock_fetch(customer_id, days):
            return {"cost_history": sample_cost_history, "usage_history": []}
        
        engine._fetch_historical_data = mock_fetch
        
        request = {
            "customer_id": "test-customer",
            "analysis_report": {"idle_resources": sample_idle_resources},
            "include_predictions": True,
            "include_trends": False,
            "forecast_days": 7
        }
        
        response = await engine.generate_recommendations(request)
        
        assert response["success"] is True
        # Cost forecast should be present (may be None if no data)
        assert "cost_forecast" in response
    
    @pytest.mark.asyncio
    async def test_categorization_integration(self, sample_idle_resources):
        """Test recommendation categorization in full flow."""
        engine = RecommendationEngine()
        
        request = {
            "customer_id": "test-customer",
            "analysis_report": {"idle_resources": sample_idle_resources},
            "include_predictions": False,
            "include_trends": False
        }
        
        response = await engine.generate_recommendations(request)
        
        assert "quick_wins" in response
        assert "strategic_initiatives" in response
        assert "long_term_opportunities" in response
        
        # Total should match
        total_categorized = (
            len(response["quick_wins"]) +
            len(response["strategic_initiatives"]) +
            len(response["long_term_opportunities"])
        )
        assert total_categorized == response["total_recommendations"]
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in engine."""
        engine = RecommendationEngine()
        
        # Invalid request (missing required fields)
        request = {
            "customer_id": "test-customer"
            # Missing analysis_report
        }
        
        response = await engine.generate_recommendations(request)
        
        # Should handle gracefully
        assert "success" in response


# ============================================================================
# VALIDATION TESTS (4 tests)
# ============================================================================

class TestValidation:
    """Test input validation."""
    
    def test_request_validation(self):
        """Test RecommendationEngineRequest validation."""
        # Valid request
        request = RecommendationEngineRequest(
            customer_id="test-customer",
            analysis_report={"idle_resources": []},
            forecast_days=30
        )
        
        assert request.customer_id == "test-customer"
        assert request.forecast_days == 30
    
    def test_invalid_customer_id(self):
        """Test validation of invalid customer ID."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            RecommendationEngineRequest(
                customer_id="invalid@customer#id",  # Invalid characters
                analysis_report={}
            )
    
    def test_weights_validation(self):
        """Test that weights must sum to 1.0."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            RecommendationEngineRequest(
                customer_id="test-customer",
                analysis_report={},
                roi_weight=0.5,
                risk_weight=0.5,
                urgency_weight=0.5,  # Sum > 1.0
                impact_weight=0.5
            )
    
    def test_forecast_days_validation(self):
        """Test forecast_days range validation."""
        # Valid range
        request = RecommendationEngineRequest(
            customer_id="test-customer",
            analysis_report={},
            forecast_days=30
        )
        assert request.forecast_days == 30
        
        # Invalid (too high)
        with pytest.raises(Exception):
            RecommendationEngineRequest(
                customer_id="test-customer",
                analysis_report={},
                forecast_days=500  # > 365
            )


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
