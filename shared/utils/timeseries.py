"""
Time Series Helper Functions

Utilities for working with time series data.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import statistics


def create_time_windows(
    start_time: datetime,
    end_time: datetime,
    window_size: timedelta,
) -> List[Tuple[datetime, datetime]]:
    """
    Create time windows between start and end time.
    
    Args:
        start_time: Start datetime
        end_time: End datetime
        window_size: Size of each window
    
    Returns:
        List of (window_start, window_end) tuples
    
    Example:
        windows = create_time_windows(
            start_time=datetime(2025, 1, 1),
            end_time=datetime(2025, 1, 2),
            window_size=timedelta(hours=1)
        )
        # Returns 24 hourly windows
    """
    windows = []
    current = start_time
    
    while current < end_time:
        window_end = min(current + window_size, end_time)
        windows.append((current, window_end))
        current = window_end
    
    return windows


def aggregate_time_series(
    data: List[Dict],
    timestamp_field: str,
    value_field: str,
    window_size: timedelta,
    aggregation: str = 'avg',
) -> List[Dict]:
    """
    Aggregate time series data into windows.
    
    Args:
        data: List of data points with timestamps
        timestamp_field: Name of timestamp field
        value_field: Name of value field to aggregate
        window_size: Size of aggregation window
        aggregation: Aggregation function ('avg', 'sum', 'min', 'max', 'count')
    
    Returns:
        List of aggregated data points
    
    Example:
        data = [
            {'timestamp': datetime(2025, 1, 1, 0, 0), 'cpu': 45.2},
            {'timestamp': datetime(2025, 1, 1, 0, 5), 'cpu': 52.1},
            ...
        ]
        
        result = aggregate_time_series(
            data=data,
            timestamp_field='timestamp',
            value_field='cpu',
            window_size=timedelta(hours=1),
            aggregation='avg'
        )
    """
    if not data:
        return []
    
    # Sort by timestamp
    sorted_data = sorted(data, key=lambda x: x[timestamp_field])
    
    # Get time range
    start_time = sorted_data[0][timestamp_field]
    end_time = sorted_data[-1][timestamp_field]
    
    # Create windows
    windows = create_time_windows(start_time, end_time, window_size)
    
    # Aggregate data
    aggregated = []
    
    for window_start, window_end in windows:
        # Filter data in this window
        window_data = [
            d[value_field]
            for d in sorted_data
            if window_start <= d[timestamp_field] < window_end
        ]
        
        if not window_data:
            continue
        
        # Calculate aggregation
        if aggregation == 'avg':
            value = statistics.mean(window_data)
        elif aggregation == 'sum':
            value = sum(window_data)
        elif aggregation == 'min':
            value = min(window_data)
        elif aggregation == 'max':
            value = max(window_data)
        elif aggregation == 'count':
            value = len(window_data)
        else:
            raise ValueError(f"Unknown aggregation: {aggregation}")
        
        aggregated.append({
            'window_start': window_start,
            'window_end': window_end,
            'value': value,
            'count': len(window_data),
        })
    
    return aggregated


def calculate_rate_of_change(
    data: List[Dict],
    timestamp_field: str,
    value_field: str,
) -> List[Dict]:
    """
    Calculate rate of change between consecutive data points.
    
    Args:
        data: List of data points
        timestamp_field: Name of timestamp field
        value_field: Name of value field
    
    Returns:
        List of data points with rate_of_change field
    """
    if len(data) < 2:
        return []
    
    sorted_data = sorted(data, key=lambda x: x[timestamp_field])
    result = []
    
    for i in range(1, len(sorted_data)):
        prev = sorted_data[i - 1]
        curr = sorted_data[i]
        
        time_diff = (curr[timestamp_field] - prev[timestamp_field]).total_seconds()
        value_diff = curr[value_field] - prev[value_field]
        
        if time_diff > 0:
            rate = value_diff / time_diff
        else:
            rate = 0
        
        result.append({
            'timestamp': curr[timestamp_field],
            'value': curr[value_field],
            'rate_of_change': rate,
        })
    
    return result


def detect_anomalies(
    data: List[float],
    threshold_std_dev: float = 2.0,
) -> List[int]:
    """
    Detect anomalies using standard deviation method.
    
    Args:
        data: List of numeric values
        threshold_std_dev: Number of standard deviations for anomaly threshold
    
    Returns:
        List of indices where anomalies were detected
    
    Example:
        values = [10, 12, 11, 10, 50, 11, 12]  # 50 is an anomaly
        anomaly_indices = detect_anomalies(values)
        # Returns [4]
    """
    if len(data) < 3:
        return []
    
    mean = statistics.mean(data)
    std_dev = statistics.stdev(data)
    
    anomalies = []
    for i, value in enumerate(data):
        if abs(value - mean) > threshold_std_dev * std_dev:
            anomalies.append(i)
    
    return anomalies
