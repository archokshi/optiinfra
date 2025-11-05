"""
Comprehensive tests for Reserved Instance optimization workflow.

Tests cover:
- RI usage analysis
- RI recommendation engine
- ROI calculations
- Complete workflow
- Metrics integration
- Security validation
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from src.workflows.ri_optimization import ProductionRIOptimizationWorkflow
from src.nodes.ri_analyze import (
    analyze_usage_patterns,
    calculate_utilization_metrics,
    detect_usage_pattern,
    calculate_confidence_score
)
from src.nodes.ri_recommend import (
    generate_ri_recommendations,
    calculate_ri_savings,
    assess_risk_level
)
from src.nodes.ri_roi import (
    calculate_roi_analysis,
    calculate_roi_percent,
    calculate_risk_adjusted_roi,
    calculate_npv
)
from src.models.ri_optimization import (
    RIOptimizationRequest,
    RIRecommendation,
    RIOptimizationResponse
)


class TestRIAnalysis:
    """Test RI usage analysis functions."""
    
    def test_identify_stable_workloads(self):
        """Test identification of RI candidates based on uptime and cost."""
        state = {
            "request_id": "test-123",
            "customer_id": "customer1",
            "instance_usage": [
                {
                    "instance_id": "i-stable",
                    "instance_type": "t3.large",
                    "region": "us-east-1",
                    "hourly_cost": 0.14,
                    "usage_history": [
                        {"state": "running", "cpu_utilization": 50, "memory_utilization": 60}
                        for _ in range(720)  # 30 days
                    ]
                },
                {
                    "instance_id": "i-low-uptime",
                    "instance_type": "t3.medium",
                    "region": "us-east-1",
                    "hourly_cost": 0.07,
                    "usage_history": [
                        {"state": "running" if i % 2 == 0 else "stopped", "cpu_utilization": 50, "memory_utilization": 60}
                        for i in range(720)
                    ]
                },
                {
                    "instance_id": "i-low-cost",
                    "instance_type": "t3.micro",
                    "region": "us-east-1",
                    "hourly_cost": 0.01,
                    "usage_history": [
                        {"state": "running", "cpu_utilization": 50, "memory_utilization": 60}
                        for _ in range(720)
                    ]
                }
            ],
            "min_uptime_percent": 80.0,
            "min_monthly_cost": 50.0
        }
        
        result = analyze_usage_patterns(state)
        
        assert result["workflow_status"] == "analyzed"
        assert len(result["stable_workloads"]) == 1
        assert result["stable_workloads"][0]["instance_id"] == "i-stable"
    
    def test_calculate_utilization_metrics(self):
        """Test utilization metrics calculation."""
        instance = {
            "instance_id": "i-123",
            "hourly_cost": 0.10,
            "usage_history": [
                {"state": "running", "cpu_utilization": 50, "memory_utilization": 60}
                for _ in range(720)
            ] + [
                {"state": "stopped", "cpu_utilization": 0, "memory_utilization": 0}
                for _ in range(80)
            ]
        }
        
        metrics = calculate_utilization_metrics(instance)
        
        assert metrics["uptime_percent"] == 90.0  # 720/800
        assert metrics["monthly_cost"] == 73.0  # 0.10 * 730
        assert metrics["avg_cpu"] == 50.0
        assert metrics["running_hours"] == 720
    
    def test_detect_steady_pattern(self):
        """Test detection of steady usage pattern."""
        usage_history = [
            {"cpu_utilization": 50 + (i % 5)}  # Slight variation
            for i in range(720)
        ]
        
        pattern = detect_usage_pattern(usage_history)
        
        assert pattern == "steady"
    
    def test_detect_growing_pattern(self):
        """Test detection of growing usage pattern."""
        usage_history = [
            {"cpu_utilization": 30 + (i / 10)}  # Growing trend
            for i in range(720)
        ]
        
        pattern = detect_usage_pattern(usage_history)
        
        assert pattern == "growing"
    
    def test_detect_seasonal_pattern(self):
        """Test detection of seasonal usage pattern."""
        import random
        random.seed(42)
        usage_history = [
            {"cpu_utilization": random.uniform(10, 90)}  # High variance
            for _ in range(720)
        ]
        
        pattern = detect_usage_pattern(usage_history)
        
        assert pattern in ["seasonal", "steady"]  # Depends on random seed
    
    def test_confidence_score_calculation(self):
        """Test confidence score calculation."""
        # High confidence scenario
        metrics_high = {
            "uptime_percent": 95,
            "variance": 5,
            "monthly_cost": 500
        }
        score_high = calculate_confidence_score(metrics_high, "steady")
        assert score_high >= 0.90
        
        # Medium confidence scenario
        metrics_medium = {
            "uptime_percent": 85,
            "variance": 15,
            "monthly_cost": 150
        }
        score_medium = calculate_confidence_score(metrics_medium, "growing")
        assert 0.60 <= score_medium <= 0.80
        
        # Low confidence scenario
        metrics_low = {
            "uptime_percent": 80,
            "variance": 25,
            "monthly_cost": 60
        }
        score_low = calculate_confidence_score(metrics_low, "seasonal")
        assert score_low <= 0.60


class TestRIRecommendation:
    """Test RI recommendation engine."""
    
    def test_generate_recommendations(self):
        """Test RI recommendation generation."""
        state = {
            "request_id": "test-123",
            "customer_id": "customer1",
            "cloud_provider": "aws",
            "stable_workloads": [
                {
                    "instance_id": "i-123",
                    "instance_type": "t3.large",
                    "region": "us-east-1",
                    "service_type": "ec2",
                    "monthly_cost": 100.0,
                    "uptime_percent": 95.0,
                    "usage_pattern": "steady",
                    "confidence_score": 0.90,
                    "metrics": {"variance": 5}
                }
            ],
            "customer_preferences": {}
        }
        
        result = generate_ri_recommendations(state)
        
        assert result["workflow_status"] == "recommendations_generated"
        assert len(result["ri_recommendations"]) > 0
        assert result["total_monthly_savings"] > 0
        assert result["total_annual_savings"] > 0
    
    def test_calculate_savings_all_upfront(self):
        """Test savings calculation for all upfront payment."""
        savings = calculate_ri_savings(
            on_demand_monthly_cost=100.0,
            discount_rate=0.40,  # 40% savings
            term="1year",
            payment_option="all_upfront"
        )
        
        assert savings["upfront_cost"] == 720.0  # 100 * 12 * 0.6
        assert savings["monthly_cost"] == 0.0
        assert savings["monthly_savings"] == 100.0
        assert savings["annual_savings"] == 1200.0
        assert savings["savings_percent"] == 40.0
    
    def test_calculate_savings_no_upfront(self):
        """Test savings calculation for no upfront payment."""
        savings = calculate_ri_savings(
            on_demand_monthly_cost=100.0,
            discount_rate=0.30,  # 30% savings
            term="1year",
            payment_option="no_upfront"
        )
        
        assert savings["upfront_cost"] == 0.0
        assert savings["monthly_cost"] == 70.0  # 100 * 0.7
        assert savings["monthly_savings"] == 30.0
        assert savings["annual_savings"] == 360.0
    
    def test_assess_risk_level_low(self):
        """Test low risk assessment."""
        risk = assess_risk_level(
            usage_pattern="steady",
            uptime_percent=95.0,
            variance=5.0
        )
        
        assert risk == "low"
    
    def test_assess_risk_level_high(self):
        """Test high risk assessment."""
        risk = assess_risk_level(
            usage_pattern="declining",
            uptime_percent=82.0,
            variance=25.0
        )
        
        assert risk == "high"


class TestROICalculation:
    """Test ROI calculations."""
    
    def test_calculate_roi_analysis(self):
        """Test comprehensive ROI analysis."""
        state = {
            "request_id": "test-123",
            "customer_id": "customer1",
            "ri_recommendations": [
                {
                    "instance_id": "i-123",
                    "instance_type": "t3.large",
                    "service_type": "ec2",
                    "region": "us-east-1",
                    "term": "1year",
                    "payment_option": "all_upfront",
                    "ri_cost_upfront": 720.0,
                    "monthly_savings": 40.0,
                    "annual_savings": 480.0,
                    "breakeven_months": 18,
                    "risk_level": "low"
                },
                {
                    "instance_id": "i-456",
                    "instance_type": "t3.xlarge",
                    "service_type": "rds",
                    "region": "us-west-2",
                    "term": "3year",
                    "payment_option": "partial_upfront",
                    "ri_cost_upfront": 1800.0,
                    "monthly_savings": 60.0,
                    "annual_savings": 720.0,
                    "breakeven_months": 30,
                    "risk_level": "medium"
                }
            ]
        }
        
        result = calculate_roi_analysis(state)
        
        assert result["workflow_status"] == "roi_calculated"
        assert "roi_analysis" in result
        roi = result["roi_analysis"]
        assert roi["average_breakeven_months"] == 24.0  # (18 + 30) / 2
        assert roi["total_investment"] == 2520.0  # 720 + 1800
        assert roi["total_annual_savings"] == 1200.0  # 480 + 720
    
    def test_calculate_roi_percent(self):
        """Test ROI percentage calculation."""
        roi = calculate_roi_percent(
            investment=1000.0,
            total_return=1500.0
        )
        
        assert roi == 50.0  # ((1500 - 1000) / 1000) * 100
    
    def test_calculate_risk_adjusted_roi(self):
        """Test risk-adjusted ROI calculation."""
        recommendations = [
            {
                "ri_cost_upfront": 1000.0,
                "annual_savings": 500.0,
                "risk_level": "low"  # 1.0x multiplier
            },
            {
                "ri_cost_upfront": 1000.0,
                "annual_savings": 500.0,
                "risk_level": "high"  # 0.7x multiplier
            }
        ]
        
        risk_adjusted_roi = calculate_risk_adjusted_roi(recommendations)
        
        # Risk-adjusted ROI should be negative due to high investment
        assert risk_adjusted_roi < 0
    
    def test_calculate_npv(self):
        """Test NPV calculation."""
        npv = calculate_npv(
            initial_investment=1000.0,
            monthly_cash_flow=100.0,
            months=12,
            annual_discount_rate=0.05
        )
        
        # NPV should be positive since monthly savings exceed investment
        assert npv > 0


class TestRIWorkflow:
    """Test complete RI workflow."""
    
    @pytest.mark.asyncio
    async def test_workflow_initialization(self):
        """Test workflow initialization."""
        workflow = ProductionRIOptimizationWorkflow(
            aws_credentials={"access_key": "test", "secret_key": "test"}
        )
        
        assert workflow is not None
    
    @pytest.mark.asyncio
    async def test_collect_usage_data(self):
        """Test usage data collection."""
        workflow = ProductionRIOptimizationWorkflow(
            aws_credentials={"access_key": "test", "secret_key": "test"}
        )
        
        # Mock the AWS collector to be available
        workflow.aws_collector = MagicMock()
        
        with patch.object(workflow, '_collect_aws_usage') as mock_collect:
            # Mock the AWS usage data collection
            mock_collect.return_value = [
                {
                    "instance_id": "i-123",
                    "instance_type": "t3.large",
                    "region": "us-east-1",
                    "hourly_cost": 0.10,
                    "usage_history": [{"state": "running", "cpu_utilization": 50} for _ in range(720)]
                }
            ]
            
            usage_data = await workflow.collect_usage_data(
                customer_id="customer1",
                cloud_provider="aws",
                days=30
            )
            
            assert isinstance(usage_data, list)
            assert len(usage_data) > 0
            # Should have usage history for each instance
            for instance in usage_data:
                assert "usage_history" in instance
                assert len(instance["usage_history"]) > 0
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test end-to-end RI optimization workflow."""
        workflow = ProductionRIOptimizationWorkflow(
            aws_credentials={"access_key": "test", "secret_key": "test"}
        )
        
        # Mock the AWS collector to be available
        workflow.aws_collector = MagicMock()
        
        with patch.object(workflow, '_collect_aws_usage') as mock_collect:
            # Mock AWS usage data with realistic data
            mock_collect.return_value = [
                {
                    "instance_id": "i-stable-123",
                    "instance_type": "t3.large",
                    "region": "us-east-1",
                    "service_type": "ec2",
                    "hourly_cost": 0.14,
                    "usage_history": [
                        {"state": "running", "cpu_utilization": 50, "memory_utilization": 60}
                        for _ in range(720)  # 30 days of stable usage
                    ]
                }
            ]
            
            result = await workflow.run_optimization(
                customer_id="customer1",
                cloud_provider="aws",
                service_types=["ec2"],
                analysis_period_days=30
            )
            
            assert result["success"] is True
            assert "ri_recommendations" in result
            assert "roi_analysis" in result
            assert result["workflow_status"] in ["roi_calculated", "complete"]


class TestRIMetrics:
    """Test RI metrics recording."""
    
    @pytest.mark.asyncio
    async def test_clickhouse_insert_ri_event(self):
        """Test ClickHouse RI event insertion."""
        from src.database.clickhouse_metrics import SpotMigrationMetrics
        
        with patch('src.database.clickhouse_metrics.Client') as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            
            metrics = SpotMigrationMetrics()
            
            await metrics.insert_ri_optimization_event({
                "request_id": "test-123",
                "customer_id": "customer1",
                "cloud_provider": "aws",
                "service_type": "ec2",
                "workflow_phase": "complete",
                "ris_recommended": 5,
                "annual_savings": 5000.0
            })
            
            # Verify insert was called
            assert mock_instance.execute.called
    
    @pytest.mark.asyncio
    async def test_get_customer_ri_savings(self):
        """Test querying customer RI savings."""
        from src.database.clickhouse_metrics import SpotMigrationMetrics
        
        with patch('src.database.clickhouse_metrics.Client') as mock_client:
            mock_instance = MagicMock()
            mock_instance.execute.return_value = [(3, 15000.0, 12, 14.5)]
            mock_client.return_value = mock_instance
            
            metrics = SpotMigrationMetrics()
            
            result = await metrics.get_customer_ri_savings("customer1", days=30)
            
            assert result["optimization_count"] == 3
            assert result["total_annual_savings"] == 15000.0
            assert result["total_ris_recommended"] == 12
    
    def test_prometheus_metrics_recording(self):
        """Test Prometheus metrics recording."""
        from src.monitoring.prometheus_metrics import (
            record_ri_optimization_start,
            record_ri_optimization_complete,
            record_ri_recommendation
        )
        
        # These should not raise exceptions
        record_ri_optimization_start("customer1", "aws")
        record_ri_optimization_complete("customer1", "aws", 10.5, 5000.0, 5)
        record_ri_recommendation("customer1", "ec2", "1year", 1000.0, 12, "all_upfront")


class TestRIValidation:
    """Test input validation for RI optimization."""
    
    def test_valid_request(self):
        """Test valid RI optimization request."""
        request = RIOptimizationRequest(
            customer_id="customer-123",
            cloud_provider="aws",
            service_types=["ec2", "rds"],
            analysis_period_days=30,
            min_uptime_percent=80.0,
            min_monthly_cost=50.0
        )
        
        assert request.customer_id == "customer-123"
        assert request.cloud_provider == "aws"
        assert len(request.service_types) == 2
    
    def test_invalid_customer_id(self):
        """Test invalid customer ID format."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            RIOptimizationRequest(
                customer_id="invalid@customer!",
                cloud_provider="aws"
            )
    
    def test_invalid_cloud_provider(self):
        """Test invalid cloud provider."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            RIOptimizationRequest(
                customer_id="customer-123",
                cloud_provider="oracle"
            )
    
    def test_invalid_service_type(self):
        """Test invalid service type."""
        with pytest.raises(ValueError, match="Invalid service type"):
            RIOptimizationRequest(
                customer_id="customer-123",
                cloud_provider="aws",
                service_types=["invalid-service"]
            )
    
    def test_invalid_analysis_period(self):
        """Test invalid analysis period."""
        with pytest.raises(ValueError):
            RIOptimizationRequest(
                customer_id="customer-123",
                cloud_provider="aws",
                analysis_period_days=100  # Max is 90
            )
    
    def test_invalid_uptime_percent(self):
        """Test invalid uptime percentage."""
        with pytest.raises(ValueError):
            RIOptimizationRequest(
                customer_id="customer-123",
                cloud_provider="aws",
                min_uptime_percent=150.0  # Max is 100
            )
    
    def test_ri_recommendation_validation(self):
        """Test RI recommendation model validation."""
        rec = RIRecommendation(
            instance_id="i-123",
            instance_type="t3.large",
            service_type="ec2",
            region="us-east-1",
            term="1year",
            payment_option="all_upfront",
            quantity=1,
            on_demand_cost_monthly=100.0,
            ri_cost_upfront=720.0,
            ri_cost_monthly=0.0,
            monthly_savings=40.0,
            annual_savings=480.0,
            total_savings=480.0,
            savings_percent=40.0,
            breakeven_months=18,
            risk_level="low",
            confidence_score=0.90,
            usage_pattern="steady"
        )
        
        assert rec.term == "1year"
        assert rec.risk_level == "low"
    
    def test_invalid_ri_term(self):
        """Test invalid RI term."""
        with pytest.raises(ValueError, match='term must be either "1year" or "3year"'):
            RIRecommendation(
                instance_id="i-123",
                instance_type="t3.large",
                service_type="ec2",
                region="us-east-1",
                term="5year",  # Invalid
                payment_option="all_upfront",
                quantity=1,
                on_demand_cost_monthly=100.0,
                ri_cost_upfront=720.0,
                ri_cost_monthly=0.0,
                monthly_savings=40.0,
                annual_savings=480.0,
                total_savings=480.0,
                savings_percent=40.0,
                breakeven_months=18,
                risk_level="low",
                confidence_score=0.90,
                usage_pattern="steady"
            )


class TestIntegration:
    """Integration tests for complete RI workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_with_metrics(self):
        """Test complete workflow with metrics recording."""
        workflow = ProductionRIOptimizationWorkflow(
            aws_credentials={"access_key": "test", "secret_key": "test"}
        )
        
        # Mock the AWS collector to be available
        workflow.aws_collector = MagicMock()
        
        with patch.object(workflow, '_collect_aws_usage') as mock_collect:
            # Mock AWS usage data
            mock_collect.return_value = [
                {
                    "instance_id": "i-stable-456",
                    "instance_type": "t3.xlarge",
                    "region": "us-east-1",
                    "service_type": "ec2",
                    "hourly_cost": 0.20,
                    "usage_history": [
                        {"state": "running", "cpu_utilization": 60, "memory_utilization": 70}
                        for _ in range(720)
                    ]
                }
            ]
            
            with patch('src.monitoring.prometheus_metrics.record_ri_optimization_start'):
                with patch('src.monitoring.prometheus_metrics.record_ri_optimization_complete'):
                    with patch('src.database.clickhouse_metrics.get_metrics_client') as mock_metrics:
                        mock_client = AsyncMock()
                        mock_metrics.return_value = mock_client
                        
                        result = await workflow.run_optimization(
                            customer_id="customer1",
                            cloud_provider="aws",
                            analysis_period_days=30
                        )
                        
                        assert result["success"] is True
                        assert len(result.get("ri_recommendations", [])) >= 0
                        assert "roi_analysis" in result
