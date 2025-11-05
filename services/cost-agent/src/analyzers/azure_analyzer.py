"""
Azure Cost Analyzer

Aggregates cost data from all Azure collectors, detects anomalies, and prioritizes opportunities.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import statistics
from ..collectors.azure import (
    AzureCostManagementClient,
    AzureVirtualMachinesCollector,
    AzureSQLDatabaseCollector,
    AzureFunctionsCollector,
    AzureStorageCollector
)


class AzureCostAnalyzer:
    """Analyzer for Azure cost data"""
    
    def __init__(
        self,
        subscription_id: str,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        self.subscription_id = subscription_id
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        
        # Initialize collectors
        self.cost_client = AzureCostManagementClient(subscription_id, tenant_id, client_id, client_secret)
        self.vm_collector = AzureVirtualMachinesCollector(subscription_id, tenant_id, client_id, client_secret)
        self.sql_collector = AzureSQLDatabaseCollector(subscription_id, tenant_id, client_id, client_secret)
        self.functions_collector = AzureFunctionsCollector(subscription_id, tenant_id, client_id, client_secret)
        self.storage_collector = AzureStorageCollector(subscription_id, tenant_id, client_id, client_secret)
        
        self.logger = logging.getLogger(__name__)
    
    async def analyze(
        self,
        lookback_days: int = 30,
        include_utilization: bool = True
    ) -> Dict:
        """
        Perform comprehensive cost analysis
        
        Args:
            lookback_days: Days to look back for analysis
            include_utilization: Whether to collect utilization metrics
            
        Returns:
            Complete analysis dictionary
        """
        start_date = datetime.utcnow() - timedelta(days=lookback_days)
        end_date = datetime.utcnow()
        
        self.logger.info(f"Starting Azure cost analysis for subscription {self.subscription_id}")
        
        # Get overall costs
        subscription_costs = await self.cost_client.get_subscription_costs(
            start_date=start_date,
            end_date=end_date,
            granularity="Daily"
        )
        
        costs_by_service = await self.cost_client.get_costs_by_service(
            start_date=start_date,
            end_date=end_date
        )
        
        costs_by_resource_group = await self.cost_client.get_costs_by_resource_group(
            start_date=start_date,
            end_date=end_date
        )
        
        costs_by_location = await self.cost_client.get_costs_by_location(
            start_date=start_date,
            end_date=end_date
        )
        
        # Collect service-specific data
        vm_data = await self.vm_collector.collect_all(
            lookback_days=lookback_days,
            include_utilization=include_utilization
        )
        
        sql_data = await self.sql_collector.collect_all(
            lookback_days=lookback_days
        )
        
        functions_data = await self.functions_collector.collect_all(
            lookback_days=lookback_days
        )
        
        storage_data = await self.storage_collector.collect_all(
            lookback_days=lookback_days
        )
        
        # Aggregate costs
        cost_breakdown = self._aggregate_costs(
            subscription_costs,
            costs_by_service,
            costs_by_resource_group,
            costs_by_location
        )
        
        # Collect all opportunities
        all_opportunities = self._collect_opportunities(
            vm_data,
            sql_data,
            functions_data,
            storage_data
        )
        
        # Prioritize opportunities
        prioritized_opportunities = self._prioritize_opportunities(all_opportunities)
        
        # Detect anomalies
        anomalies = self._detect_anomalies(subscription_costs.get('daily_costs', []))
        
        # Generate forecast
        forecast = self._forecast_costs(subscription_costs.get('daily_costs', []))
        
        # Calculate total waste
        total_waste = self._calculate_total_waste(prioritized_opportunities)
        
        return {
            "subscription_id": self.subscription_id,
            "time_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_cost": subscription_costs.get('total_cost', 0),
            "cost_breakdown": cost_breakdown,
            "services": {
                "virtual_machines": {
                    "total_vms": vm_data.get('total_vms', 0),
                    "running_vms": vm_data.get('running_vms', 0),
                    "total_monthly_cost": vm_data.get('total_monthly_cost', 0),
                    "idle_vms": sum(1 for vm in vm_data.get('vms', []) 
                                   if vm.get('utilization_analysis', {}).get('is_idle')),
                    "underutilized_vms": sum(1 for vm in vm_data.get('vms', []) 
                                            if vm.get('utilization_analysis', {}).get('is_underutilized')),
                    "spot_eligible": sum(1 for vm in vm_data.get('vms', []) 
                                        if vm.get('utilization_analysis', {}).get('spot_eligible')),
                    "unattached_disks": len(vm_data.get('unattached_disks', []))
                },
                "sql_database": {
                    "total_databases": sql_data.get('total_databases', 0),
                    "total_monthly_cost": sql_data.get('total_monthly_cost', 0),
                    "idle_databases": sum(1 for db in sql_data.get('databases', []) 
                                         if db.get('utilization_analysis', {}).get('is_idle'))
                },
                "functions": {
                    "total_function_apps": functions_data.get('total_function_apps', 0),
                    "total_monthly_cost": functions_data.get('total_monthly_cost', 0),
                    "over_provisioned": sum(1 for app in functions_data.get('function_apps', []) 
                                           if app.get('utilization_analysis', {}).get('is_over_provisioned'))
                },
                "storage": {
                    "total_storage_accounts": storage_data.get('total_storage_accounts', 0),
                    "total_monthly_cost": storage_data.get('total_monthly_cost', 0),
                    "missing_lifecycle_policy": sum(1 for acc in storage_data.get('storage_accounts', []) 
                                                   if acc.get('utilization_analysis', {}).get('lifecycle_policy_missing'))
                }
            },
            "optimization": {
                "total_opportunities": len(prioritized_opportunities),
                "total_potential_savings": total_waste,
                "opportunities": prioritized_opportunities
            },
            "anomalies": anomalies,
            "forecast": forecast,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def _aggregate_costs(
        self,
        subscription_costs: Dict,
        costs_by_service: Dict,
        costs_by_resource_group: Dict,
        costs_by_location: Dict
    ) -> Dict:
        """Aggregate costs from different dimensions"""
        return {
            "by_service": costs_by_service,
            "by_resource_group": costs_by_resource_group,
            "by_location": costs_by_location,
            "daily": subscription_costs.get('daily_costs', [])
        }
    
    def _collect_opportunities(
        self,
        vm_data: Dict,
        sql_data: Dict,
        functions_data: Dict,
        storage_data: Dict
    ) -> List[Dict]:
        """Collect all optimization opportunities from all services"""
        opportunities = []
        
        opportunities.extend(vm_data.get('opportunities', []))
        opportunities.extend(sql_data.get('opportunities', []))
        opportunities.extend(functions_data.get('opportunities', []))
        opportunities.extend(storage_data.get('opportunities', []))
        
        return opportunities
    
    def _prioritize_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Prioritize opportunities by savings potential and implementation effort
        
        Priority levels:
        - high: savings > $500/month, easy implementation
        - medium: savings $100-$500/month
        - low: savings < $100/month
        """
        for opp in opportunities:
            savings = opp.get('estimated_savings', 0)
            
            if savings > 500:
                opp['priority'] = 'high'
                opp['confidence'] = 0.90
            elif savings > 100:
                opp['priority'] = 'medium'
                opp['confidence'] = 0.85
            else:
                opp['priority'] = 'low'
                opp['confidence'] = 0.80
            
            # Adjust confidence based on opportunity type
            if opp.get('type') == 'idle_vm':
                opp['confidence'] = 0.95
            elif opp.get('type') == 'idle_database':
                opp['confidence'] = 0.95
            elif opp.get('type') == 'unattached_disk':
                opp['confidence'] = 0.98
        
        # Sort by savings (descending)
        return sorted(opportunities, key=lambda x: x.get('estimated_savings', 0), reverse=True)
    
    def _detect_anomalies(self, daily_costs: List[Dict]) -> List[Dict]:
        """
        Detect cost anomalies using statistical analysis
        
        An anomaly is a day where cost is > 1.5x the baseline (mean)
        """
        anomalies = []
        
        if len(daily_costs) < 7:
            return anomalies
        
        costs = [day['cost'] for day in daily_costs]
        mean = statistics.mean(costs)
        stdev = statistics.stdev(costs) if len(costs) > 1 else 0
        
        threshold = 1.5  # 1.5x standard deviations
        
        for day in daily_costs:
            if stdev > 0:
                z_score = (day['cost'] - mean) / stdev
                
                if abs(z_score) > threshold:
                    anomalies.append({
                        "date": day['date'],
                        "cost": day['cost'],
                        "baseline": mean,
                        "deviation": z_score,
                        "severity": "high" if abs(z_score) > 2 else "medium"
                    })
        
        return anomalies
    
    def _forecast_costs(self, daily_costs: List[Dict], forecast_days: int = 30) -> Dict:
        """
        Generate cost forecast using simple linear regression
        
        Args:
            daily_costs: Historical daily costs
            forecast_days: Number of days to forecast
            
        Returns:
            Forecast dictionary with projected cost and confidence interval
        """
        if len(daily_costs) < 7:
            return {
                "next_30_days": 0,
                "confidence_interval": {"lower": 0, "upper": 0}
            }
        
        costs = [day['cost'] for day in daily_costs]
        mean_daily_cost = statistics.mean(costs)
        stdev_daily_cost = statistics.stdev(costs) if len(costs) > 1 else 0
        
        # Simple forecast: average daily cost * forecast days
        projected_cost = mean_daily_cost * forecast_days
        
        # Confidence interval: ±1 standard deviation
        lower_bound = projected_cost - (stdev_daily_cost * forecast_days)
        upper_bound = projected_cost + (stdev_daily_cost * forecast_days)
        
        return {
            "next_30_days": projected_cost,
            "confidence_interval": {
                "lower": max(0, lower_bound),
                "upper": upper_bound
            },
            "average_daily_cost": mean_daily_cost
        }
    
    def _calculate_total_waste(self, opportunities: List[Dict]) -> float:
        """Calculate total potential savings from all opportunities"""
        return sum(opp.get('estimated_savings', 0) for opp in opportunities)
