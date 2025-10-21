"""
Performance Metrics Collector

Utilities for collecting and tracking performance metrics.
"""

import time
import logging
from typing import Dict, Optional, Callable
from functools import wraps
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and tracks performance metrics"""
    
    def __init__(self):
        self._metrics: Dict[str, list] = {}
    
    def record(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """Record a metric value"""
        if metric_name not in self._metrics:
            self._metrics[metric_name] = []
        
        self._metrics[metric_name].append({
            'value': value,
            'timestamp': time.time(),
            'tags': tags or {},
        })
    
    def get_metrics(self, metric_name: str) -> list:
        """Get all recorded values for a metric"""
        return self._metrics.get(metric_name, [])
    
    def get_average(self, metric_name: str) -> Optional[float]:
        """Get average value for a metric"""
        metrics = self.get_metrics(metric_name)
        if not metrics:
            return None
        return sum(m['value'] for m in metrics) / len(metrics)
    
    def get_latest(self, metric_name: str) -> Optional[float]:
        """Get latest value for a metric"""
        metrics = self.get_metrics(metric_name)
        if not metrics:
            return None
        return metrics[-1]['value']
    
    def clear(self, metric_name: str = None):
        """Clear metrics (all or specific metric)"""
        if metric_name:
            self._metrics.pop(metric_name, None)
        else:
            self._metrics.clear()
    
    def get_summary(self) -> Dict[str, Dict]:
        """Get summary of all metrics"""
        summary = {}
        for metric_name, values in self._metrics.items():
            if values:
                summary[metric_name] = {
                    'count': len(values),
                    'latest': values[-1]['value'],
                    'average': sum(v['value'] for v in values) / len(values),
                    'min': min(v['value'] for v in values),
                    'max': max(v['value'] for v in values),
                }
        return summary


# Global metrics collector
metrics_collector = MetricsCollector()


def measure_time(metric_name: str = None, tags: Dict[str, str] = None):
    """
    Decorator to measure function execution time.
    
    Example:
        @measure_time('api_call_duration')
        def fetch_data():
            # Function code
            pass
    """
    def decorator(func: Callable):
        nonlocal metric_name
        if metric_name is None:
            metric_name = f"{func.__module__}.{func.__name__}_duration"
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metrics_collector.record(metric_name, duration, tags)
                logger.debug(f"{func.__name__} took {duration:.3f}s")
        
        return wrapper
    return decorator


@contextmanager
def measure_block(metric_name: str, tags: Dict[str, str] = None):
    """
    Context manager to measure code block execution time.
    
    Example:
        with measure_block('database_query'):
            # Code to measure
            result = db.query()
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        metrics_collector.record(metric_name, duration, tags)
        logger.debug(f"{metric_name} took {duration:.3f}s")


def count_calls(metric_name: str = None):
    """
    Decorator to count function calls.
    
    Example:
        @count_calls('api_requests')
        def handle_request():
            # Function code
            pass
    """
    def decorator(func: Callable):
        nonlocal metric_name
        if metric_name is None:
            metric_name = f"{func.__module__}.{func.__name__}_calls"
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            metrics_collector.record(metric_name, 1)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
