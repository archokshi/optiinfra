"""
Cost Agent Specific Metrics

Metrics for tracking cost optimization performance.
"""

from prometheus_client import Counter, Gauge, Histogram, REGISTRY
from shared.utils.prometheus_metrics import BaseMetrics


class CostAgentMetrics(BaseMetrics):
    """Metrics specific to the Cost Agent"""
    
    def __init__(self):
        super().__init__('cost-agent', REGISTRY)
        
        # Cost savings metrics
        self.cost_savings_total = Counter(
            'cost_savings_total',
            'Total cost savings in USD',
            ['provider', 'optimization_type'],
            registry=self.registry
        )
        
        self.cost_recommendations_total = Counter(
            'cost_recommendations_total',
            'Total cost recommendations made',
            ['type', 'provider'],  # type: spot, reserved, right-sizing
            registry=self.registry
        )
        
        # Spot instance metrics
        self.spot_migration_success_rate = Gauge(
            'spot_migration_success_rate',
            'Success rate of spot instance migrations',
            registry=self.registry
        )
        
        self.spot_migration_attempts_total = Counter(
            'spot_migration_attempts_total',
            'Total spot migration attempts',
            ['outcome'],  # outcome: success, failure
            registry=self.registry
        )
        
        self.spot_migration_success_total = Counter(
            'spot_migration_success_total',
            'Total successful spot migrations',
            registry=self.registry
        )
        
        # Reserved instance metrics
        self.reserved_instance_coverage = Gauge(
            'reserved_instance_coverage',
            'Percentage of instances covered by reservations',
            ['provider'],
            registry=self.registry
        )
        
        self.reserved_instance_recommendations_total = Counter(
            'reserved_instance_recommendations_total',
            'Total reserved instance recommendations',
            ['provider'],
            registry=self.registry
        )
        
        # Right-sizing metrics
        self.right_sizing_opportunities = Gauge(
            'right_sizing_opportunities',
            'Number of right-sizing opportunities identified',
            ['provider'],
            registry=self.registry
        )
        
        self.right_sizing_savings_potential = Gauge(
            'right_sizing_savings_potential',
            'Potential savings from right-sizing (USD/month)',
            ['provider'],
            registry=self.registry
        )
        
        # Analysis metrics
        self.cost_analysis_duration_seconds = Histogram(
            'cost_analysis_duration_seconds',
            'Duration of cost analysis in seconds',
            ['analysis_type'],
            buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60),
            registry=self.registry
        )
        
        self.instances_analyzed_total = Counter(
            'instances_analyzed_total',
            'Total instances analyzed',
            ['provider'],
            registry=self.registry
        )
    
    def record_savings(self, provider: str, optimization_type: str, amount: float):
        """Record cost savings"""
        self.cost_savings_total.labels(
            provider=provider,
            optimization_type=optimization_type
        ).inc(amount)
    
    def record_recommendation(self, rec_type: str, provider: str):
        """Record a cost recommendation"""
        self.cost_recommendations_total.labels(
            type=rec_type,
            provider=provider
        ).inc()
    
    def record_spot_migration(self, success: bool):
        """Record a spot migration attempt"""
        outcome = 'success' if success else 'failure'
        self.spot_migration_attempts_total.labels(outcome=outcome).inc()
        
        if success:
            self.spot_migration_success_total.inc()
        
        # Update success rate
        total_attempts = sum(
            self.spot_migration_attempts_total.labels(outcome=o)._value.get()
            for o in ['success', 'failure']
        )
        if total_attempts > 0:
            success_count = self.spot_migration_success_total._value.get()
            self.spot_migration_success_rate.set(success_count / total_attempts)
    
    def update_reserved_coverage(self, provider: str, coverage: float):
        """Update reserved instance coverage percentage"""
        self.reserved_instance_coverage.labels(provider=provider).set(coverage)
    
    def update_right_sizing_opportunities(self, provider: str, count: int, savings: float):
        """Update right-sizing opportunities"""
        self.right_sizing_opportunities.labels(provider=provider).set(count)
        self.right_sizing_savings_potential.labels(provider=provider).set(savings)
    
    def track_analysis(self, analysis_type: str, duration: float, instance_count: int, provider: str):
        """Track a cost analysis operation"""
        self.cost_analysis_duration_seconds.labels(
            analysis_type=analysis_type
        ).observe(duration)
        
        self.instances_analyzed_total.labels(
            provider=provider
        ).inc(instance_count)


# Global metrics instance
cost_metrics = CostAgentMetrics()
