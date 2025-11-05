"""
Azure Cost Management Client

Interfaces with Azure Cost Management API to retrieve cost and usage data.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.costmanagement.models import (
    QueryDefinition,
    QueryTimePeriod,
    QueryDataset,
    QueryAggregation,
    QueryGrouping,
    TimeframeType
)
from .base import AzureBaseCollector


class AzureCostManagementClient(AzureBaseCollector):
    """Client for Azure Cost Management API"""
    
    def __init__(
        self,
        subscription_id: str,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        super().__init__(subscription_id, tenant_id, client_id, client_secret)
        self.cost_client = CostManagementClient(self.credentials)
        self.scope = f"/subscriptions/{subscription_id}"
        self.logger = logging.getLogger(__name__)
    
    async def get_subscription_costs(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str = "Daily"
    ) -> Dict:
        """
        Get total subscription costs for date range
        
        Args:
            start_date: Start date
            end_date: End date
            granularity: Daily, Monthly, or None
            
        Returns:
            Cost data dictionary with total_cost, currency, daily_costs
        """
        query = self._build_cost_query(
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
            grouping=None
        )
        
        try:
            result = await self._make_request(
                self.cost_client.query,
                "usage",
                scope=self.scope,
                parameters=query
            )
            
            return self._parse_cost_result(result)
        except Exception as e:
            self.logger.error(f"Failed to get subscription costs: {str(e)}")
            return self._handle_error(e)
    
    async def get_costs_by_service(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, float]:
        """
        Get cost breakdown by Azure service
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary mapping service name to cost
        """
        query = self._build_cost_query(
            start_date=start_date,
            end_date=end_date,
            granularity=None,
            grouping=[QueryGrouping(type="Dimension", name="ServiceName")]
        )
        
        try:
            result = await self._make_request(
                self.cost_client.query,
                "usage",
                scope=self.scope,
                parameters=query
            )
            
            return self._parse_grouped_costs(result, "ServiceName")
        except Exception as e:
            self.logger.error(f"Failed to get costs by service: {str(e)}")
            return {}
    
    async def get_costs_by_resource_group(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, float]:
        """
        Get cost breakdown by resource group
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary mapping resource group to cost
        """
        query = self._build_cost_query(
            start_date=start_date,
            end_date=end_date,
            granularity=None,
            grouping=[QueryGrouping(type="Dimension", name="ResourceGroupName")]
        )
        
        try:
            result = await self._make_request(
                self.cost_client.query,
                "usage",
                scope=self.scope,
                parameters=query
            )
            
            return self._parse_grouped_costs(result, "ResourceGroupName")
        except Exception as e:
            self.logger.error(f"Failed to get costs by resource group: {str(e)}")
            return {}
    
    async def get_costs_by_location(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, float]:
        """
        Get cost breakdown by location
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary mapping location to cost
        """
        query = self._build_cost_query(
            start_date=start_date,
            end_date=end_date,
            granularity=None,
            grouping=[QueryGrouping(type="Dimension", name="ResourceLocation")]
        )
        
        try:
            result = await self._make_request(
                self.cost_client.query,
                "usage",
                scope=self.scope,
                parameters=query
            )
            
            return self._parse_grouped_costs(result, "ResourceLocation")
        except Exception as e:
            self.logger.error(f"Failed to get costs by location: {str(e)}")
            return {}
    
    async def get_resource_costs(
        self,
        resource_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """
        Get costs for specific resource
        
        Args:
            resource_id: Azure resource ID
            start_date: Start date
            end_date: End date
            
        Returns:
            List of daily cost records
        """
        query = self._build_cost_query(
            start_date=start_date,
            end_date=end_date,
            granularity="Daily",
            filter_expression=f"ResourceId eq '{resource_id}'"
        )
        
        try:
            result = await self._make_request(
                self.cost_client.query,
                "usage",
                scope=self.scope,
                parameters=query
            )
            
            return self._parse_daily_costs(result)
        except Exception as e:
            self.logger.error(f"Failed to get resource costs for {resource_id}: {str(e)}")
            return []
    
    def _build_cost_query(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: Optional[str],
        grouping: Optional[List[QueryGrouping]] = None,
        filter_expression: Optional[str] = None
    ) -> QueryDefinition:
        """
        Build cost query definition
        
        Args:
            start_date: Start date
            end_date: End date
            granularity: Daily, Monthly, or None
            grouping: List of grouping dimensions
            filter_expression: Filter expression
            
        Returns:
            QueryDefinition object
        """
        # Build dataset
        dataset = QueryDataset(
            granularity=granularity,
            aggregation={
                "totalCost": QueryAggregation(
                    name="Cost",
                    function="Sum"
                )
            }
        )
        
        if grouping:
            dataset.grouping = grouping
        
        if filter_expression:
            dataset.filter = filter_expression
        
        # Build query
        query = QueryDefinition(
            type="Usage",
            timeframe=TimeframeType.CUSTOM,
            time_period=QueryTimePeriod(
                from_property=start_date.strftime("%Y-%m-%dT00:00:00Z"),
                to=end_date.strftime("%Y-%m-%dT23:59:59Z")
            ),
            dataset=dataset
        )
        
        return query
    
    def _parse_cost_result(self, result) -> Dict:
        """
        Parse cost query result
        
        Args:
            result: Query result from Cost Management API
            
        Returns:
            Dictionary with total_cost, currency, row_count
        """
        total_cost = 0.0
        currency = "USD"
        daily_costs = []
        
        if hasattr(result, 'rows') and result.rows:
            # Find column indices
            cost_index = None
            date_index = None
            
            for i, col in enumerate(result.columns):
                if col.name == "Cost":
                    cost_index = i
                elif col.name == "UsageDate":
                    date_index = i
                elif col.name == "Currency":
                    if result.rows:
                        currency = result.rows[0][i]
            
            # Sum costs
            for row in result.rows:
                if cost_index is not None:
                    cost = float(row[cost_index])
                    total_cost += cost
                    
                    if date_index is not None:
                        daily_costs.append({
                            "date": row[date_index],
                            "cost": cost
                        })
        
        return {
            "total_cost": total_cost,
            "currency": currency,
            "row_count": len(result.rows) if hasattr(result, 'rows') else 0,
            "daily_costs": daily_costs
        }
    
    def _parse_grouped_costs(self, result, group_by: str) -> Dict[str, float]:
        """
        Parse grouped cost results
        
        Args:
            result: Query result from Cost Management API
            group_by: Dimension name used for grouping
            
        Returns:
            Dictionary mapping group name to cost
        """
        costs = {}
        
        if hasattr(result, 'rows') and result.rows:
            # Find column indices
            group_index = None
            cost_index = None
            
            for i, col in enumerate(result.columns):
                if col.name == group_by:
                    group_index = i
                elif col.name == "Cost":
                    cost_index = i
            
            if group_index is not None and cost_index is not None:
                for row in result.rows:
                    group_name = row[group_index]
                    cost = float(row[cost_index])
                    costs[group_name] = costs.get(group_name, 0.0) + cost
        
        return costs
    
    def _parse_daily_costs(self, result) -> List[Dict]:
        """
        Parse daily cost results
        
        Args:
            result: Query result from Cost Management API
            
        Returns:
            List of daily cost dictionaries
        """
        daily_costs = []
        
        if hasattr(result, 'rows') and result.rows:
            # Find column indices
            date_index = None
            cost_index = None
            
            for i, col in enumerate(result.columns):
                if col.name == "UsageDate":
                    date_index = i
                elif col.name == "Cost":
                    cost_index = i
            
            if date_index is not None and cost_index is not None:
                for row in result.rows:
                    daily_costs.append({
                        "date": row[date_index],
                        "cost": float(row[cost_index])
                    })
        
        return daily_costs
