"""
BigQuery Helper for GCP Cost Queries

Helper class for querying GCP billing export data in BigQuery.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from google.cloud import bigquery

from src.collectors.gcp.base import GCPBaseCollector

logger = logging.getLogger(__name__)


class BigQueryHelper(GCPBaseCollector):
    """Helper for querying GCP billing data from BigQuery"""
    
    def __init__(
        self,
        billing_dataset: str,
        billing_table: str,
        **kwargs
    ):
        """
        Initialize BigQuery helper.
        
        Args:
            billing_dataset: BigQuery dataset with billing export
            billing_table: Billing export table name
            **kwargs: Additional configuration
        """
        super().__init__(**kwargs)
        
        self.billing_dataset = billing_dataset
        self.billing_table = billing_table
        self.bq_client = self.get_client(bigquery.Client)
        
        logger.info(f"Initialized BigQuery helper for {billing_dataset}.{billing_table}")
    
    def execute_billing_query(
        self,
        start_date: str,
        end_date: str,
        group_by: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute billing query with grouping.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            group_by: Fields to group by (service, project, region, sku)
        
        Returns:
            Query results
        """
        if group_by is None:
            group_by = ['service', 'project_id']
        
        # Build query
        select_fields = ['DATE(usage_start_time) as date']
        select_fields.extend(group_by)
        select_fields.extend([
            'SUM(cost) as cost',
            'SUM(IFNULL((SELECT SUM(amount) FROM UNNEST(credits)), 0)) as credits',
            'SUM(cost) + SUM(IFNULL((SELECT SUM(amount) FROM UNNEST(credits)), 0)) as total_cost'
        ])
        
        query = f"""
        SELECT
            {', '.join(select_fields)}
        FROM `{self.project_id}.{self.billing_dataset}.{self.billing_table}`
        WHERE DATE(usage_start_time) BETWEEN @start_date AND @end_date
        GROUP BY date, {', '.join(group_by)}
        ORDER BY date DESC, total_cost DESC
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
            ]
        )
        
        try:
            self.log_api_call()
            query_job = self.bq_client.query(query, job_config=job_config)
            results = query_job.result()
            
            rows = []
            for row in results:
                rows.append(dict(row))
            
            logger.info(f"Query returned {len(rows)} rows")
            return rows
            
        except Exception as e:
            logger.error(f"BigQuery query failed: {e}")
            raise
    
    def get_daily_costs(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, float]:
        """
        Get daily cost breakdown.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            Dict of date -> cost
        """
        query = f"""
        SELECT
            DATE(usage_start_time) as date,
            SUM(cost) + SUM(IFNULL((SELECT SUM(amount) FROM UNNEST(credits)), 0)) as total_cost
        FROM `{self.project_id}.{self.billing_dataset}.{self.billing_table}`
        WHERE DATE(usage_start_time) BETWEEN @start_date AND @end_date
        GROUP BY date
        ORDER BY date DESC
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
            ]
        )
        
        try:
            self.log_api_call()
            query_job = self.bq_client.query(query, job_config=job_config)
            results = query_job.result()
            
            daily_costs = {}
            for row in results:
                daily_costs[str(row['date'])] = float(row['total_cost'])
            
            return daily_costs
            
        except Exception as e:
            logger.error(f"Failed to get daily costs: {e}")
            return {}
    
    def get_service_costs(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, float]:
        """
        Get costs grouped by service.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            Dict of service -> cost
        """
        query = f"""
        SELECT
            service.description as service,
            SUM(cost) + SUM(IFNULL((SELECT SUM(amount) FROM UNNEST(credits)), 0)) as total_cost
        FROM `{self.project_id}.{self.billing_dataset}.{self.billing_table}`
        WHERE DATE(usage_start_time) BETWEEN @start_date AND @end_date
        GROUP BY service
        ORDER BY total_cost DESC
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
            ]
        )
        
        try:
            self.log_api_call()
            query_job = self.bq_client.query(query, job_config=job_config)
            results = query_job.result()
            
            service_costs = {}
            for row in results:
                service_costs[row['service']] = float(row['total_cost'])
            
            return service_costs
            
        except Exception as e:
            logger.error(f"Failed to get service costs: {e}")
            return {}
    
    def get_project_costs(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, float]:
        """
        Get costs grouped by project.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            Dict of project_id -> cost
        """
        query = f"""
        SELECT
            project.id as project_id,
            SUM(cost) + SUM(IFNULL((SELECT SUM(amount) FROM UNNEST(credits)), 0)) as total_cost
        FROM `{self.project_id}.{self.billing_dataset}.{self.billing_table}`
        WHERE DATE(usage_start_time) BETWEEN @start_date AND @end_date
        GROUP BY project_id
        ORDER BY total_cost DESC
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
            ]
        )
        
        try:
            self.log_api_call()
            query_job = self.bq_client.query(query, job_config=job_config)
            results = query_job.result()
            
            project_costs = {}
            for row in results:
                project_costs[row['project_id']] = float(row['total_cost'])
            
            return project_costs
            
        except Exception as e:
            logger.error(f"Failed to get project costs: {e}")
            return {}
    
    def get_sku_details(
        self,
        start_date: str,
        end_date: str,
        service: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get detailed SKU-level costs.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            service: Optional service filter
            limit: Max results
        
        Returns:
            List of SKU cost details
        """
        where_clause = "WHERE DATE(usage_start_time) BETWEEN @start_date AND @end_date"
        if service:
            where_clause += " AND service.description = @service"
        
        query = f"""
        SELECT
            service.description as service,
            sku.description as sku,
            SUM(usage.amount) as usage_amount,
            usage.unit as usage_unit,
            SUM(cost) as cost,
            SUM(IFNULL((SELECT SUM(amount) FROM UNNEST(credits)), 0)) as credits
        FROM `{self.project_id}.{self.billing_dataset}.{self.billing_table}`
        {where_clause}
        GROUP BY service, sku, usage_unit
        ORDER BY cost DESC
        LIMIT {limit}
        """
        
        query_params = [
            bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
            bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
        ]
        
        if service:
            query_params.append(
                bigquery.ScalarQueryParameter("service", "STRING", service)
            )
        
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        
        try:
            self.log_api_call()
            query_job = self.bq_client.query(query, job_config=job_config)
            results = query_job.result()
            
            sku_details = []
            for row in results:
                sku_details.append(dict(row))
            
            return sku_details
            
        except Exception as e:
            logger.error(f"Failed to get SKU details: {e}")
            return []
