"""
GCP Billing API Client

Wrapper for Google Cloud Billing API to retrieve cost and usage data.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.collectors.gcp.base import GCPBaseCollector
from src.collectors.gcp.bigquery_helper import BigQueryHelper

logger = logging.getLogger(__name__)


class BillingClient(GCPBaseCollector):
    """Client for GCP Cloud Billing API"""
    
    def __init__(
        self,
        billing_account_id: Optional[str] = None,
        billing_dataset: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Billing client.
        
        Args:
            billing_account_id: GCP billing account ID
            billing_dataset: BigQuery dataset with billing export
            **kwargs: Additional configuration
        """
        super().__init__(**kwargs)
        
        self.billing_account_id = billing_account_id
        self.billing_dataset = billing_dataset or 'billing_export'
        self.billing_table = f'gcp_billing_export_v1_{billing_account_id}' if billing_account_id else None
        
        # Initialize BigQuery helper if billing export is configured
        if self.billing_table:
            self.bq_helper = BigQueryHelper(
                billing_dataset=self.billing_dataset,
                billing_table=self.billing_table,
                project_id=self.project_id,
                credentials_path=self.credentials_path
            )
        else:
            self.bq_helper = None
            logger.warning("Billing export not configured, some features will be unavailable")
    
    def get_billing_info(self) -> Dict[str, Any]:
        """
        Retrieve billing account details.
        
        Returns:
            Billing account information
        """
        try:
            from google.cloud import billing_v1
            
            client = self.get_client(billing_v1.CloudBillingClient)
            
            if not self.billing_account_id:
                # List billing accounts
                accounts = list(client.list_billing_accounts())
                if accounts:
                    account = accounts[0]
                    self.billing_account_id = account.name.split('/')[-1]
                else:
                    raise ValueError("No billing accounts found")
            else:
                account_name = f"billingAccounts/{self.billing_account_id}"
                account = client.get_billing_account(name=account_name)
            
            return {
                'billing_account_id': self.billing_account_id,
                'display_name': account.display_name,
                'open': account.open_,
                'master_billing_account': account.master_billing_account
            }
            
        except Exception as e:
            logger.error(f"Failed to get billing info: {e}")
            return {}
    
    def query_costs(
        self,
        start_date: str,
        end_date: str,
        group_by: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Query costs from BigQuery billing export.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            group_by: Fields to group by
        
        Returns:
            Cost data
        """
        if not self.bq_helper:
            raise ValueError("BigQuery billing export not configured")
        
        try:
            # Get daily costs
            daily_costs = self.bq_helper.get_daily_costs(start_date, end_date)
            
            # Get service breakdown
            service_costs = self.bq_helper.get_service_costs(start_date, end_date)
            
            # Get project breakdown
            project_costs = self.bq_helper.get_project_costs(start_date, end_date)
            
            # Calculate total
            total_cost = sum(daily_costs.values())
            
            # Build daily breakdown
            daily_breakdown = [
                {'date': date, 'cost': cost}
                for date, cost in sorted(daily_costs.items())
            ]
            
            return {
                'time_period': {'start': start_date, 'end': end_date},
                'total_cost': round(total_cost, 2),
                'by_service': {k: round(v, 2) for k, v in service_costs.items()},
                'by_project': {k: round(v, 2) for k, v in project_costs.items()},
                'by_region': {},  # Would need region grouping
                'daily_breakdown': daily_breakdown
            }
            
        except Exception as e:
            logger.error(f"Failed to query costs: {e}")
            raise
    
    def get_cost_forecast(
        self,
        forecast_days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate cost forecast based on historical data.
        
        Args:
            forecast_days: Days to forecast
        
        Returns:
            Forecast data
        """
        try:
            # Get last 30 days of data
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
            start_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            daily_costs = self.bq_helper.get_daily_costs(start_date, end_date)
            
            if not daily_costs:
                return {}
            
            # Calculate average daily cost
            avg_daily_cost = sum(daily_costs.values()) / len(daily_costs)
            
            # Simple linear forecast
            projected_cost = avg_daily_cost * forecast_days
            
            # Add confidence interval (±10%)
            confidence_lower = projected_cost * 0.90
            confidence_upper = projected_cost * 1.10
            
            forecast_start = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
            forecast_end = (datetime.utcnow() + timedelta(days=forecast_days)).strftime('%Y-%m-%d')
            
            return {
                'time_period': {
                    'start': forecast_start,
                    'end': forecast_end
                },
                'projected_cost': round(projected_cost, 2),
                'confidence_interval': {
                    'lower': round(confidence_lower, 2),
                    'upper': round(confidence_upper, 2)
                },
                'average_daily_cost': round(avg_daily_cost, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate forecast: {e}")
            return {}
    
    def get_committed_use_discounts(self) -> Dict[str, Any]:
        """
        Get Committed Use Discount (CUD) information.
        
        Returns:
            CUD utilization data
        """
        try:
            # Query for CUD-related SKUs
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
            start_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            # This would need specific SKU filtering for CUDs
            # Simplified version here
            
            return {
                'time_period': {'start': start_date, 'end': end_date},
                'cud_coverage': 0.0,  # Would calculate from actual data
                'total_commitment': 0.0,
                'used_commitment': 0.0,
                'unused_commitment': 0.0
            }
            
        except Exception as e:
            logger.warning(f"Failed to get CUD info: {e}")
            return {}
    
    def get_sustained_use_discounts(self) -> Dict[str, Any]:
        """
        Get Sustained Use Discount (SUD) information.
        
        Returns:
            SUD data
        """
        try:
            # SUDs are automatically applied by GCP
            # Query credits to see SUD amounts
            
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
            start_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            return {
                'time_period': {'start': start_date, 'end': end_date},
                'total_sud_credits': 0.0,  # Would calculate from credits
                'sud_percentage': 0.0
            }
            
        except Exception as e:
            logger.warning(f"Failed to get SUD info: {e}")
            return {}
