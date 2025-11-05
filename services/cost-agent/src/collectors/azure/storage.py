"""
Azure Storage Cost Collector

Collects Storage costs, usage metrics, and identifies optimization opportunities.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from .base import AzureBaseCollector
from .cost_management_client import AzureCostManagementClient


class AzureStorageCollector(AzureBaseCollector):
    """Collector for Azure Storage"""
    
    def __init__(
        self,
        subscription_id: str,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        super().__init__(subscription_id, tenant_id, client_id, client_secret)
        self.storage_client = StorageManagementClient(self.credentials, subscription_id)
        self.monitor_client = MonitorManagementClient(self.credentials, subscription_id)
        self.cost_client = AzureCostManagementClient(subscription_id, tenant_id, client_id, client_secret)
        
        self.logger = logging.getLogger(__name__)
    
    async def collect_all(
        self,
        lookback_days: int = 30
    ) -> Dict:
        """
        Collect all storage account data and costs
        
        Args:
            lookback_days: Days to look back for metrics
            
        Returns:
            Dictionary with storage account data, costs, and opportunities
        """
        start_date = datetime.utcnow() - timedelta(days=lookback_days)
        end_date = datetime.utcnow()
        
        self.logger.info(f"Collecting Azure Storage data for {lookback_days} days")
        
        # List all storage accounts
        storage_accounts = await self._list_storage_accounts()
        self.logger.info(f"Found {len(storage_accounts)} storage accounts")
        
        # Collect costs and metrics for each storage account
        account_details = []
        for account in storage_accounts:
            try:
                account_data = await self._collect_storage_data(
                    storage_account=account,
                    start_date=start_date,
                    end_date=end_date
                )
                account_details.append(account_data)
            except Exception as e:
                self.logger.error(f"Failed to collect data for storage account {account['name']}: {str(e)}")
        
        # Calculate totals
        total_accounts = len(account_details)
        total_cost = sum(acc.get('monthly_cost', 0) for acc in account_details)
        
        # Identify opportunities
        opportunities = self._identify_opportunities(account_details)
        
        return {
            "total_storage_accounts": total_accounts,
            "total_monthly_cost": total_cost,
            "storage_accounts": account_details,
            "opportunities": opportunities,
            "collected_at": datetime.utcnow().isoformat()
        }
    
    async def _list_storage_accounts(self) -> List[Dict]:
        """List all storage accounts in subscription"""
        storage_accounts = []
        
        try:
            accounts = await self._make_request(
                self.storage_client.storage_accounts,
                "list"
            )
            
            for account in accounts:
                storage_accounts.append({
                    "id": account.id,
                    "name": account.name,
                    "resource_group": self._get_resource_group_from_id(account.id),
                    "location": account.location,
                    "sku": account.sku.name if account.sku else "Unknown",
                    "kind": account.kind,
                    "access_tier": account.access_tier if hasattr(account, 'access_tier') else None,
                    "tags": account.tags or {}
                })
        except Exception as e:
            self.logger.error(f"Failed to list storage accounts: {str(e)}")
            raise
        
        return storage_accounts
    
    async def _collect_storage_data(
        self,
        storage_account: Dict,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Collect comprehensive data for a single storage account"""
        
        # Get costs
        monthly_cost = await self._get_storage_costs(storage_account['id'], start_date, end_date)
        
        # Get metrics
        metrics = await self._get_storage_metrics(storage_account['id'], start_date, end_date)
        
        # Check lifecycle policies
        has_lifecycle_policy = await self._check_lifecycle_policy(
            storage_account['resource_group'],
            storage_account['name']
        )
        
        # Analyze utilization
        utilization_analysis = self._analyze_storage_utilization(
            storage_account,
            metrics,
            monthly_cost,
            has_lifecycle_policy
        )
        
        return {
            **storage_account,
            "monthly_cost": monthly_cost,
            "metrics": metrics,
            "has_lifecycle_policy": has_lifecycle_policy,
            "utilization_analysis": utilization_analysis
        }
    
    async def _get_storage_costs(
        self,
        storage_account_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Get costs for specific storage account"""
        try:
            daily_costs = await self.cost_client.get_resource_costs(
                resource_id=storage_account_id,
                start_date=start_date,
                end_date=end_date
            )
            
            total_cost = sum(day['cost'] for day in daily_costs)
            days = (end_date - start_date).days or 1
            monthly_cost = (total_cost / days) * 30
            
            return monthly_cost
        except Exception as e:
            self.logger.error(f"Failed to get costs for storage account {storage_account_id}: {str(e)}")
            return 0.0
    
    async def _get_storage_metrics(
        self,
        storage_account_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Get capacity, transactions, egress metrics from Azure Monitor"""
        metrics_to_collect = {
            "UsedCapacity": "capacity",
            "Transactions": "transactions",
            "Egress": "egress",
            "SuccessServerLatency": "latency"
        }
        
        collected_metrics = {}
        
        for metric_name, metric_key in metrics_to_collect.items():
            try:
                metric_data = await self._make_request(
                    self.monitor_client.metrics,
                    "list",
                    resource_uri=storage_account_id,
                    timespan=f"{start_date.isoformat()}/{end_date.isoformat()}",
                    interval='PT1H',
                    metricnames=metric_name,
                    aggregation='Average,Total'
                )
                
                values = []
                total = 0
                for item in metric_data.value:
                    for timeseries in item.timeseries:
                        for data in timeseries.data:
                            if data.average is not None:
                                values.append(data.average)
                            if data.total is not None:
                                total += data.total
                
                if values or total > 0:
                    collected_metrics[metric_key] = {
                        "average": sum(values) / len(values) if values else 0,
                        "total": total
                    }
            except Exception as e:
                self.logger.warning(f"Failed to collect metric {metric_name}: {str(e)}")
        
        # Convert capacity from bytes to GB
        if 'capacity' in collected_metrics:
            collected_metrics['capacity']['average_gb'] = collected_metrics['capacity']['average'] / (1024**3)
            collected_metrics['capacity']['total_gb'] = collected_metrics['capacity']['total'] / (1024**3)
        
        # Convert egress from bytes to GB
        if 'egress' in collected_metrics:
            collected_metrics['egress']['total_gb'] = collected_metrics['egress']['total'] / (1024**3)
        
        return collected_metrics
    
    async def _check_lifecycle_policy(
        self,
        resource_group: str,
        account_name: str
    ) -> bool:
        """Check if lifecycle management policy is configured"""
        try:
            policy = await self._make_request(
                self.storage_client.management_policies,
                "get",
                resource_group_name=resource_group,
                account_name=account_name,
                management_policy_name="default"
            )
            
            return policy is not None and hasattr(policy, 'policy')
        except Exception as e:
            # Policy doesn't exist or error occurred
            return False
    
    def _analyze_storage_utilization(
        self,
        storage_account: Dict,
        metrics: Dict,
        monthly_cost: float,
        has_lifecycle_policy: bool
    ) -> Dict:
        """Analyze storage utilization and identify issues"""
        analysis = {
            "lifecycle_policy_missing": not has_lifecycle_policy,
            "recommendations": []
        }
        
        # Check for lifecycle policy
        if not has_lifecycle_policy and monthly_cost > 10:
            analysis['recommendations'].append({
                "type": "lifecycle_policy",
                "reason": "No lifecycle management policy configured",
                "action": "Implement lifecycle policy to automatically tier blobs (Hot → Cool → Archive)",
                "estimated_savings": monthly_cost * 0.50
            })
        
        # Check access tier optimization
        current_tier = storage_account.get('access_tier')
        if current_tier == 'Hot' and 'transactions' in metrics:
            total_transactions = metrics['transactions'].get('total', 0)
            days = 30
            transactions_per_day = total_transactions / days
            
            # If low transaction rate, recommend Cool tier
            if transactions_per_day < 1000:
                analysis['recommendations'].append({
                    "type": "tier_migration",
                    "reason": f"Low transaction rate ({transactions_per_day:.0f}/day) on Hot tier",
                    "action": "Migrate to Cool tier",
                    "estimated_savings": monthly_cost * 0.50
                })
        
        # Check for unused storage account
        if 'capacity' in metrics:
            capacity_gb = metrics['capacity'].get('average_gb', 0)
            
            if capacity_gb < 0.1:  # Less than 100MB
                analysis['recommendations'].append({
                    "type": "unused_storage",
                    "reason": f"Storage account has minimal data ({capacity_gb:.2f} GB)",
                    "action": "Consider deleting unused storage account",
                    "estimated_savings": monthly_cost * 0.90
                })
        
        # Check egress costs
        if 'egress' in metrics:
            egress_gb = metrics['egress'].get('total_gb', 0)
            
            if egress_gb > 1000:  # More than 1TB egress
                analysis['recommendations'].append({
                    "type": "egress_optimization",
                    "reason": f"High egress traffic ({egress_gb:.0f} GB)",
                    "action": "Review data access patterns and consider CDN or caching",
                    "estimated_savings": monthly_cost * 0.20
                })
        
        return analysis
    
    def _identify_opportunities(self, account_details: List[Dict]) -> List[Dict]:
        """Identify all optimization opportunities"""
        opportunities = []
        
        for account in account_details:
            if account.get('utilization_analysis', {}).get('recommendations'):
                for rec in account['utilization_analysis']['recommendations']:
                    opportunities.append({
                        "service": "Storage",
                        "resource_id": account['id'],
                        "resource_name": account['name'],
                        **rec
                    })
        
        return opportunities
