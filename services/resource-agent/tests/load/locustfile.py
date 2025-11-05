"""
Locust Load Test for Resource Agent

Run with:
    locust -f locustfile.py --host http://localhost:8003
"""

from locust import HttpUser, task, between
import random


class ResourceAgentUser(HttpUser):
    """Simulates a user interacting with Resource Agent."""
    
    # Wait between 1-3 seconds between tasks
    wait_time = between(1, 3)
    
    @task(10)
    def health_check(self):
        """Health check endpoint (most frequent)."""
        self.client.get("/health/")
    
    @task(5)
    def get_system_metrics(self):
        """Get system metrics."""
        self.client.get("/system/metrics")
    
    @task(3)
    def get_cpu_metrics(self):
        """Get CPU metrics only."""
        self.client.get("/system/metrics/cpu")
    
    @task(3)
    def get_memory_metrics(self):
        """Get memory metrics only."""
        self.client.get("/system/metrics/memory")
    
    @task(2)
    def get_gpu_info(self):
        """Get GPU info (may not be available)."""
        with self.client.get("/gpu/info", catch_response=True) as response:
            if response.status_code in [200, 503]:
                response.success()
    
    @task(4)
    def get_analysis(self):
        """Get resource analysis."""
        self.client.get("/analysis/")
    
    @task(2)
    def get_health_score(self):
        """Get health score."""
        self.client.get("/analysis/health-score")
    
    @task(3)
    def get_lmcache_status(self):
        """Get LMCache status."""
        self.client.get("/lmcache/status")
    
    @task(1)
    def run_optimization(self):
        """Run optimization workflow (least frequent, most expensive)."""
        with self.client.post("/optimize/run", catch_response=True) as response:
            if response.status_code in [200, 500]:
                # 500 is acceptable if LLM not configured
                response.success()
    
    @task(2)
    def detailed_health(self):
        """Get detailed health check."""
        self.client.get("/health/detailed")
    
    def on_start(self):
        """Called when a simulated user starts."""
        # Warm up with a health check
        self.client.get("/health/")


class LightLoadUser(HttpUser):
    """Light load scenario - monitoring only."""
    
    wait_time = between(5, 10)
    
    @task(5)
    def health_check(self):
        self.client.get("/health/")
    
    @task(3)
    def get_system_metrics(self):
        self.client.get("/system/metrics")
    
    @task(2)
    def get_analysis(self):
        self.client.get("/analysis/")


class HeavyLoadUser(HttpUser):
    """Heavy load scenario - intensive operations."""
    
    wait_time = between(0.5, 1.5)
    
    @task(5)
    def get_system_metrics(self):
        self.client.get("/system/metrics")
    
    @task(5)
    def get_analysis(self):
        self.client.get("/analysis/")
    
    @task(3)
    def get_lmcache_status(self):
        self.client.get("/lmcache/status")
    
    @task(2)
    def run_optimization(self):
        with self.client.post("/optimize/run", catch_response=True) as response:
            if response.status_code in [200, 500]:
                response.success()
    
    @task(1)
    def health_check(self):
        self.client.get("/health/")
