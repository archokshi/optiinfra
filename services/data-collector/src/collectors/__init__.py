"""Collectors for various cloud providers - Phase 6.6 Multi-Cloud with Generic Collector"""

from .base import BaseCollector

# Application collectors
from .application import VultrApplicationCollector
from .runpod import (
    RunPodApplicationCollector,
    RunPodCollectorSettings,
    RunPodCostCollector,
    RunPodPerformanceCollector,
    RunPodResourceCollector,
)

# Note: Vultr now uses Generic Collector (see generic_collector.py)
# Old dedicated Vultr collectors removed in Phase 6.6

# AWS collectors - Optional (requires boto3)
try:
    from .aws import AWSCostCollector, AWSPerformanceCollector, AWSResourceCollector
except ImportError:
    AWSCostCollector = None
    AWSPerformanceCollector = None
    AWSResourceCollector = None

# GCP collectors - Optional (requires google-cloud libraries)
try:
    from .gcp import GCPCostCollector, GCPPerformanceCollector, GCPResourceCollector
except ImportError:
    GCPCostCollector = None
    GCPPerformanceCollector = None
    GCPResourceCollector = None

# Azure collectors - Optional (requires azure libraries)
try:
    from .azure import AzureCostCollector, AzurePerformanceCollector, AzureResourceCollector
except ImportError:
    AzureCostCollector = None
    AzurePerformanceCollector = None
    AzureResourceCollector = None

__all__ = [
    "BaseCollector",
    # Application
    "VultrApplicationCollector",
    "RunPodApplicationCollector",
    # RunPod
    "RunPodCollectorSettings",
    "RunPodCostCollector",
    "RunPodPerformanceCollector",
    "RunPodResourceCollector",
    # AWS (Dedicated)
    "AWSCostCollector",
    "AWSPerformanceCollector",
    "AWSResourceCollector",
    # GCP (Dedicated)
    "GCPCostCollector",
    "GCPPerformanceCollector",
    "GCPResourceCollector",
    # Azure (Dedicated)
    "AzureCostCollector",
    "AzurePerformanceCollector",
    "AzureResourceCollector",
]
