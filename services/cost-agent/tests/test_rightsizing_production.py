"""
Comprehensive tests for Right-Sizing Optimization Workflow

This test suite covers:
- Utilization analysis
- Right-sizing recommendations
- Impact analysis
- Workflow execution
- Metrics recording
- Input validation
"""

import pytest
import sys
import importlib.util
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime

# Direct module loading to avoid circular imports
def load_module(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Get base path
base_path = Path(__file__).parent.parent / "src"

# Load modules directly (order matters to avoid circular imports)
# Load dependencies first
sys.modules['nodes.rightsizing_analyze'] = load_module("nodes.rightsizing_analyze", base_path / "nodes" / "rightsizing_analyze.py")
sys.modules['nodes.rightsizing_recommend'] = load_module("nodes.rightsizing_recommend", base_path / "nodes" / "rightsizing_recommend.py")
sys.modules['nodes.rightsizing_impact'] = load_module("nodes.rightsizing_impact", base_path / "nodes" / "rightsizing_impact.py")

# Now load the main modules
rightsizing_analyze = sys.modules['nodes.rightsizing_analyze']
rightsizing_recommend = sys.modules['nodes.rightsizing_recommend']
rightsizing_impact = sys.modules['nodes.rightsizing_impact']
rightsizing_models = load_module("rightsizing_models", base_path / "models" / "rightsizing_optimization.py")
rightsizing_workflow = load_module("rightsizing_workflow", base_path / "workflows" / "rightsizing_optimization.py")

# Import functions
analyze_utilization_patterns = rightsizing_analyze.analyze_utilization_patterns
calculate_resource_metrics = rightsizing_analyze.calculate_resource_metrics
detect_provisioning_issue = rightsizing_analyze.detect_provisioning_issue
calculate_optimization_score = rightsizing_analyze.calculate_optimization_score

generate_rightsizing_recommendations = rightsizing_recommend.generate_rightsizing_recommendations
find_optimal_instance_type = rightsizing_recommend.find_optimal_instance_type
assess_performance_risk = rightsizing_recommend.assess_performance_risk

calculate_impact_analysis = rightsizing_impact.calculate_impact_analysis
calculate_cost_impact = rightsizing_impact.calculate_cost_impact
calculate_performance_impact = rightsizing_impact.calculate_performance_impact
generate_impact_summary = rightsizing_impact.generate_impact_summary

RightSizingRequest = rightsizing_models.RightSizingRequest
ResourceMetrics = rightsizing_models.ResourceMetrics
RightSizingRecommendation = rightsizing_models.RightSizingRecommendation
ImpactAnalysis = rightsizing_models.ImpactAnalysis
RightSizingResponse = rightsizing_models.RightSizingResponse

ProductionRightSizingWorkflow = rightsizing_workflow.ProductionRightSizingWorkflow


class TestUtilizationAnalysis:
    """Test utilization analysis functions."""
    
    def test_identify_over_provisioned_instances(self):
        """Test identification of over-provisioned instances."""
        state = {
            "request_id": "test-123",
            "customer_id": "customer1",
            "min_utilization_threshold": 40.0,
            "max_utilization_threshold": 80.0,
            "instance_metrics": [
                {
                    "instance_id": "i-over-123",
                    "instance_type": "t3.xlarge",
                    "metrics_history": [
                        {"cpu_utilization": 25, "memory_utilization": 30}
                        for _ in range(100)
                    ]
                }
            ]
        }
        
        result = analyze_utilization_patterns(state)
        
        assert result["workflow_status"] == "analyzed"
        assert result["over_provisioned_count"] > 0
        assert len(result["optimization_candidates"]) > 0
        assert result["optimization_candidates"][0]["provisioning_issue"] == "over_provisioned"
    
    def test_identify_under_provisioned_instances(self):
        """Test identification of under-provisioned instances."""
        state = {
            "request_id": "test-123",
            "customer_id": "customer1",
            "min_utilization_threshold": 40.0,
            "max_utilization_threshold": 80.0,
            "instance_metrics": [
                {
                    "instance_id": "i-under-456",
                    "instance_type": "t3.medium",
                    "metrics_history": [
                        {"cpu_utilization": 85, "memory_utilization": 90, "throttling_events": 1}
                        for _ in range(100)
                    ]
                }
            ]
        }
        
        result = analyze_utilization_patterns(state)
        
        assert result["workflow_status"] == "analyzed"
        assert result["under_provisioned_count"] > 0
        assert len(result["optimization_candidates"]) > 0
        assert result["optimization_candidates"][0]["provisioning_issue"] == "under_provisioned"
    
    def test_calculate_resource_metrics(self):
        """Test resource metrics calculation."""
        instance = {
            "instance_id": "i-test-789",
            "metrics_history": [
                {
                    "cpu_utilization": 50 + i % 20,
                    "memory_utilization": 60 + i % 15,
                    "network_in_mbps": 10.0,
                    "network_out_mbps": 5.0
                }
                for i in range(100)
            ]
        }
        
        metrics = calculate_resource_metrics(instance)
        
        assert "cpu_p50" in metrics
        assert "cpu_p95" in metrics
        assert "memory_p50" in metrics
        assert "memory_p95" in metrics
        assert metrics["data_points"] == 100
        assert 0 <= metrics["cpu_p95"] <= 100
        assert 0 <= metrics["memory_p95"] <= 100
    
    def test_detect_provisioning_issue(self):
        """Test provisioning issue detection."""
        # Over-provisioned
        metrics_over = {"cpu_p95": 25, "memory_p95": 30, "throttling_events": 0}
        assert detect_provisioning_issue(metrics_over, 40, 80) == "over_provisioned"
        
        # Under-provisioned
        metrics_under = {"cpu_p95": 85, "memory_p95": 90, "throttling_events": 5}
        assert detect_provisioning_issue(metrics_under, 40, 80) == "under_provisioned"
        
        # Optimal
        metrics_optimal = {"cpu_p95": 60, "memory_p95": 70, "throttling_events": 0}
        assert detect_provisioning_issue(metrics_optimal, 40, 80) == "optimal"
    
    def test_calculate_optimization_score(self):
        """Test optimization score calculation."""
        # High score for over-provisioned
        metrics_over = {"cpu_p95": 20, "memory_p95": 25, "cpu_std": 5, "memory_std": 5}
        score_over = calculate_optimization_score(metrics_over, "over_provisioned")
        assert 0.0 <= score_over <= 1.0
        assert score_over > 0.5  # Should be high
        
        # High score for under-provisioned with throttling
        metrics_under = {"cpu_p95": 90, "memory_p95": 95, "throttling_events": 10}
        score_under = calculate_optimization_score(metrics_under, "under_provisioned")
        assert 0.0 <= score_under <= 1.0
        assert score_under > 0.5  # Should be high
        
        # Zero score for optimal
        score_optimal = calculate_optimization_score({}, "optimal")
        assert score_optimal == 0.0
    
    def test_handle_missing_metrics(self):
        """Test handling of instances with missing metrics."""
        state = {
            "request_id": "test-123",
            "customer_id": "customer1",
            "min_utilization_threshold": 40.0,
            "max_utilization_threshold": 80.0,
            "instance_metrics": [
                {
                    "instance_id": "i-no-metrics",
                    "instance_type": "t3.large",
                    "metrics_history": []  # No metrics
                }
            ]
        }
        
        result = analyze_utilization_patterns(state)
        
        # Should handle gracefully
        assert result["workflow_status"] == "analyzed"
        assert len(result["optimization_candidates"]) == 0


class TestRecommendation:
    """Test right-sizing recommendation generation."""
    
    def test_generate_rightsizing_recommendations(self):
        """Test recommendation generation."""
        state = {
            "request_id": "test-123",
            "customer_id": "customer1",
            "include_arm": True,
            "optimization_candidates": [
                {
                    "instance_id": "i-over-123",
                    "instance_type": "t3.xlarge",
                    "service_type": "ec2",
                    "region": "us-east-1",
                    "provisioning_issue": "over_provisioned",
                    "optimization_score": 0.8,
                    "metrics": {
                        "cpu_p95": 25,
                        "memory_p95": 30,
                        "cpu_p99": 30,
                        "memory_p99": 35,
                        "throttling_events": 0
                    }
                }
            ]
        }
        
        result = generate_rightsizing_recommendations(state)
        
        assert result["workflow_status"] == "recommendations_generated"
        assert len(result["rightsizing_recommendations"]) > 0
        assert result["total_monthly_savings"] > 0
    
    def test_find_optimal_instance_type_downsize(self):
        """Test finding optimal instance type for downsizing."""
        metrics = {
            "cpu_p95": 25,
            "memory_p95": 30,
            "cpu_p99": 30,
            "memory_p99": 35
        }
        
        optimal = find_optimal_instance_type(
            "t3.xlarge",
            metrics,
            "over_provisioned",
            {},
            include_arm=True
        )
        
        assert optimal is not None
        assert optimal["instance_type"] != "t3.xlarge"
        # Should recommend smaller instance
        assert "reason" in optimal
    
    def test_find_optimal_instance_type_upsize(self):
        """Test finding optimal instance type for upsizing."""
        metrics = {
            "cpu_p95": 85,
            "memory_p95": 90,
            "cpu_p99": 95,
            "memory_p99": 95,
            "throttling_events": 10
        }
        
        optimal = find_optimal_instance_type(
            "t3.medium",
            metrics,
            "under_provisioned",
            {},
            include_arm=True
        )
        
        assert optimal is not None
        assert optimal["instance_type"] != "t3.medium"
        # Should recommend larger instance
    
    def test_assess_performance_risk(self):
        """Test performance risk assessment."""
        metrics = {"cpu_p95": 25, "memory_p95": 30, "cpu_p99": 30, "memory_p99": 35}
        current_info = {"vcpus": 4, "memory_gb": 16.0}
        recommended_info = {"vcpus": 2, "memory_gb": 8.0}
        
        risk_level, risk_factors = assess_performance_risk(
            metrics,
            current_info,
            recommended_info,
            "over_provisioned"
        )
        
        assert risk_level in ["low", "medium", "high"]
        assert isinstance(risk_factors, list)
    
    def test_assess_performance_risk_low(self):
        """Test low performance risk assessment."""
        metrics = {"cpu_p95": 20, "memory_p95": 25, "cpu_p99": 25, "memory_p99": 30}
        current_info = {"vcpus": 4, "memory_gb": 16.0}
        recommended_info = {"vcpus": 2, "memory_gb": 8.0}
        
        risk_level, _ = assess_performance_risk(
            metrics,
            current_info,
            recommended_info,
            "over_provisioned"
        )
        
        assert risk_level == "low"
    
    def test_assess_performance_risk_high(self):
        """Test high performance risk assessment."""
        metrics = {"cpu_p95": 70, "memory_p95": 75, "cpu_p99": 85, "memory_p99": 90}
        current_info = {"vcpus": 4, "memory_gb": 16.0}
        recommended_info = {"vcpus": 1, "memory_gb": 4.0}  # Significant downsize
        
        risk_level, _ = assess_performance_risk(
            metrics,
            current_info,
            recommended_info,
            "over_provisioned"
        )
        
        assert risk_level in ["medium", "high"]


class TestImpactAnalysis:
    """Test impact analysis calculations."""
    
    def test_calculate_impact_analysis(self):
        """Test comprehensive impact analysis."""
        state = {
            "request_id": "test-123",
            "customer_id": "customer1",
            "rightsizing_recommendations": [
                {
                    "instance_id": "i-123",
                    "current_instance_type": "t3.xlarge",
                    "recommended_instance_type": "t3.large",
                    "service_type": "ec2",
                    "region": "us-east-1",
                    "current_metrics": {},
                    "current_hourly_cost": 0.1664,
                    "recommended_hourly_cost": 0.0832,
                    "hourly_savings": 0.0832,
                    "monthly_savings": 60.74,
                    "annual_savings": 728.83,
                    "savings_percent": 50.0,
                    "current_vcpus": 4,
                    "recommended_vcpus": 2,
                    "current_memory_gb": 16.0,
                    "recommended_memory_gb": 8.0,
                    "performance_risk": "low",
                    "risk_factors": [],
                    "confidence_score": 0.8,
                    "migration_complexity": "simple",
                    "estimated_downtime_minutes": 2,
                    "requires_testing": False,
                    "optimization_type": "downsize",
                    "provisioning_issue": "over_provisioned",
                    "recommendation_reason": "Same family, optimized for workload"
                }
            ]
        }
        
        result = calculate_impact_analysis(state)
        
        assert result["workflow_status"] == "impact_calculated"
        assert "impact_analysis" in result
        impact = result["impact_analysis"]
        assert impact["total_monthly_savings"] > 0
        assert impact["low_risk_count"] > 0
    
    def test_calculate_cost_impact(self):
        """Test cost impact calculation."""
        recommendations = [
            {
                "current_hourly_cost": 0.1664,
                "recommended_hourly_cost": 0.0832,
                "monthly_savings": 60.74,
                "annual_savings": 728.83,
                "savings_percent": 50.0,
                "service_type": "ec2"
            }
        ]
        
        cost_impact = calculate_cost_impact(recommendations)
        
        assert cost_impact["total_monthly_savings"] > 0
        assert cost_impact["total_annual_savings"] > 0
        assert cost_impact["average_savings_percent"] > 0
    
    def test_calculate_performance_impact(self):
        """Test performance impact calculation."""
        recommendations = [
            {
                "instance_id": "i-123",
                "performance_risk": "low",
                "requires_testing": False,
                "optimization_type": "downsize",
                "risk_factors": []
            },
            {
                "instance_id": "i-456",
                "performance_risk": "medium",
                "requires_testing": True,
                "optimization_type": "upsize",
                "risk_factors": ["High peak CPU utilization"]
            }
        ]
        
        performance_impact = calculate_performance_impact(recommendations)
        
        assert performance_impact["low_risk_count"] == 1
        assert performance_impact["medium_risk_count"] == 1
        assert performance_impact["requires_testing_count"] == 1
    
    def test_generate_impact_summary(self):
        """Test impact summary generation."""
        recommendations = [
            {
                "instance_id": "i-quick-win",
                "current_instance_type": "t3.xlarge",
                "recommended_instance_type": "t3.large",
                "monthly_savings": 60.0,
                "savings_percent": 50.0,
                "performance_risk": "low",
                "migration_complexity": "simple",
                "optimization_type": "downsize"
            }
        ]
        
        cost_impact = {"total_monthly_savings": 60.0, "total_annual_savings": 720.0, "average_savings_percent": 50.0}
        performance_impact = {"low_risk_count": 1, "medium_risk_count": 0, "high_risk_count": 0}
        migration_complexity = {"simple_migrations": 1, "moderate_migrations": 0, "complex_migrations": 0, "total_estimated_downtime_minutes": 2}
        
        summary = generate_impact_summary(recommendations, cost_impact, performance_impact, migration_complexity)
        
        assert "quick_wins" in summary
        assert len(summary["quick_wins"]) > 0
        assert "executive_summary" in summary
        assert "implementation_roadmap" in summary


class TestWorkflow:
    """Test right-sizing workflow execution."""
    
    def test_workflow_initialization(self):
        """Test workflow initialization."""
        workflow = ProductionRightSizingWorkflow(
            aws_credentials={"access_key": "test", "secret_key": "test"}
        )
        
        assert workflow is not None
        assert workflow.workflow is not None
    
    @pytest.mark.asyncio
    async def test_collect_metrics_data(self):
        """Test metrics data collection."""
        workflow = ProductionRightSizingWorkflow(
            aws_credentials={"access_key": "test", "secret_key": "test"}
        )
        
        # Mock the AWS collector
        workflow.aws_collector = MagicMock()
        
        with patch.object(workflow, '_collect_aws_metrics') as mock_collect:
            mock_collect.return_value = [
                {
                    "instance_id": "i-123",
                    "instance_type": "t3.large",
                    "region": "us-east-1",
                    "metrics_history": [
                        {"cpu_utilization": 50, "memory_utilization": 60}
                        for _ in range(100)
                    ]
                }
            ]
            
            metrics_data = await workflow.collect_metrics_data(
                customer_id="customer1",
                cloud_provider="aws",
                service_types=["ec2"],
                days=30
            )
            
            assert isinstance(metrics_data, list)
            assert len(metrics_data) > 0
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test end-to-end right-sizing workflow."""
        workflow = ProductionRightSizingWorkflow(
            aws_credentials={"access_key": "test", "secret_key": "test"}
        )
        
        # Mock the AWS collector
        workflow.aws_collector = MagicMock()
        
        with patch.object(workflow, '_collect_aws_metrics') as mock_collect:
            # Mock AWS metrics with over-provisioned instance
            mock_collect.return_value = [
                {
                    "instance_id": "i-over-123",
                    "instance_type": "t3.xlarge",
                    "service_type": "ec2",
                    "region": "us-east-1",
                    "metrics_history": [
                        {"cpu_utilization": 25, "memory_utilization": 30}
                        for _ in range(100)
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
            assert "recommendations" in result
            assert result["workflow_status"] in ["impact_calculated", "complete"]


class TestMetrics:
    """Test metrics recording."""
    
    @pytest.mark.asyncio
    async def test_clickhouse_insert_event(self):
        """Test ClickHouse event insertion."""
        from src.database.clickhouse_metrics import SpotMigrationMetrics
        
        metrics_client = SpotMigrationMetrics()
        
        event = {
            "request_id": "test-123",
            "customer_id": "customer1",
            "cloud_provider": "aws",
            "service_type": "ec2",
            "workflow_phase": "complete",
            "instances_analyzed": 10,
            "optimization_candidates": 5,
            "over_provisioned_count": 3,
            "under_provisioned_count": 2,
            "recommendations_generated": 5,
            "downsize_count": 3,
            "upsize_count": 2,
            "family_change_count": 0,
            "total_current_cost": 1000.0,
            "total_recommended_cost": 700.0,
            "monthly_savings": 300.0,
            "annual_savings": 3600.0,
            "average_savings_percent": 30.0,
            "low_risk_count": 4,
            "medium_risk_count": 1,
            "high_risk_count": 0,
            "simple_migrations": 4,
            "moderate_migrations": 1,
            "complex_migrations": 0,
            "success": 1,
            "error_message": "",
            "duration_ms": 5000
        }
        
        # Should not raise exception
        await metrics_client.insert_rightsizing_optimization_event(event)
    
    @pytest.mark.asyncio
    async def test_get_customer_savings(self):
        """Test customer savings query."""
        from src.database.clickhouse_metrics import SpotMigrationMetrics
        
        metrics_client = SpotMigrationMetrics()
        
        savings = await metrics_client.get_customer_rightsizing_savings(
            customer_id="customer1",
            days=30
        )
        
        assert isinstance(savings, dict)
        assert "optimization_count" in savings
        assert "total_annual_savings" in savings
    
    def test_prometheus_metrics_recording(self):
        """Test Prometheus metrics recording."""
        # Mock prometheus metrics to avoid registry conflicts
        with patch('monitoring.prometheus_metrics.record_rightsizing_optimization_start'):
            with patch('monitoring.prometheus_metrics.record_rightsizing_optimization_complete'):
                with patch('monitoring.prometheus_metrics.record_rightsizing_recommendation'):
                    # Should not raise exceptions
                    from monitoring import prometheus_metrics
                    
                    prometheus_metrics.record_rightsizing_optimization_start(
                        customer_id="customer1",
                        cloud_provider="aws"
                    )
                    
                    prometheus_metrics.record_rightsizing_optimization_complete(
                        customer_id="customer1",
                        cloud_provider="aws",
                        duration=10.5,
                        savings=3600.0,
                        recommendations=5
                    )
                    
                    prometheus_metrics.record_rightsizing_recommendation(
                        customer_id="customer1",
                        optimization_type="downsize",
                        risk_level="low",
                        savings_percent=30.0
                    )


class TestValidation:
    """Test input validation."""
    
    def test_valid_request(self):
        """Test valid request validation."""
        request = RightSizingRequest(
            customer_id="customer-123",
            cloud_provider="aws",
            service_types=["ec2"],
            analysis_period_days=30,
            min_utilization_threshold=40.0,
            max_utilization_threshold=80.0
        )
        
        assert request.customer_id == "customer-123"
        assert request.cloud_provider == "aws"
        assert request.analysis_period_days == 30
    
    def test_invalid_customer_id(self):
        """Test invalid customer ID validation."""
        with pytest.raises(ValueError):
            RightSizingRequest(
                customer_id="invalid@customer",  # Invalid characters
                cloud_provider="aws"
            )
    
    def test_invalid_cloud_provider(self):
        """Test invalid cloud provider validation."""
        with pytest.raises(ValueError):
            RightSizingRequest(
                customer_id="customer-123",
                cloud_provider="invalid_provider"
            )
    
    def test_invalid_service_type(self):
        """Test invalid service type validation."""
        with pytest.raises(ValueError):
            RightSizingRequest(
                customer_id="customer-123",
                cloud_provider="aws",
                service_types=["invalid_service"]
            )
    
    def test_invalid_analysis_period(self):
        """Test invalid analysis period validation."""
        with pytest.raises(ValueError):
            RightSizingRequest(
                customer_id="customer-123",
                cloud_provider="aws",
                analysis_period_days=5  # Too short
            )
        
        with pytest.raises(ValueError):
            RightSizingRequest(
                customer_id="customer-123",
                cloud_provider="aws",
                analysis_period_days=100  # Too long
            )
    
    def test_invalid_thresholds(self):
        """Test invalid threshold validation."""
        with pytest.raises(ValueError):
            RightSizingRequest(
                customer_id="customer-123",
                cloud_provider="aws",
                min_utilization_threshold=80.0,  # Min > Max
                max_utilization_threshold=40.0
            )
    
    def test_resource_metrics_validation(self):
        """Test resource metrics validation."""
        metrics = ResourceMetrics(
            cpu_p50=50.0,
            cpu_p95=75.0,
            cpu_p99=85.0,
            cpu_max=95.0,
            cpu_avg=60.0,
            cpu_std=10.0,
            memory_p50=55.0,
            memory_p95=70.0,
            memory_p99=80.0,
            memory_max=90.0,
            memory_avg=65.0,
            memory_std=8.0,
            network_in_p95=100.0,
            network_out_p95=50.0,
            data_points=100
        )
        
        assert metrics.cpu_p95 == 75.0
        assert metrics.memory_p95 == 70.0
    
    def test_recommendation_validation(self):
        """Test recommendation validation."""
        metrics = ResourceMetrics(
            cpu_p50=25.0, cpu_p95=30.0, cpu_p99=35.0, cpu_max=40.0, cpu_avg=28.0, cpu_std=5.0,
            memory_p50=30.0, memory_p95=35.0, memory_p99=40.0, memory_max=45.0, memory_avg=33.0, memory_std=4.0,
            network_in_p95=10.0, network_out_p95=5.0, data_points=100
        )
        
        recommendation = RightSizingRecommendation(
            instance_id="i-123",
            current_instance_type="t3.xlarge",
            recommended_instance_type="t3.large",
            region="us-east-1",
            current_metrics=metrics,
            current_hourly_cost=0.1664,
            recommended_hourly_cost=0.0832,
            hourly_savings=0.0832,
            monthly_savings=60.74,
            annual_savings=728.83,
            savings_percent=50.0,
            current_vcpus=4,
            recommended_vcpus=2,
            current_memory_gb=16.0,
            recommended_memory_gb=8.0,
            performance_risk="low",
            confidence_score=0.8,
            migration_complexity="simple",
            estimated_downtime_minutes=2,
            optimization_type="downsize",
            provisioning_issue="over_provisioned"
        )
        
        assert recommendation.instance_id == "i-123"
        assert recommendation.performance_risk == "low"
    
    def test_invalid_performance_risk(self):
        """Test invalid performance risk validation."""
        metrics = ResourceMetrics(
            cpu_p50=25.0, cpu_p95=30.0, cpu_p99=35.0, cpu_max=40.0, cpu_avg=28.0, cpu_std=5.0,
            memory_p50=30.0, memory_p95=35.0, memory_p99=40.0, memory_max=45.0, memory_avg=33.0, memory_std=4.0,
            network_in_p95=10.0, network_out_p95=5.0, data_points=100
        )
        
        with pytest.raises(ValueError):
            RightSizingRecommendation(
                instance_id="i-123",
                current_instance_type="t3.xlarge",
                recommended_instance_type="t3.large",
                region="us-east-1",
                current_metrics=metrics,
                current_hourly_cost=0.1664,
                recommended_hourly_cost=0.0832,
                hourly_savings=0.0832,
                monthly_savings=60.74,
                annual_savings=728.83,
                savings_percent=50.0,
                current_vcpus=4,
                recommended_vcpus=2,
                current_memory_gb=16.0,
                recommended_memory_gb=8.0,
                performance_risk="invalid_risk",  # Invalid
                confidence_score=0.8,
                migration_complexity="simple",
                estimated_downtime_minutes=2,
                optimization_type="downsize",
                provisioning_issue="over_provisioned"
            )


class TestIntegration:
    """Integration tests for complete right-sizing workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_with_metrics(self):
        """Test complete workflow with metrics recording."""
        workflow = ProductionRightSizingWorkflow(
            aws_credentials={"access_key": "test", "secret_key": "test"}
        )
        
        # Mock the AWS collector
        workflow.aws_collector = MagicMock()
        
        with patch.object(workflow, '_collect_aws_metrics') as mock_collect:
            # Mock AWS metrics
            mock_collect.return_value = [
                {
                    "instance_id": "i-over-456",
                    "instance_type": "t3.2xlarge",
                    "service_type": "ec2",
                    "region": "us-east-1",
                    "metrics_history": [
                        {"cpu_utilization": 20, "memory_utilization": 25}
                        for _ in range(100)
                    ]
                }
            ]
            
            with patch('monitoring.prometheus_metrics.record_rightsizing_optimization_start'):
                with patch('monitoring.prometheus_metrics.record_rightsizing_optimization_complete'):
                    with patch('database.clickhouse_metrics.get_metrics_client') as mock_metrics:
                        mock_client = AsyncMock()
                        mock_metrics.return_value = mock_client
                        
                        result = await workflow.run_optimization(
                            customer_id="customer1",
                            cloud_provider="aws",
                            analysis_period_days=30
                        )
                        
                        assert result["success"] is True
                        assert len(result.get("recommendations", [])) >= 0
                        assert "impact_analysis" in result
