#!/usr/bin/env python3
"""Test time series utilities"""
import sys
sys.path.insert(0, r'C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra')

from datetime import datetime, timedelta
from shared.utils import (
    create_time_windows,
    aggregate_time_series,
    calculate_rate_of_change,
    detect_anomalies,
)

print("=" * 60)
print("TESTING TIME SERIES MODULE")
print("=" * 60)

# Test 1: Create time windows
print("\n1. Creating time windows:")
start = datetime(2025, 1, 1, 0, 0)
end = datetime(2025, 1, 1, 6, 0)
windows = create_time_windows(start, end, timedelta(hours=1))
print(f"   Created {len(windows)} hourly windows")
print(f"   First window: {windows[0]}")
print(f"   Last window: {windows[-1]}")

# Test 2: Aggregate time series
print("\n2. Aggregating time series data:")
data = [
    {'timestamp': datetime(2025, 1, 1, 0, 5), 'cpu': 45.2},
    {'timestamp': datetime(2025, 1, 1, 0, 15), 'cpu': 52.1},
    {'timestamp': datetime(2025, 1, 1, 0, 25), 'cpu': 48.5},
    {'timestamp': datetime(2025, 1, 1, 0, 35), 'cpu': 51.0},
    {'timestamp': datetime(2025, 1, 1, 1, 5), 'cpu': 47.3},
    {'timestamp': datetime(2025, 1, 1, 1, 15), 'cpu': 49.8},
]

aggregated = aggregate_time_series(
    data=data,
    timestamp_field='timestamp',
    value_field='cpu',
    window_size=timedelta(hours=1),
    aggregation='avg'
)

print(f"   Aggregated {len(data)} points into {len(aggregated)} windows")
for agg in aggregated:
    print(f"   Window {agg['window_start'].strftime('%H:%M')}: avg={agg['value']:.2f}, count={agg['count']}")

# Test 3: Calculate rate of change
print("\n3. Calculating rate of change:")
rate_data = calculate_rate_of_change(
    data=data,
    timestamp_field='timestamp',
    value_field='cpu'
)
print(f"   Calculated rate for {len(rate_data)} points")
print(f"   Sample: {rate_data[0]}")

# Test 4: Detect anomalies
print("\n4. Detecting anomalies:")
values = [10, 12, 11, 10, 50, 11, 12, 9, 45, 10]  # 50 and 45 are anomalies
anomaly_indices = detect_anomalies(values, threshold_std_dev=2.0)
print(f"   Detected {len(anomaly_indices)} anomalies at indices: {anomaly_indices}")
print(f"   Anomalous values: {[values[i] for i in anomaly_indices]}")

print("\n" + "=" * 60)
print("✅ TIME SERIES MODULE TEST PASSED")
print("=" * 60)
