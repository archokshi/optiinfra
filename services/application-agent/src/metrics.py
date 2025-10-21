"""
Application Agent Specific Metrics

Metrics for tracking application quality and validation.
"""

from prometheus_client import Counter, Gauge, Histogram, REGISTRY
from shared.utils.prometheus_metrics import BaseMetrics


class ApplicationAgentMetrics(BaseMetrics):
    """Metrics specific to the Application Agent"""
    
    def __init__(self):
        super().__init__('application-agent', REGISTRY)
        
        # Quality score metrics
        self.quality_score = Gauge(
            'quality_score',
            'Overall quality score (0-1)',
            ['metric_type'],  # relevance, coherence, hallucination, overall
            registry=self.registry
        )
        
        self.quality_score_history = Histogram(
            'quality_score_history',
            'Distribution of quality scores',
            ['metric_type'],
            buckets=(0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.99, 1.0),
            registry=self.registry
        )
        
        # Regression detection
        self.regression_detections_total = Counter(
            'regression_detections_total',
            'Total quality regressions detected',
            ['regression_type'],  # latency, accuracy, cost
            registry=self.registry
        )
        
        self.regression_detection_latency_seconds = Histogram(
            'regression_detection_latency_seconds',
            'Time to detect regression in seconds',
            buckets=(1, 5, 10, 30, 60, 300, 600),
            registry=self.registry
        )
        
        self.false_positive_rate = Gauge(
            'false_positive_rate',
            'False positive rate in regression detection (0-1)',
            registry=self.registry
        )
        
        # A/B testing metrics
        self.ab_test_active = Gauge(
            'ab_test_active',
            'Number of active A/B tests',
            registry=self.registry
        )
        
        self.ab_test_results = Gauge(
            'ab_test_results',
            'A/B test metric results',
            ['test_id', 'variant', 'metric'],
            registry=self.registry
        )
        
        self.ab_test_statistical_significance = Gauge(
            'ab_test_statistical_significance',
            'Statistical significance of A/B test (p-value)',
            ['test_id'],
            registry=self.registry
        )
        
        self.ab_test_winning_variants_total = Counter(
            'ab_test_winning_variants_total',
            'Total winning variants in A/B tests',
            ['variant'],
            registry=self.registry
        )
        
        # Validation metrics
        self.validation_duration_seconds = Histogram(
            'validation_duration_seconds',
            'Duration of validation in seconds',
            ['validation_type'],
            buckets=(0.1, 0.5, 1, 5, 10, 30, 60),
            registry=self.registry
        )
        
        self.validation_results_total = Counter(
            'validation_results_total',
            'Total validation results',
            ['result'],  # approved, rejected
            registry=self.registry
        )
        
        self.validation_approval_rate = Gauge(
            'validation_approval_rate',
            'Approval rate of validations (0-1)',
            registry=self.registry
        )
        
        # Auto-rollback metrics
        self.auto_rollback_events_total = Counter(
            'auto_rollback_events_total',
            'Total auto-rollback events',
            ['trigger_reason'],
            registry=self.registry
        )
        
        self.rollback_duration_seconds = Histogram(
            'rollback_duration_seconds',
            'Duration of rollback in seconds',
            buckets=(1, 5, 10, 30, 60, 120),
            registry=self.registry
        )
        
        # Quality by optimization type
        self.quality_by_optimization = Gauge(
            'quality_by_optimization',
            'Quality score by optimization type',
            ['optimization_type'],
            registry=self.registry
        )
        
        self.quality_safety_margin = Gauge(
            'quality_safety_margin',
            'Safety margin above minimum quality threshold',
            registry=self.registry
        )
        
        # Specific quality metrics
        self.relevance_score = Gauge(
            'relevance_score',
            'Relevance score (0-1)',
            registry=self.registry
        )
        
        self.coherence_score = Gauge(
            'coherence_score',
            'Coherence score (0-1)',
            registry=self.registry
        )
        
        self.hallucination_rate = Gauge(
            'hallucination_rate',
            'Hallucination rate (0-1)',
            registry=self.registry
        )
        
        # Monitoring coverage
        self.monitored_endpoints_total = Gauge(
            'monitored_endpoints_total',
            'Total number of monitored endpoints',
            registry=self.registry
        )
        
        self.validation_coverage = Gauge(
            'validation_coverage',
            'Percentage of requests validated (0-1)',
            registry=self.registry
        )
    
    def update_quality_score(self, metric_type: str, score: float):
        """Update quality score"""
        self.quality_score.labels(metric_type=metric_type).set(score)
        self.quality_score_history.labels(metric_type=metric_type).observe(score)
        
        # Update specific metrics
        if metric_type == 'relevance':
            self.relevance_score.set(score)
        elif metric_type == 'coherence':
            self.coherence_score.set(score)
        elif metric_type == 'hallucination':
            self.hallucination_rate.set(1.0 - score)  # Invert for rate
    
    def record_regression(self, regression_type: str, detection_latency: float):
        """Record a quality regression"""
        self.regression_detections_total.labels(
            regression_type=regression_type
        ).inc()
        
        self.regression_detection_latency_seconds.observe(detection_latency)
    
    def update_false_positive_rate(self, rate: float):
        """Update false positive rate"""
        self.false_positive_rate.set(rate)
    
    def update_ab_test(self, test_id: str, variant: str, metric: str, value: float):
        """Update A/B test metrics"""
        self.ab_test_results.labels(
            test_id=test_id,
            variant=variant,
            metric=metric
        ).set(value)
    
    def update_ab_test_significance(self, test_id: str, p_value: float):
        """Update A/B test statistical significance"""
        self.ab_test_statistical_significance.labels(test_id=test_id).set(p_value)
    
    def record_winning_variant(self, variant: str):
        """Record a winning A/B test variant"""
        self.ab_test_winning_variants_total.labels(variant=variant).inc()
    
    def update_active_tests(self, count: int):
        """Update number of active A/B tests"""
        self.ab_test_active.set(count)
    
    def record_validation(self, validation_type: str, duration: float, approved: bool):
        """Record a validation"""
        self.validation_duration_seconds.labels(
            validation_type=validation_type
        ).observe(duration)
        
        result = 'approved' if approved else 'rejected'
        self.validation_results_total.labels(result=result).inc()
        
        # Update approval rate
        total_approved = self.validation_results_total.labels(result='approved')._value.get()
        total_rejected = self.validation_results_total.labels(result='rejected')._value.get()
        total = total_approved + total_rejected
        
        if total > 0:
            self.validation_approval_rate.set(total_approved / total)
    
    def record_rollback(self, trigger_reason: str, duration: float):
        """Record an auto-rollback event"""
        self.auto_rollback_events_total.labels(
            trigger_reason=trigger_reason
        ).inc()
        
        self.rollback_duration_seconds.observe(duration)
    
    def update_quality_by_optimization(self, opt_type: str, quality: float):
        """Update quality score by optimization type"""
        self.quality_by_optimization.labels(
            optimization_type=opt_type
        ).set(quality)
    
    def update_safety_margin(self, margin: float):
        """Update quality safety margin"""
        self.quality_safety_margin.set(margin)
    
    def update_monitoring_coverage(self, total_endpoints: int, coverage: float):
        """Update monitoring coverage metrics"""
        self.monitored_endpoints_total.set(total_endpoints)
        self.validation_coverage.set(coverage)
