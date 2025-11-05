"""
Prometheus Metrics Parser

Parses Prometheus text format metrics.
"""

import re
from typing import List, Dict, Tuple, Optional
import logging

from src.models.metrics import PrometheusMetric, MetricType

logger = logging.getLogger(__name__)


class PrometheusParser:
    """Parser for Prometheus text format metrics."""
    
    # Regex patterns
    METRIC_LINE_PATTERN = re.compile(
        r'^(?P<name>[a-zA-Z_:][a-zA-Z0-9_:]*)'
        r'(?:\{(?P<labels>[^}]+)\})?\s+'
        r'(?P<value>[^\s]+)'
        r'(?:\s+(?P<timestamp>\d+))?$'
    )
    
    TYPE_PATTERN = re.compile(r'^#\s+TYPE\s+(?P<name>\S+)\s+(?P<type>\S+)')
    HELP_PATTERN = re.compile(r'^#\s+HELP\s+(?P<name>\S+)\s+(?P<help>.+)')
    
    def __init__(self):
        self.metric_types: Dict[str, str] = {}
        self.metric_help: Dict[str, str] = {}
    
    def parse(self, text: str) -> List[PrometheusMetric]:
        """
        Parse Prometheus text format metrics.
        
        Args:
            text: Prometheus metrics in text format
            
        Returns:
            List of parsed metrics
        """
        metrics: List[PrometheusMetric] = []
        
        for line in text.split('\n'):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Parse TYPE comments
            type_match = self.TYPE_PATTERN.match(line)
            if type_match:
                self.metric_types[type_match.group('name')] = type_match.group('type')
                continue
            
            # Parse HELP comments
            help_match = self.HELP_PATTERN.match(line)
            if help_match:
                self.metric_help[help_match.group('name')] = help_match.group('help')
                continue
            
            # Skip other comments
            if line.startswith('#'):
                continue
            
            # Parse metric line
            metric = self._parse_metric_line(line)
            if metric:
                metrics.append(metric)
        
        return metrics
    
    def _parse_metric_line(self, line: str) -> Optional[PrometheusMetric]:
        """Parse a single metric line."""
        match = self.METRIC_LINE_PATTERN.match(line)
        if not match:
            logger.warning(f"Failed to parse metric line: {line}")
            return None
        
        name = match.group('name')
        value_str = match.group('value')
        labels_str = match.group('labels')
        
        # Parse value
        try:
            value = float(value_str)
        except ValueError:
            logger.warning(f"Invalid metric value: {value_str}")
            return None
        
        # Parse labels
        labels = self._parse_labels(labels_str) if labels_str else {}
        
        # Get metric type
        metric_type = self._get_metric_type(name)
        
        return PrometheusMetric(
            name=name,
            type=metric_type,
            value=value,
            labels=labels
        )
    
    def _parse_labels(self, labels_str: str) -> Dict[str, str]:
        """Parse label string into dictionary."""
        labels = {}
        
        # Split by comma, but respect quoted values
        parts = re.findall(r'(\w+)="([^"]*)"', labels_str)
        
        for key, value in parts:
            labels[key] = value
        
        return labels
    
    def _get_metric_type(self, name: str) -> MetricType:
        """Get metric type from name."""
        # Check if we have explicit type
        if name in self.metric_types:
            type_str = self.metric_types[name]
            try:
                return MetricType(type_str.lower())
            except ValueError:
                pass
        
        # Infer from name
        if name.endswith('_total'):
            return MetricType.COUNTER
        elif name.endswith('_seconds') or name.endswith('_bytes'):
            return MetricType.HISTOGRAM
        else:
            return MetricType.GAUGE
    
    def filter_metrics(
        self,
        metrics: List[PrometheusMetric],
        prefix: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> List[PrometheusMetric]:
        """
        Filter metrics by prefix and labels.
        
        Args:
            metrics: List of metrics to filter
            prefix: Metric name prefix filter
            labels: Label filters
            
        Returns:
            Filtered metrics
        """
        filtered = metrics
        
        # Filter by prefix
        if prefix:
            filtered = [m for m in filtered if m.name.startswith(prefix)]
        
        # Filter by labels
        if labels:
            filtered = [
                m for m in filtered
                if all(m.labels.get(k) == v for k, v in labels.items())
            ]
        
        return filtered
