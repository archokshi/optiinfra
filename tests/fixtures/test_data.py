"""
Test Data Factories

Factories for creating test customers, infrastructure, and metrics.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random
import uuid


class TestCustomerFactory:
    """Factory for creating test customers."""
    
    def __init__(self, db_session):
        self.db_session = db_session
    
    def create_customer(
        self,
        company_name: str = "Test Company",
        monthly_spend: float = 100000,
        cloud_provider: str = "aws",
        **kwargs
    ) -> Dict[str, Any]:
        """Create a test customer."""
        customer = {
            "id": kwargs.get("id", str(uuid.uuid4())),
            "company_name": company_name,
            "email": kwargs.get("email", f"test-{uuid.uuid4().hex[:8]}@example.com"),
            "monthly_spend": monthly_spend,
            "cloud_provider": cloud_provider,
            "plan": kwargs.get("plan", "pro"),
            "status": kwargs.get("status", "active"),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        
        # In real implementation, this would insert into database
        # For now, return the dict
        return type('Customer', (), customer)
    
    def create_batch(self, count: int = 5) -> List[Dict[str, Any]]:
        """Create multiple test customers."""
        return [
            self.create_customer(
                company_name=f"Test Company {i}",
                monthly_spend=random.randint(50000, 500000)
            )
            for i in range(count)
        ]


class TestInfrastructureFactory:
    """Factory for creating test infrastructure."""
    
    def __init__(self, db_session):
        self.db_session = db_session
    
    def create_infrastructure(
        self,
        customer_id: str,
        instances: List[Dict[str, Any]],
        vllm_deployments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Create test infrastructure for a customer."""
        infrastructure = {
            "customer_id": customer_id,
            "instances": instances,
            "vllm_deployments": vllm_deployments or [],
            "created_at": datetime.now(),
        }
        
        return type('Infrastructure', (), infrastructure)
    
    def create_gpu_instance(
        self,
        instance_id: Optional[str] = None,
        instance_type: str = "p4d.24xlarge",
        gpu_type: str = "A100",
        gpu_count: int = 8,
        pricing: str = "on-demand",
        monthly_cost: float = 30000,
        utilization: float = 0.75
    ) -> Dict[str, Any]:
        """Create a GPU instance configuration."""
        return {
            "instance_id": instance_id or f"i-{uuid.uuid4().hex[:12]}",
            "instance_type": instance_type,
            "region": "us-east-1",
            "pricing": pricing,
            "monthly_cost": monthly_cost,
            "gpu_type": gpu_type,
            "gpu_count": gpu_count,
            "utilization": utilization,
            "status": "running",
        }
    
    def create_vllm_deployment(
        self,
        deployment_id: Optional[str] = None,
        model: str = "meta-llama/Llama-3-70B",
        instance_ids: Optional[List[str]] = None,
        avg_latency_p95: float = 1500,
        requests_per_second: float = 50
    ) -> Dict[str, Any]:
        """Create a vLLM deployment configuration."""
        return {
            "deployment_id": deployment_id or f"vllm-{uuid.uuid4().hex[:8]}",
            "model": model,
            "instance_ids": instance_ids or [],
            "avg_latency_p95": avg_latency_p95,
            "requests_per_second": requests_per_second,
            "status": "healthy",
        }


class MockMetricsFactory:
    """Factory for creating mock metrics data."""
    
    @staticmethod
    def create_cost_metrics(
        customer_id: str,
        days: int = 30,
        base_cost: float = 100000,
        trend: str = "stable"
    ) -> List[Dict[str, Any]]:
        """Create mock cost metrics."""
        metrics = []
        start_date = datetime.now() - timedelta(days=days)
        
        for i in range(days):
            date = start_date + timedelta(days=i)
            
            if trend == "increasing":
                cost = base_cost * (1 + (i / days) * 0.2)
            elif trend == "decreasing":
                cost = base_cost * (1 - (i / days) * 0.2)
            else:  # stable
                cost = base_cost + random.uniform(-5000, 5000)
            
            metrics.append({
                "customer_id": customer_id,
                "metric_type": "daily_cost",
                "value": cost,
                "timestamp": date,
            })
        
        return metrics
    
    @staticmethod
    def create_performance_metrics(
        customer_id: str,
        hours: int = 24,
        base_latency: float = 1500,
        base_throughput: float = 50
    ) -> List[Dict[str, Any]]:
        """Create mock performance metrics."""
        metrics = []
        start_time = datetime.now() - timedelta(hours=hours)
        
        for i in range(hours * 12):  # Every 5 minutes
            timestamp = start_time + timedelta(minutes=i * 5)
            
            metrics.append({
                "customer_id": customer_id,
                "metric_type": "latency_p95",
                "value": base_latency + random.uniform(-200, 200),
                "timestamp": timestamp,
            })
            
            metrics.append({
                "customer_id": customer_id,
                "metric_type": "throughput",
                "value": base_throughput + random.uniform(-10, 10),
                "timestamp": timestamp,
            })
        
        return metrics
    
    @staticmethod
    def create_quality_metrics(
        customer_id: str,
        hours: int = 24,
        base_score: float = 0.95
    ) -> List[Dict[str, Any]]:
        """Create mock quality metrics."""
        metrics = []
        start_time = datetime.now() - timedelta(hours=hours)
        
        for i in range(hours * 4):  # Every 15 minutes
            timestamp = start_time + timedelta(minutes=i * 15)
            
            metrics.append({
                "customer_id": customer_id,
                "metric_type": "quality_score",
                "value": max(0, min(1, base_score + random.uniform(-0.05, 0.05))),
                "timestamp": timestamp,
            })
        
        return metrics


class MockLLMResponses:
    """Mock LLM API responses for testing."""
    
    @staticmethod
    def cost_analysis_response() -> Dict[str, Any]:
        """Mock cost analysis LLM response."""
        return {
            "analysis": "High GPU costs detected. Spot instances recommended.",
            "confidence": 0.92,
            "recommendations": [
                {
                    "type": "spot_migration",
                    "estimated_savings": 18000,
                    "risk_level": "low",
                    "reasoning": "Workload is fault-tolerant and can handle interruptions"
                }
            ]
        }
    
    @staticmethod
    def performance_analysis_response() -> Dict[str, Any]:
        """Mock performance analysis LLM response."""
        return {
            "analysis": "KV cache inefficiency detected. PagedAttention recommended.",
            "confidence": 0.88,
            "recommendations": [
                {
                    "type": "kv_cache_optimization",
                    "estimated_improvement": "2.5x latency reduction",
                    "risk_level": "low",
                    "reasoning": "PagedAttention reduces memory fragmentation"
                }
            ]
        }
    
    @staticmethod
    def quality_analysis_response() -> Dict[str, Any]:
        """Mock quality analysis LLM response."""
        return {
            "analysis": "Quality baseline established. No degradation detected.",
            "confidence": 0.95,
            "baseline_score": 0.96,
            "current_score": 0.95,
            "status": "healthy"
        }


class SampleInfrastructureConfigs:
    """Sample infrastructure configurations for testing."""
    
    @staticmethod
    def small_deployment() -> Dict[str, Any]:
        """Small deployment (2 instances)."""
        return {
            "instances": [
                {
                    "instance_id": "i-small-001",
                    "instance_type": "g5.2xlarge",
                    "gpu_type": "A10G",
                    "gpu_count": 1,
                    "monthly_cost": 1200,
                    "utilization": 0.65
                },
                {
                    "instance_id": "i-small-002",
                    "instance_type": "g5.2xlarge",
                    "gpu_type": "A10G",
                    "gpu_count": 1,
                    "monthly_cost": 1200,
                    "utilization": 0.70
                }
            ],
            "total_monthly_cost": 2400
        }
    
    @staticmethod
    def medium_deployment() -> Dict[str, Any]:
        """Medium deployment (6 instances)."""
        return {
            "instances": [
                {
                    "instance_id": f"i-medium-{i:03d}",
                    "instance_type": "p4d.24xlarge",
                    "gpu_type": "A100",
                    "gpu_count": 8,
                    "monthly_cost": 30000,
                    "utilization": random.uniform(0.70, 0.85)
                }
                for i in range(1, 7)
            ],
            "total_monthly_cost": 180000
        }
    
    @staticmethod
    def large_deployment() -> Dict[str, Any]:
        """Large deployment (20+ instances)."""
        instances = []
        
        # 10 p4d.24xlarge instances
        for i in range(1, 11):
            instances.append({
                "instance_id": f"i-large-p4d-{i:03d}",
                "instance_type": "p4d.24xlarge",
                "gpu_type": "A100",
                "gpu_count": 8,
                "monthly_cost": 30000,
                "utilization": random.uniform(0.75, 0.90)
            })
        
        # 10 p4de.24xlarge instances
        for i in range(1, 11):
            instances.append({
                "instance_id": f"i-large-p4de-{i:03d}",
                "instance_type": "p4de.24xlarge",
                "gpu_type": "A100",
                "gpu_count": 8,
                "monthly_cost": 40000,
                "utilization": random.uniform(0.80, 0.95)
            })
        
        return {
            "instances": instances,
            "total_monthly_cost": 700000
        }
