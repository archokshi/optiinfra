"""
Azure Functions Cost Collector

Collects Functions costs, execution metrics, and identifies optimization opportunities.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from .base import AzureBaseCollector
from .cost_management_client import AzureCostManagementClient


class AzureFunctionsCollector(AzureBaseCollector):
    """Collector for Azure Functions"""
    
    def __init__(
        self,
        subscription_id: str,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        super().__init__(subscription_id, tenant_id, client_id, client_secret)
        self.web_client = WebSiteManagementClient(self.credentials, subscription_id)
        self.monitor_client = MonitorManagementClient(self.credentials, subscription_id)
        self.cost_client = AzureCostManagementClient(subscription_id, tenant_id, client_id, client_secret)
        
        # Thresholds
        self.memory_utilization_threshold = 50.0  # %
        
        self.logger = logging.getLogger(__name__)
    
    async def collect_all(
        self,
        lookback_days: int = 30
    ) -> Dict:
        """
        Collect all function app data and costs
        
        Args:
            lookback_days: Days to look back for metrics
            
        Returns:
            Dictionary with function app data, costs, and opportunities
        """
        start_date = datetime.utcnow() - timedelta(days=lookback_days)
        end_date = datetime.utcnow()
        
        self.logger.info(f"Collecting Azure Functions data for {lookback_days} days")
        
        # List all function apps
        function_apps = await self._list_function_apps()
        self.logger.info(f"Found {len(function_apps)} function apps")
        
        # Collect costs and metrics for each function app
        app_details = []
        for app in function_apps:
            try:
                app_data = await self._collect_function_data(
                    function_app=app,
                    start_date=start_date,
                    end_date=end_date
                )
                app_details.append(app_data)
            except Exception as e:
                self.logger.error(f"Failed to collect data for function app {app['name']}: {str(e)}")
        
        # Calculate totals
        total_apps = len(app_details)
        total_cost = sum(app.get('monthly_cost', 0) for app in app_details)
        
        # Identify opportunities
        opportunities = self._identify_opportunities(app_details)
        
        return {
            "total_function_apps": total_apps,
            "total_monthly_cost": total_cost,
            "function_apps": app_details,
            "opportunities": opportunities,
            "collected_at": datetime.utcnow().isoformat()
        }
    
    async def _list_function_apps(self) -> List[Dict]:
        """List all function apps in subscription"""
        function_apps = []
        
        try:
            apps = await self._make_request(
                self.web_client.web_apps,
                "list"
            )
            
            for app in apps:
                # Check if it's a function app
                if app.kind and 'functionapp' in app.kind.lower():
                    function_apps.append({
                        "id": app.id,
                        "name": app.name,
                        "resource_group": self._get_resource_group_from_id(app.id),
                        "location": app.location,
                        "kind": app.kind,
                        "state": app.state,
                        "tags": app.tags or {}
                    })
        except Exception as e:
            self.logger.error(f"Failed to list function apps: {str(e)}")
            raise
        
        return function_apps
    
    async def _collect_function_data(
        self,
        function_app: Dict,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Collect comprehensive data for a single function app"""
        
        # Get app service plan details
        plan_details = await self._get_plan_details(
            function_app['resource_group'],
            function_app['name']
        )
        
        # Get costs
        monthly_cost = await self._get_function_costs(function_app['id'], start_date, end_date)
        
        # Get metrics
        metrics = await self._get_function_metrics(function_app['id'], start_date, end_date)
        
        # Analyze utilization
        utilization_analysis = self._analyze_function_utilization(
            function_app,
            plan_details,
            metrics,
            monthly_cost
        )
        
        return {
            **function_app,
            "plan_type": plan_details.get('plan_type', 'Unknown'),
            "plan_sku": plan_details.get('sku', 'Unknown'),
            "monthly_cost": monthly_cost,
            "metrics": metrics,
            "utilization_analysis": utilization_analysis
        }
    
    async def _get_plan_details(self, resource_group: str, app_name: str) -> Dict:
        """Get app service plan details"""
        try:
            app = await self._make_request(
                self.web_client.web_apps,
                "get",
                resource_group_name=resource_group,
                name=app_name
            )
            
            if app.server_farm_id:
                plan_name = app.server_farm_id.split('/')[-1]
                plan_rg = self._get_resource_group_from_id(app.server_farm_id)
                
                plan = await self._make_request(
                    self.web_client.app_service_plans,
                    "get",
                    resource_group_name=plan_rg,
                    name=plan_name
                )
                
                return {
                    "plan_type": "Consumption" if plan.sku.tier == "Dynamic" else plan.sku.tier,
                    "sku": plan.sku.name,
                    "capacity": plan.sku.capacity
                }
        except Exception as e:
            self.logger.warning(f"Failed to get plan details for {app_name}: {str(e)}")
        
        return {}
    
    async def _get_function_costs(
        self,
        function_app_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Get costs for specific function app"""
        try:
            daily_costs = await self.cost_client.get_resource_costs(
                resource_id=function_app_id,
                start_date=start_date,
                end_date=end_date
            )
            
            total_cost = sum(day['cost'] for day in daily_costs)
            days = (end_date - start_date).days or 1
            monthly_cost = (total_cost / days) * 30
            
            return monthly_cost
        except Exception as e:
            self.logger.error(f"Failed to get costs for function app {function_app_id}: {str(e)}")
            return 0.0
    
    async def _get_function_metrics(
        self,
        function_app_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Get execution, memory, duration metrics from Azure Monitor"""
        metrics_to_collect = {
            "FunctionExecutionCount": "executions",
            "FunctionExecutionUnits": "execution_units",
            "MemoryWorkingSet": "memory",
            "Http5xx": "errors"
        }
        
        collected_metrics = {}
        
        for metric_name, metric_key in metrics_to_collect.items():
            try:
                metric_data = await self._make_request(
                    self.monitor_client.metrics,
                    "list",
                    resource_uri=function_app_id,
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
        
        return collected_metrics
    
    def _analyze_function_utilization(
        self,
        function_app: Dict,
        plan_details: Dict,
        metrics: Dict,
        monthly_cost: float
    ) -> Dict:
        """Analyze function utilization and identify issues"""
        analysis = {
            "is_over_provisioned": False,
            "recommendations": []
        }
        
        # Check memory utilization
        if 'memory' in metrics:
            memory_avg = metrics['memory']['average']
            # Assume 1.5 GB default allocation (1536 MB)
            memory_allocated = 1536
            memory_utilization = (memory_avg / memory_allocated) * 100
            
            if memory_utilization < self.memory_utilization_threshold:
                analysis['is_over_provisioned'] = True
                recommended_memory = int(memory_avg * 1.2)  # 20% buffer
                
                analysis['recommendations'].append({
                    "type": "memory_optimization",
                    "reason": f"Memory utilization is {memory_utilization:.1f}% (avg: {memory_avg:.0f}MB, allocated: {memory_allocated}MB)",
                    "action": f"Reduce memory allocation to {recommended_memory}MB",
                    "estimated_savings": monthly_cost * 0.30
                })
        
        # Check plan type optimization
        plan_type = plan_details.get('plan_type', 'Unknown')
        if 'executions' in metrics:
            total_executions = metrics['executions'].get('total', 0)
            
            # If high execution count on Consumption plan, consider Premium
            if plan_type == "Consumption" and total_executions > 10000000:  # 10M executions/month
                analysis['recommendations'].append({
                    "type": "plan_upgrade",
                    "reason": f"High execution count ({total_executions:,}) on Consumption plan",
                    "action": "Consider upgrading to Premium plan for better performance",
                    "estimated_savings": 0  # This is a performance optimization, not cost
                })
            
            # If low execution count on Premium/Dedicated, consider Consumption
            elif plan_type in ["Premium", "PremiumV2", "PremiumV3"] and total_executions < 1000000:  # 1M executions/month
                analysis['recommendations'].append({
                    "type": "plan_downgrade",
                    "reason": f"Low execution count ({total_executions:,}) on {plan_type} plan",
                    "action": "Consider downgrading to Consumption plan",
                    "estimated_savings": monthly_cost * 0.50
                })
        
        return analysis
    
    def _identify_opportunities(self, app_details: List[Dict]) -> List[Dict]:
        """Identify all optimization opportunities"""
        opportunities = []
        
        for app in app_details:
            if app.get('utilization_analysis', {}).get('recommendations'):
                for rec in app['utilization_analysis']['recommendations']:
                    opportunities.append({
                        "service": "Functions",
                        "resource_id": app['id'],
                        "resource_name": app['name'],
                        **rec
                    })
        
        return opportunities
