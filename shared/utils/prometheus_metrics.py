"""
Prometheus Metrics for Python Agents

Base metrics class and utilities for all Python agents.
"""

import time
import logging
from typing import Dict, Optional, Callable
from functools import wraps

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    REGISTRY,
    CollectorRegistry,
)

logger = logging.getLogger(__name__)


class BaseMetrics:
    """Base metrics class for all Python agents"""
    
    def __init__(self, service_name: str, registry: CollectorRegistry = REGISTRY):
        """
        Initialize base metrics for a service.
        
        Args:
            service_name: Name of the service (e.g., 'cost-agent')
            registry: Prometheus registry to use
        """
        self.service_name = service_name
        self.registry = registry
        
        # Request metrics
        self.requests_total = Counter(
            'requests_total',
            'Total number of requests',
            ['endpoint', 'method', 'status'],
            registry=registry
        )
        
        self.request_duration_seconds = Histogram(
            'request_duration_seconds',
            'Request duration in seconds',
            ['endpoint', 'method'],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
            registry=registry
        )
        
        # Error metrics
        self.errors_total = Counter(
            'errors_total',
            'Total number of errors',
            ['error_type', 'endpoint'],
            registry=registry
        )
        
        # LLM metrics
        self.llm_api_calls_total = Counter(
            'llm_api_calls_total',
            'Total LLM API calls',
            ['provider', 'model'],
            registry=registry
        )
        
        self.llm_token_usage_total = Counter(
            'llm_token_usage_total',
            'Total LLM tokens used',
            ['provider', 'type'],  # type: input, output, total
            registry=registry
        )
        
        self.llm_cost_total = Counter(
            'llm_cost_total',
            'Total LLM cost in USD',
            ['provider', 'model'],
            registry=registry
        )
        
        # Optimization metrics
        self.optimization_executions_total = Counter(
            'optimization_executions_total',
            'Total optimization executions',
            ['type', 'outcome'],  # outcome: success, failure, skipped
            registry=registry
        )
        
        self.recommendation_confidence = Histogram(
            'recommendation_confidence',
            'Confidence score of recommendations',
            ['type'],
            buckets=(0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.99, 1.0),
            registry=registry
        )
        
        # Service info
        self.service_info = Info(
            'service',
            'Service information',
            registry=registry
        )
        self.service_info.info({
            'name': service_name,
            'version': '1.0.0',
            'type': 'agent'
        })
    
    def track_request(self, endpoint: str, method: str, status: int, duration: float):
        """Track a request with its metrics"""
        try:
            self.requests_total.labels(
                endpoint=endpoint,
                method=method,
                status=str(status)
            ).inc()
            
            self.request_duration_seconds.labels(
                endpoint=endpoint,
                method=method
            ).observe(duration)
        except Exception as e:
            logger.error(f"Failed to track request metrics: {e}")
    
    def track_error(self, error_type: str, endpoint: str):
        """Track an error"""
        try:
            self.errors_total.labels(
                error_type=error_type,
                endpoint=endpoint
            ).inc()
        except Exception as e:
            logger.error(f"Failed to track error metrics: {e}")
    
    def track_llm_call(self, provider: str, model: str, input_tokens: int, 
                       output_tokens: int, cost: float):
        """Track an LLM API call"""
        try:
            self.llm_api_calls_total.labels(
                provider=provider,
                model=model
            ).inc()
            
            self.llm_token_usage_total.labels(
                provider=provider,
                type='input'
            ).inc(input_tokens)
            
            self.llm_token_usage_total.labels(
                provider=provider,
                type='output'
            ).inc(output_tokens)
            
            self.llm_token_usage_total.labels(
                provider=provider,
                type='total'
            ).inc(input_tokens + output_tokens)
            
            self.llm_cost_total.labels(
                provider=provider,
                model=model
            ).inc(cost)
        except Exception as e:
            logger.error(f"Failed to track LLM metrics: {e}")
    
    def track_optimization(self, opt_type: str, outcome: str, confidence: Optional[float] = None):
        """Track an optimization execution"""
        try:
            self.optimization_executions_total.labels(
                type=opt_type,
                outcome=outcome
            ).inc()
            
            if confidence is not None:
                self.recommendation_confidence.labels(
                    type=opt_type
                ).observe(confidence)
        except Exception as e:
            logger.error(f"Failed to track optimization metrics: {e}")
    
    def get_metrics(self) -> bytes:
        """Get current metrics in Prometheus format"""
        return generate_latest(self.registry)


def track_duration(metric_name: str = None):
    """
    Decorator to track function execution duration.
    
    Args:
        metric_name: Name of the metric (defaults to function name)
    
    Example:
        @track_duration('process_request')
        def process_request():
            # Function code
            pass
    """
    def decorator(func: Callable):
        nonlocal metric_name
        if metric_name is None:
            metric_name = f"{func.__module__}.{func.__name__}_duration_seconds"
        
        # Create histogram for this function
        histogram = Histogram(
            metric_name,
            f'Duration of {func.__name__} in seconds',
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)
        )
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                histogram.observe(duration)
        
        return wrapper
    return decorator


def track_errors(error_counter: Counter = None):
    """
    Decorator to track function errors.
    
    Args:
        error_counter: Counter metric to use (creates one if not provided)
    
    Example:
        @track_errors()
        def risky_function():
            # Function code that might fail
            pass
    """
    def decorator(func: Callable):
        nonlocal error_counter
        if error_counter is None:
            error_counter = Counter(
                f"{func.__module__}_{func.__name__}_errors_total",
                f'Total errors in {func.__name__}',
                ['error_type']
            )
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_counter.labels(
                    error_type=type(e).__name__
                ).inc()
                raise
        
        return wrapper
    return decorator


class FastAPIMetricsMiddleware:
    """
    FastAPI middleware for automatic request tracking.
    
    Usage:
        from fastapi import FastAPI
        from shared.utils.prometheus_metrics import FastAPIMetricsMiddleware, BaseMetrics
        
        app = FastAPI()
        metrics = BaseMetrics('my-service')
        app.add_middleware(FastAPIMetricsMiddleware, metrics=metrics)
    """
    
    def __init__(self, app, metrics: BaseMetrics):
        self.app = app
        self.metrics = metrics
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        # Get request info
        method = scope.get("method", "")
        path = scope.get("path", "")
        
        # Track the request
        status_code = 200
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            status_code = 500
            self.metrics.track_error(type(e).__name__, path)
            raise
        finally:
            duration = time.time() - start_time
            self.metrics.track_request(path, method, status_code, duration)


# Convenience function for FastAPI metrics endpoint
def create_metrics_endpoint(metrics: BaseMetrics):
    """
    Create a FastAPI endpoint that returns Prometheus metrics.
    
    Usage:
        from fastapi import FastAPI
        from shared.utils.prometheus_metrics import BaseMetrics, create_metrics_endpoint
        
        app = FastAPI()
        metrics = BaseMetrics('my-service')
        
        @app.get("/metrics")
        async def metrics_endpoint():
            return create_metrics_endpoint(metrics)
    """
    from fastapi.responses import Response
    
    def endpoint():
        return Response(
            content=metrics.get_metrics(),
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    
    return endpoint
