"""
Tests for Vultr cost collector.
"""

import pytest
from unittest.mock import Mock, patch
import responses

from src.collectors.vultr import (
    VultrClient,
    VultrBillingCollector,
    VultrInstanceCollector,
    VultrCostAnalyzer,
    VultrAPIError,
    collect_vultr_metrics
)


class TestVultrClient:
    """Test Vultr API client"""
    
    @responses.activate
    def test_authentication(self):
        """Test API authentication"""
        responses.add(
            responses.GET,
            "https://api.vultr.com/v2/account",
            json={"account": {"name": "test", "balance": 100}},
            status=200
        )
        
        client = VultrClient(api_key="test_key")
        result = client.get_account_info()
        
        assert result["account"]["name"] == "test"
        assert responses.calls[0].request.headers["Authorization"] == "Bearer test_key"
    
    @responses.activate
    def test_rate_limiting(self):
        """Test rate limiting works"""
        import time
        
        responses.add(
            responses.GET,
            "https://api.vultr.com/v2/account",
            json={"account": {}},
            status=200
        )
        
        client = VultrClient(api_key="test_key", rate_limit_delay=0.1)
        
        start = time.time()
        client.get_account_info()
        client.get_account_info()
        elapsed = time.time() - start
        
        # Should take at least 0.1 seconds due to rate limiting
        assert elapsed >= 0.1
    
    @responses.activate
    def test_pagination(self):
        """Test paginated requests"""
        # First page
        responses.add(
            responses.GET,
            "https://api.vultr.com/v2/instances",
            json={
                "instances": [{"id": "1"}, {"id": "2"}],
                "meta": {"links": {"next": "cursor123"}}
            },
            status=200
        )
        
        # Second page
        responses.add(
            responses.GET,
            "https://api.vultr.com/v2/instances",
            json={
                "instances": [{"id": "3"}],
                "meta": {"links": {"next": None}}
            },
            status=200
        )
        
        client = VultrClient(api_key="test_key")
        instances = client.get_paginated("/instances")
        
        assert len(instances) == 3
        assert instances[0]["id"] == "1"
        assert instances[2]["id"] == "3"
    
    @responses.activate
    def test_error_handling(self):
        """Test API error handling"""
        responses.add(
            responses.GET,
            "https://api.vultr.com/v2/account",
            json={"error": "Invalid API key"},
            status=401
        )
        
        client = VultrClient(api_key="invalid_key")
        
        with pytest.raises(Exception):  # Should raise authentication error
            client.get_account_info()


class TestVultrBillingCollector:
    """Test billing collector"""
    
    def test_collect_account_info(self):
        """Test account info collection"""
        mock_client = Mock()
        mock_client.get_account_info.return_value = {
            "account": {
                "name": "test_account",
                "email": "test@example.com",
                "balance": 150.50,
                "pending_charges": 45.30
            }
        }
        
        collector = VultrBillingCollector(mock_client)
        result = collector.collect_account_info()
        
        assert result["balance"] == 150.50
        assert result["pending_charges"] == 45.30
        assert result["email"] == "test@example.com"
    
    def test_collect_pending_charges(self):
        """Test pending charges collection"""
        mock_client = Mock()
        mock_client.get_pending_charges.return_value = {
            "billing": {
                "pending_charges": 123.45,
                "billing_period_start": "2024-10-01",
                "billing_period_end": "2024-10-31"
            }
        }
        
        collector = VultrBillingCollector(mock_client)
        result = collector.collect_pending_charges()
        
        assert result["pending_charges"] == 123.45
        assert result["currency"] == "USD"
    
    def test_collect_invoices(self):
        """Test invoice collection"""
        from datetime import datetime, timedelta
        
        mock_client = Mock()
        mock_client.list_invoices.return_value = [
            {
                "id": "inv_1",
                "date": datetime.utcnow().isoformat() + "Z",
                "amount": 100.00,
                "description": "October invoice",
                "balance": 0
            },
            {
                "id": "inv_2",
                "date": (datetime.utcnow() - timedelta(days=100)).isoformat() + "Z",
                "amount": 200.00,
                "description": "Old invoice",
                "balance": 0
            }
        ]
        
        collector = VultrBillingCollector(mock_client)
        invoices = collector.collect_invoices()
        
        # Should only get recent invoice (within 90 days)
        assert len(invoices) == 1
        assert invoices[0]["invoice_id"] == "inv_1"
    
    def test_analyze_spending_patterns(self):
        """Test spending pattern analysis"""
        from datetime import datetime, timedelta
        
        invoices = [
            {
                "invoice_id": "inv_1",
                "date": datetime.utcnow().isoformat() + "Z",
                "amount": 150.00
            },
            {
                "invoice_id": "inv_2",
                "date": (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z",
                "amount": 100.00
            }
        ]
        
        collector = VultrBillingCollector(Mock())
        analysis = collector.analyze_spending_patterns(invoices)
        
        assert analysis["total_spend"] == 250.00
        assert analysis["invoice_count"] == 2
        assert analysis["trend"] in ["increasing", "decreasing", "stable"]


class TestVultrInstanceCollector:
    """Test instance collector"""
    
    def test_collect_compute_instances(self):
        """Test compute instance collection"""
        mock_client = Mock()
        mock_client.list_instances.return_value = [
            {
                "id": "inst_1",
                "label": "web-server",
                "hostname": "web1.example.com",
                "plan": "vc2-1c-1gb",
                "region": "ewr",
                "os": "Ubuntu 22.04",
                "status": "active",
                "power_status": "running",
                "vcpu_count": 1,
                "ram": 1024,
                "disk": 25,
                "monthly_cost": 5.00,
                "tags": ["web", "production"],
                "date_created": "2024-10-01T00:00:00Z"
            },
            {
                "id": "inst_2",
                "label": "gpu-server",
                "hostname": "gpu1.example.com",
                "plan": "vhf-8c-32gb-gpu",
                "region": "ewr",
                "os": "Ubuntu 22.04",
                "status": "active",
                "power_status": "running",
                "vcpu_count": 8,
                "ram": 32768,
                "disk": 640,
                "monthly_cost": 90.00,
                "tags": ["ml", "gpu"],
                "date_created": "2024-10-01T00:00:00Z"
            }
        ]
        
        collector = VultrInstanceCollector(mock_client)
        instances = collector.collect_compute_instances()
        
        assert len(instances) == 2
        assert instances[0]["is_gpu"] is False
        assert instances[1]["is_gpu"] is True
        assert instances[0]["monthly_cost"] == 5.00
        assert instances[1]["monthly_cost"] == 90.00
    
    def test_collect_bare_metal_servers(self):
        """Test bare metal server collection"""
        mock_client = Mock()
        mock_client.list_bare_metals.return_value = [
            {
                "id": "bm_1",
                "label": "database-server",
                "plan": "vbm-4c-32gb",
                "region": "ewr",
                "os": "Ubuntu 22.04",
                "status": "active",
                "cpu_count": 4,
                "ram": 32768,
                "disk": 480,
                "monthly_cost": 120.00,
                "tags": ["database"],
                "date_created": "2024-10-01T00:00:00Z"
            }
        ]
        
        collector = VultrInstanceCollector(mock_client)
        servers = collector.collect_bare_metal_servers()
        
        assert len(servers) == 1
        assert servers[0]["server_id"] == "bm_1"
        assert servers[0]["monthly_cost"] == 120.00
    
    def test_analyze_instance_utilization(self):
        """Test instance utilization analysis"""
        instances = [
            {
                "instance_id": "i1",
                "status": "active",
                "power_status": "running",
                "is_gpu": False,
                "monthly_cost": 5.00
            },
            {
                "instance_id": "i2",
                "status": "active",
                "power_status": "stopped",
                "is_gpu": True,
                "monthly_cost": 90.00
            },
            {
                "instance_id": "i3",
                "status": "active",
                "power_status": "running",
                "is_gpu": True,
                "monthly_cost": 90.00
            }
        ]
        
        collector = VultrInstanceCollector(Mock())
        analysis = collector.analyze_instance_utilization(instances)
        
        assert analysis["total_instances"] == 3
        assert analysis["running_instances"] == 3
        assert analysis["gpu_instances"] == 2
        assert analysis["idle_instances"] == 1
        assert analysis["idle_cost"] == 90.00
        assert analysis["total_monthly_cost"] == 185.00


class TestVultrCostAnalyzer:
    """Test cost analyzer"""
    
    def test_analyze_costs(self):
        """Test cost analysis"""
        account_info = {"balance": 100}
        pending_charges = {"pending_charges": 50}
        instances = [
            {
                "instance_id": "i1",
                "is_gpu": False,
                "power_status": "running",
                "monthly_cost": 5
            },
            {
                "instance_id": "i2",
                "is_gpu": True,
                "power_status": "stopped",
                "monthly_cost": 90
            }
        ]
        invoices = []
        
        analyzer = VultrCostAnalyzer()
        analysis = analyzer.analyze_costs(
            account_info, pending_charges, instances, invoices
        )
        
        assert analysis["cloud_provider"] == "vultr"
        assert analysis["instance_count"] == 2
        assert analysis["account_balance"] == 100
        assert analysis["current_monthly_spend"] == 50
        assert analysis["waste_analysis"]["idle_instances"] == 1
        assert analysis["waste_analysis"]["idle_cost"] == 90
        assert len(analysis["recommendations"]) >= 1
        assert analysis["total_estimated_savings"] == 90  # Delete idle GPU
    
    def test_cost_breakdown(self):
        """Test cost breakdown calculation"""
        account_info = {"balance": 100}
        pending_charges = {"pending_charges": 200}
        instances = [
            {"instance_id": "i1", "is_gpu": False, "power_status": "running", "monthly_cost": 50},
            {"instance_id": "i2", "is_gpu": True, "power_status": "running", "monthly_cost": 150}
        ]
        invoices = []
        
        analyzer = VultrCostAnalyzer()
        analysis = analyzer.analyze_costs(
            account_info, pending_charges, instances, invoices
        )
        
        assert analysis["cost_breakdown"]["gpu_cost"] == 150
        assert analysis["cost_breakdown"]["cpu_cost"] == 50
        assert analysis["cost_breakdown"]["gpu_percentage"] == 75.0
    
    def test_compare_with_competitors(self):
        """Test competitor comparison"""
        vultr_costs = {"current_monthly_spend": 100}
        
        analyzer = VultrCostAnalyzer()
        comparison = analyzer.compare_with_competitors(vultr_costs)
        
        assert comparison["vultr_cost"] == 100
        assert comparison["estimated_aws_cost"] == 130  # 30% more
        assert comparison["estimated_gcp_cost"] == 125  # 25% more
        assert comparison["estimated_azure_cost"] == 135  # 35% more
        assert comparison["vultr_savings_vs_aws"] == 30


@pytest.mark.integration
def test_collect_vultr_metrics_integration():
    """
    Integration test for full collection.
    Requires VULTR_API_KEY environment variable.
    """
    import os
    
    api_key = os.getenv("VULTR_API_KEY")
    if not api_key:
        pytest.skip("VULTR_API_KEY not set")
    
    metrics = collect_vultr_metrics(api_key)
    
    assert "account" in metrics
    assert "instances" in metrics
    assert "cost_analysis" in metrics
    assert "collected_at" in metrics
    assert metrics["cost_analysis"]["cloud_provider"] == "vultr"
