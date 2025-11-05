"""
GCP Cost Analyzer

Aggregates data from all GCP collectors and performs comprehensive cost analysis.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.collectors.gcp.billing_client import BillingClient
from src.collectors.gcp.compute_engine import ComputeEngineCostCollector
from src.collectors.gcp.cloud_sql import CloudSQLCostCollector
from src.collectors.gcp.cloud_functions import CloudFunctionsCostCollector
from src.collectors.gcp.cloud_storage import CloudStorageCostCollector

logger = logging.getLogger(__name__)


class GCPCostAnalyzer:
    """Comprehensive GCP cost analyzer"""
    
    def __init__(
        self,
        project_id: str,
        credentials_path: Optional[str] = None,
        billing_account_id: Optional[str] = None,
        billing_dataset: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize GCP cost analyzer.
        
        Args:
            project_id: GCP project ID
            credentials_path: Path to service account credentials
            billing_account_id: Billing account ID
            billing_dataset: BigQuery billing dataset
            **kwargs: Additional configuration
        """
        self.project_id = project_id
        self.credentials_path = credentials_path
        
        # Initialize collectors
        collector_kwargs = {
            'project_id': project_id,
            'credentials_path': credentials_path
        }
        
        self.billing_client = BillingClient(
            billing_account_id=billing_account_id,
            billing_dataset=billing_dataset,
            **collector_kwargs
        )
        
        self.compute_collector = ComputeEngineCostCollector(**collector_kwargs)
        self.sql_collector = CloudSQLCostCollector(**collector_kwargs)
        self.functions_collector = CloudFunctionsCostCollector(**collector_kwargs)
        self.storage_collector = CloudStorageCostCollector(**collector_kwargs)
        
        logger.info(f"Initialized GCP cost analyzer for project: {project_id}")
    
    def analyze_all_services(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        Perform comprehensive cost analysis across all GCP services.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            lookback_days: Days to analyze for utilization
        
        Returns:
            Complete cost analysis
        """
        try:
            # Set default dates
            if not end_date:
                end_date = datetime.utcnow().strftime('%Y-%m-%d')
            if not start_date:
                start_date = (datetime.utcnow() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
            
            logger.info(f"Analyzing GCP costs from {start_date} to {end_date}")
            
            # Get overall cost data
            cost_data = self.billing_client.query_costs(start_date, end_date)
            
            # Get service-specific data
            compute_data = self._analyze_compute_engine(lookback_days)
            sql_data = self._analyze_cloud_sql(lookback_days)
            functions_data = self._analyze_cloud_functions(lookback_days)
            storage_data = self._analyze_cloud_storage()
            
            # Aggregate opportunities
            all_opportunities = self._aggregate_opportunities(
                compute_data,
                sql_data,
                functions_data,
                storage_data
            )
            
            # Calculate waste
            total_waste = sum(opp['estimated_savings'] for opp in all_opportunities)
            
            # Detect anomalies
            anomalies = self.detect_anomalies(cost_data)
            
            return {
                'project_id': self.project_id,
                'time_period': {'start': start_date, 'end': end_date},
                'total_cost': cost_data.get('total_cost', 0.0),
                'cost_breakdown': {
                    'by_service': cost_data.get('by_service', {}),
                    'by_project': cost_data.get('by_project', {}),
                    'daily': cost_data.get('daily_breakdown', [])
                },
                'services': {
                    'compute_engine': compute_data,
                    'cloud_sql': sql_data,
                    'cloud_functions': functions_data,
                    'cloud_storage': storage_data
                },
                'optimization': {
                    'total_opportunities': len(all_opportunities),
                    'total_potential_savings': round(total_waste, 2),
                    'opportunities': all_opportunities[:20]  # Top 20
                },
                'anomalies': anomalies,
                'analyzed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze all services: {e}")
            raise
    
    def _analyze_compute_engine(self, lookback_days: int) -> Dict[str, Any]:
        """Analyze Compute Engine costs"""
        try:
            instance_costs = self.compute_collector.collect_instance_costs()
            idle_instances = self.compute_collector.identify_idle_instances(lookback_days)
            underutilized = self.compute_collector.identify_underutilized_instances(lookback_days)
            preemptible_opps = self.compute_collector.get_preemptible_opportunities()
            disk_costs = self.compute_collector.get_persistent_disk_costs()
            
            total_instance_cost = sum(inst['monthly_cost'] for inst in instance_costs)
            
            return {
                'total_instances': len(instance_costs),
                'total_monthly_cost': round(total_instance_cost, 2),
                'idle_instances': len(idle_instances),
                'underutilized_instances': len(underutilized),
                'preemptible_opportunities': len(preemptible_opps),
                'disk_costs': disk_costs,
                'instances': instance_costs[:10]  # Sample
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze Compute Engine: {e}")
            return {}
    
    def _analyze_cloud_sql(self, lookback_days: int) -> Dict[str, Any]:
        """Analyze Cloud SQL costs"""
        try:
            sql_costs = self.sql_collector.collect_sql_costs()
            idle_dbs = self.sql_collector.identify_idle_databases(lookback_days)
            storage_costs = self.sql_collector.analyze_storage_costs()
            ha_opps = self.sql_collector.identify_high_availability_opportunities()
            
            total_sql_cost = sum(db['monthly_cost'] for db in sql_costs)
            
            return {
                'total_instances': len(sql_costs),
                'total_monthly_cost': round(total_sql_cost, 2),
                'idle_databases': len(idle_dbs),
                'ha_conversion_opportunities': len(ha_opps),
                'storage_costs': storage_costs,
                'instances': sql_costs[:10]  # Sample
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze Cloud SQL: {e}")
            return {}
    
    def _analyze_cloud_functions(self, lookback_days: int) -> Dict[str, Any]:
        """Analyze Cloud Functions costs"""
        try:
            function_costs = self.functions_collector.collect_function_costs()
            over_provisioned = self.functions_collector.identify_over_provisioned(lookback_days)
            
            total_function_cost = sum(
                fn.get('monthly_cost', 0.0) for fn in function_costs
            )
            
            return {
                'total_functions': len(function_costs),
                'total_monthly_cost': round(total_function_cost, 2),
                'over_provisioned_functions': len(over_provisioned),
                'functions': function_costs[:10]  # Sample
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze Cloud Functions: {e}")
            return {}
    
    def _analyze_cloud_storage(self) -> Dict[str, Any]:
        """Analyze Cloud Storage costs"""
        try:
            bucket_costs = self.storage_collector.collect_bucket_costs()
            storage_class_analysis = self.storage_collector.analyze_storage_classes()
            
            total_storage_cost = sum(bucket['monthly_cost'] for bucket in bucket_costs)
            
            return {
                'total_buckets': len(bucket_costs),
                'total_monthly_cost': round(total_storage_cost, 2),
                'storage_class_distribution': {
                    'standard_gb': storage_class_analysis.get('total_standard_gb', 0.0),
                    'nearline_gb': storage_class_analysis.get('total_nearline_gb', 0.0),
                    'coldline_gb': storage_class_analysis.get('total_coldline_gb', 0.0),
                    'archive_gb': storage_class_analysis.get('total_archive_gb', 0.0)
                },
                'lifecycle_opportunities': len(
                    storage_class_analysis.get('lifecycle_opportunities', [])
                ),
                'buckets': bucket_costs[:10]  # Sample
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze Cloud Storage: {e}")
            return {}
    
    def _aggregate_opportunities(
        self,
        compute_data: Dict[str, Any],
        sql_data: Dict[str, Any],
        functions_data: Dict[str, Any],
        storage_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Aggregate all optimization opportunities"""
        opportunities = []
        
        # Compute Engine opportunities
        try:
            idle_instances = self.compute_collector.identify_idle_instances()
            for inst in idle_instances:
                opportunities.append({
                    'service': 'Compute Engine',
                    'type': 'idle_instance',
                    'resource_id': inst['instance_name'],
                    'estimated_savings': inst['monthly_cost'],
                    'recommendation': 'Terminate idle instance',
                    'details': inst
                })
            
            underutilized = self.compute_collector.identify_underutilized_instances()
            for inst in underutilized:
                opportunities.append({
                    'service': 'Compute Engine',
                    'type': 'underutilized_instance',
                    'resource_id': inst['instance_name'],
                    'estimated_savings': inst['estimated_savings'],
                    'recommendation': f"Resize to {inst['recommended_machine_type']}",
                    'details': inst
                })
            
            preemptible_opps = self.compute_collector.get_preemptible_opportunities()
            for inst in preemptible_opps:
                opportunities.append({
                    'service': 'Compute Engine',
                    'type': 'preemptible_migration',
                    'resource_id': inst['instance_name'],
                    'estimated_savings': inst['monthly_savings'],
                    'recommendation': 'Migrate to preemptible instance',
                    'details': inst
                })
        except Exception as e:
            logger.warning(f"Failed to get Compute opportunities: {e}")
        
        # Cloud SQL opportunities
        try:
            idle_dbs = self.sql_collector.identify_idle_databases()
            for db in idle_dbs:
                opportunities.append({
                    'service': 'Cloud SQL',
                    'type': 'idle_database',
                    'resource_id': db['instance_name'],
                    'estimated_savings': db['monthly_cost'],
                    'recommendation': 'Terminate idle database',
                    'details': db
                })
            
            ha_opps = self.sql_collector.identify_high_availability_opportunities()
            for db in ha_opps:
                opportunities.append({
                    'service': 'Cloud SQL',
                    'type': 'ha_conversion',
                    'resource_id': db['instance_name'],
                    'estimated_savings': db['estimated_savings'],
                    'recommendation': 'Convert to zonal instance',
                    'details': db
                })
        except Exception as e:
            logger.warning(f"Failed to get Cloud SQL opportunities: {e}")
        
        # Cloud Functions opportunities
        try:
            over_provisioned = self.functions_collector.identify_over_provisioned()
            for fn in over_provisioned:
                opportunities.append({
                    'service': 'Cloud Functions',
                    'type': 'over_provisioned_function',
                    'resource_id': fn['function_name'],
                    'estimated_savings': fn['estimated_savings'],
                    'recommendation': f"Reduce memory to {fn['recommended_memory_mb']}MB",
                    'details': fn
                })
        except Exception as e:
            logger.warning(f"Failed to get Cloud Functions opportunities: {e}")
        
        # Cloud Storage opportunities
        try:
            storage_analysis = self.storage_collector.analyze_storage_classes()
            lifecycle_opps = storage_analysis.get('lifecycle_opportunities', [])
            for bucket in lifecycle_opps:
                opportunities.append({
                    'service': 'Cloud Storage',
                    'type': 'lifecycle_policy',
                    'resource_id': bucket['bucket_name'],
                    'estimated_savings': bucket['potential_monthly_savings'],
                    'recommendation': 'Add lifecycle policy for automatic transitions',
                    'details': bucket
                })
        except Exception as e:
            logger.warning(f"Failed to get Cloud Storage opportunities: {e}")
        
        # Sort by savings (descending)
        opportunities.sort(key=lambda x: x['estimated_savings'], reverse=True)
        
        return opportunities
    
    def detect_anomalies(
        self,
        cost_data: Dict[str, Any],
        threshold: float = 1.5
    ) -> List[Dict[str, Any]]:
        """
        Detect cost anomalies.
        
        Args:
            cost_data: Cost data from billing
            threshold: Multiplier for anomaly detection
        
        Returns:
            List of detected anomalies
        """
        try:
            daily_breakdown = cost_data.get('daily_breakdown', [])
            
            if len(daily_breakdown) < 7:
                return []
            
            # Calculate baseline (average of first 80% of data)
            baseline_count = int(len(daily_breakdown) * 0.8)
            baseline_costs = [day['cost'] for day in daily_breakdown[:baseline_count]]
            baseline_avg = sum(baseline_costs) / len(baseline_costs)
            
            anomalies = []
            
            # Check recent days for anomalies
            for day in daily_breakdown[baseline_count:]:
                if day['cost'] > baseline_avg * threshold:
                    anomalies.append({
                        'date': day['date'],
                        'cost': day['cost'],
                        'baseline': round(baseline_avg, 2),
                        'deviation': round(((day['cost'] / baseline_avg) - 1) * 100, 2),
                        'severity': 'high' if day['cost'] > baseline_avg * 2 else 'medium'
                    })
            
            return anomalies
            
        except Exception as e:
            logger.warning(f"Failed to detect anomalies: {e}")
            return []
    
    def get_cost_forecast(self, forecast_days: int = 30) -> Dict[str, Any]:
        """
        Generate cost forecast.
        
        Args:
            forecast_days: Days to forecast
        
        Returns:
            Forecast data
        """
        try:
            return self.billing_client.get_cost_forecast(forecast_days)
        except Exception as e:
            logger.error(f"Failed to get forecast: {e}")
            return {}
