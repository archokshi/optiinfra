"""
Vultr cost collector module.
"""

from .client import VultrClient, AsyncVultrClient, VultrAPIError
from .billing import VultrBillingCollector
from .instances import VultrInstanceCollector
from .analyzer import VultrCostAnalyzer

__all__ = [
    "VultrClient",
    "AsyncVultrClient",
    "VultrAPIError",
    "VultrBillingCollector",
    "VultrInstanceCollector",
    "VultrCostAnalyzer",
    "collect_vultr_metrics",
]


def collect_vultr_metrics(api_key: str) -> dict:
    """
    Convenience function to collect all Vultr metrics.
    
    Args:
        api_key: Vultr API key
    
    Returns:
        Complete cost metrics
    """
    # Initialize client
    client = VultrClient(api_key=api_key)
    
    # Initialize collectors
    billing_collector = VultrBillingCollector(client)
    instance_collector = VultrInstanceCollector(client)
    analyzer = VultrCostAnalyzer()
    
    # Collect data
    account_info = billing_collector.collect_account_info()
    pending_charges = billing_collector.collect_pending_charges()
    instances = instance_collector.collect_compute_instances()
    bare_metals = instance_collector.collect_bare_metal_servers()
    invoices = billing_collector.collect_invoices()
    
    # Combine instances
    all_instances = instances + bare_metals
    
    # Analyze
    cost_analysis = analyzer.analyze_costs(
        account_info=account_info,
        pending_charges=pending_charges,
        instances=all_instances,
        invoices=invoices
    )
    
    return {
        "account": account_info,
        "pending_charges": pending_charges,
        "instances": all_instances,
        "cost_analysis": cost_analysis,
        "collected_at": cost_analysis["timestamp"]
    }
