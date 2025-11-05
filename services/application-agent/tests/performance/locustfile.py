"""
Locust Performance Tests for Application Agent

Run with: locust -f tests/performance/locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between, events
import json
import random
from datetime import datetime


class ApplicationAgentUser(HttpUser):
    """Simulated user for Application Agent."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Setup before tasks."""
        self.model_names = ["model-v1", "model-v2", "model-v3"]
        self.config_hashes = ["v1.0.0", "v2.0.0", "v3.0.0"]
        self.prompts = [
            "What is AI?",
            "Explain machine learning",
            "What is deep learning?",
            "How does NLP work?",
            "What are transformers?"
        ]
        self.responses = [
            "AI is artificial intelligence...",
            "Machine learning is a subset of AI...",
            "Deep learning uses neural networks...",
            "NLP processes natural language...",
            "Transformers are attention-based models..."
        ]
        
        # Create initial baselines for all model/config combinations
        self._create_initial_baselines()
    
    @task(10)
    def analyze_quality(self):
        """Test quality analysis endpoint (highest weight)."""
        payload = {
            "prompt": random.choice(self.prompts),
            "response": random.choice(self.responses),
            "model_id": random.choice(self.model_names)
        }
        
        with self.client.post(
            "/quality/analyze",
            json=payload,
            catch_response=True,
            name="/quality/analyze"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    def _create_initial_baselines(self):
        """Create initial baselines for all model/config combinations."""
        for model_name in self.model_names:
            for config_hash in self.config_hashes:
                payload = {
                    "model_name": model_name,
                    "config_hash": config_hash,
                    "sample_size": 100
                }
                # Create baseline without tracking (setup only)
                self.client.post("/regression/baseline", json=payload, name="[Setup] Create baseline")
    
    @task(5)
    def get_quality_insights(self):
        """Test quality insights endpoint."""
        self.client.get("/quality/insights", name="/quality/insights")
    
    @task(3)
    def establish_baseline(self):
        """Test baseline establishment."""
        payload = {
            "model_name": random.choice(self.model_names),
            "config_hash": random.choice(self.config_hashes),
            "sample_size": 100
        }
        self.client.post("/regression/baseline", json=payload, name="/regression/baseline")
    
    @task(3)
    def detect_regression(self):
        """Test regression detection."""
        # Use existing model/config combinations
        payload = {
            "model_name": random.choice(self.model_names),
            "config_hash": random.choice(self.config_hashes),
            "current_quality": random.uniform(70, 95)
        }
        self.client.post("/regression/detect", json=payload, name="/regression/detect")
    
    @task(2)
    def create_validation(self):
        """Test validation creation."""
        payload = {
            "name": f"validation-{random.randint(1, 1000)}",
            "model_name": random.choice(self.model_names),
            "baseline_quality": random.uniform(80, 90),
            "new_quality": random.uniform(85, 95)
        }
        self.client.post("/validation/create", json=payload, name="/validation/create")
    
    @task(2)
    def run_workflow(self):
        """Test workflow execution."""
        payload = {
            "model_name": random.choice(self.model_names),
            "prompt": random.choice(self.prompts),
            "response": random.choice(self.responses)
        }
        self.client.post("/workflow/validate", json=payload, name="/workflow/validate")
    
    @task(3)
    def get_analytics(self):
        """Test analytics endpoints."""
        endpoints = [
            "/analytics/summary",
            "/analytics/trends",
            "/analytics/comparison?models=model-v1,model-v2"
        ]
        endpoint = random.choice(endpoints)
        self.client.get(endpoint, name="/analytics/*")
    
    @task(2)
    def get_configuration(self):
        """Test configuration endpoints."""
        self.client.get("/config/current", name="/config/current")
    
    @task(1)
    def health_check(self):
        """Test health check."""
        self.client.get("/health", name="/health")
    
    @task(1)
    def admin_stats(self):
        """Test admin stats."""
        self.client.get("/admin/stats", name="/admin/stats")


class HighLoadUser(ApplicationAgentUser):
    """High load user with shorter wait times."""
    wait_time = between(0.5, 1.5)


class BurstUser(ApplicationAgentUser):
    """Burst user with no wait time."""
    wait_time = between(0, 0.5)


# Event handlers for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print(f"Performance test started at {datetime.now()}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    print(f"Performance test stopped at {datetime.now()}")
    
    # Print summary statistics
    stats = environment.stats
    print("\n=== Performance Test Summary ===")
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Min response time: {stats.total.min_response_time:.2f}ms")
    print(f"Max response time: {stats.total.max_response_time:.2f}ms")
    print(f"Requests per second: {stats.total.total_rps:.2f}")
