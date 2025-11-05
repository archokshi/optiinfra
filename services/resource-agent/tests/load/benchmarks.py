"""
Performance Benchmarks and SLAs

Defines performance targets and validation criteria.
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class ResponseTimeSLA:
    """Response time SLA for an endpoint."""
    
    endpoint: str
    p50_ms: float  # 50th percentile
    p95_ms: float  # 95th percentile
    p99_ms: float  # 99th percentile
    max_ms: float  # Maximum acceptable


@dataclass
class ThroughputSLA:
    """Throughput SLA for a load level."""
    
    load_level: str
    min_rps: float  # Minimum requests per second
    concurrent_users: int
    max_error_rate: float  # Maximum error rate (0.01 = 1%)


# Response Time SLAs
RESPONSE_TIME_SLAS = [
    ResponseTimeSLA(
        endpoint="/health/",
        p50_ms=10,
        p95_ms=20,
        p99_ms=50,
        max_ms=100
    ),
    ResponseTimeSLA(
        endpoint="/system/metrics",
        p50_ms=100,
        p95_ms=200,
        p99_ms=500,
        max_ms=1000
    ),
    ResponseTimeSLA(
        endpoint="/analysis/",
        p50_ms=500,
        p95_ms=1000,
        p99_ms=2000,
        max_ms=3000
    ),
    ResponseTimeSLA(
        endpoint="/lmcache/status",
        p50_ms=50,
        p95_ms=100,
        p99_ms=200,
        max_ms=500
    ),
    ResponseTimeSLA(
        endpoint="/optimize/run",
        p50_ms=1000,
        p95_ms=2000,
        p99_ms=3000,
        max_ms=5000
    ),
]


# Throughput SLAs
THROUGHPUT_SLAS = [
    ThroughputSLA(
        load_level="light",
        min_rps=10,
        concurrent_users=10,
        max_error_rate=0.001  # 0.1%
    ),
    ThroughputSLA(
        load_level="medium",
        min_rps=40,
        concurrent_users=50,
        max_error_rate=0.005  # 0.5%
    ),
    ThroughputSLA(
        load_level="heavy",
        min_rps=80,
        concurrent_users=100,
        max_error_rate=0.01  # 1%
    ),
    ThroughputSLA(
        load_level="stress",
        min_rps=100,
        concurrent_users=200,
        max_error_rate=0.05  # 5%
    ),
]


def get_response_time_sla(endpoint: str) -> ResponseTimeSLA:
    """
    Get response time SLA for an endpoint.
    
    Args:
        endpoint: Endpoint path
        
    Returns:
        ResponseTimeSLA or None if not found
    """
    for sla in RESPONSE_TIME_SLAS:
        if sla.endpoint == endpoint:
            return sla
    return None


def get_throughput_sla(load_level: str) -> ThroughputSLA:
    """
    Get throughput SLA for a load level.
    
    Args:
        load_level: Load level name
        
    Returns:
        ThroughputSLA or None if not found
    """
    for sla in THROUGHPUT_SLAS:
        if sla.load_level == load_level:
            return sla
    return None


def validate_response_times(stats: Dict[str, Any], endpoint: str) -> Dict[str, bool]:
    """
    Validate response times against SLA.
    
    Args:
        stats: Statistics dictionary with percentiles
        endpoint: Endpoint path
        
    Returns:
        Dictionary with validation results
    """
    sla = get_response_time_sla(endpoint)
    if not sla:
        return {"valid": True, "message": "No SLA defined"}
    
    results = {
        "p50_valid": stats.get("p50", 0) <= sla.p50_ms,
        "p95_valid": stats.get("p95", 0) <= sla.p95_ms,
        "p99_valid": stats.get("p99", 0) <= sla.p99_ms,
        "max_valid": stats.get("max", 0) <= sla.max_ms,
    }
    
    results["valid"] = all(results.values())
    return results


def validate_throughput(rps: float, error_rate: float, load_level: str) -> Dict[str, bool]:
    """
    Validate throughput against SLA.
    
    Args:
        rps: Requests per second
        error_rate: Error rate (0.01 = 1%)
        load_level: Load level name
        
    Returns:
        Dictionary with validation results
    """
    sla = get_throughput_sla(load_level)
    if not sla:
        return {"valid": True, "message": "No SLA defined"}
    
    results = {
        "rps_valid": rps >= sla.min_rps,
        "error_rate_valid": error_rate <= sla.max_error_rate,
    }
    
    results["valid"] = all(results.values())
    return results


# Performance targets summary
PERFORMANCE_SUMMARY = """
Resource Agent Performance Targets
===================================

Response Time SLAs:
  /health/           : P50 < 10ms,  P95 < 20ms,  P99 < 50ms,   Max < 100ms
  /system/metrics    : P50 < 100ms, P95 < 200ms, P99 < 500ms,  Max < 1000ms
  /analysis/         : P50 < 500ms, P95 < 1000ms, P99 < 2000ms, Max < 3000ms
  /lmcache/status    : P50 < 50ms,  P95 < 100ms, P99 < 200ms,  Max < 500ms
  /optimize/run      : P50 < 1000ms, P95 < 2000ms, P99 < 3000ms, Max < 5000ms

Throughput SLAs:
  Light Load  (10 users)  : >= 10 RPS,  Error Rate < 0.1%
  Medium Load (50 users)  : >= 40 RPS,  Error Rate < 0.5%
  Heavy Load  (100 users) : >= 80 RPS,  Error Rate < 1%
  Stress Test (200 users) : >= 100 RPS, Error Rate < 5%
"""


if __name__ == "__main__":
    print(PERFORMANCE_SUMMARY)
