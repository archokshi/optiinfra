"""
GCP Cloud Functions Cost Collector

Collects Cloud Functions costs and identifies optimization opportunities.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from google.cloud import functions_v1
from google.cloud import monitoring_v3

from src.collectors.gcp.base import GCPBaseCollector

logger = logging.getLogger(__name__)


class CloudFunctionsCostCollector(GCPBaseCollector):
    """Collector for Cloud Functions costs and optimization opportunities"""
    
    def __init__(self, **kwargs):
        """Initialize Cloud Functions cost collector"""
        super().__init__(**kwargs)
        self.functions_client = self.get_client(functions_v1.CloudFunctionsServiceClient)
        self.monitoring_client = self.get_client(monitoring_v3.MetricServiceClient)
    
    def collect_function_costs(
        self,
        include_metrics: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Collect per-function Cloud Functions costs.
        
        Args:
            include_metrics: Include Cloud Monitoring metrics
        
        Returns:
            List of function cost data
        """
        try:
            functions = self._get_all_functions()
            logger.info(f"Found {len(functions)} Cloud Functions")
            
            function_costs = []
            
            for function in functions:
                function_name = function.name.split('/')[-1]
                memory_mb = function.available_memory_mb
                runtime = function.runtime
                region = function.name.split('/')[3]
                
                function_data = {
                    'function_name': function_name,
                    'memory_mb': memory_mb,
                    'runtime': runtime,
                    'region': region,
                    'timeout': function.timeout.seconds if function.timeout else 60
                }
                
                # Add metrics if requested
                if include_metrics:
                    metrics = self._get_function_metrics(function_name, region)
                    function_data['metrics'] = metrics
                    
                    # Calculate cost
                    monthly_cost = self._calculate_function_cost(
                        metrics['invocations'],
                        metrics['execution_time_avg'],
                        memory_mb
                    )
                    function_data['monthly_cost'] = monthly_cost
                    
                    # Analyze for optimization
                    function_data['optimization'] = self._analyze_function(
                        function_data,
                        metrics
                    )
                
                function_costs.append(function_data)
            
            logger.info(f"Collected cost data for {len(function_costs)} functions")
            return function_costs
            
        except Exception as e:
            logger.error(f"Failed to collect Cloud Functions costs: {e}")
            raise
    
    def identify_over_provisioned(
        self,
        lookback_days: int = 14
    ) -> List[Dict[str, Any]]:
        """
        Identify over-provisioned Cloud Functions.
        
        Args:
            lookback_days: Days to analyze
        
        Returns:
            List of over-provisioned functions
        """
        try:
            functions = self._get_all_functions()
            over_provisioned = []
            
            for function in functions:
                function_name = function.name.split('/')[-1]
                region = function.name.split('/')[3]
                memory_mb = function.available_memory_mb
                
                # Get actual memory usage (would need custom metrics)
                # For now, use heuristic based on execution time
                metrics = self._get_function_metrics(function_name, region, lookback_days)
                
                # If function completes quickly, might be over-provisioned
                if metrics['execution_time_avg'] < 100:  # < 100ms
                    optimal_memory = self._calculate_optimal_memory(
                        metrics['execution_time_avg'],
                        memory_mb
                    )
                    
                    if optimal_memory < memory_mb:
                        current_cost = self._calculate_function_cost(
                            metrics['invocations'],
                            metrics['execution_time_avg'],
                            memory_mb
                        )
                        
                        optimized_cost = self._calculate_function_cost(
                            metrics['invocations'],
                            metrics['execution_time_avg'],
                            optimal_memory
                        )
                        
                        over_provisioned.append({
                            'function_name': function_name,
                            'current_memory_mb': memory_mb,
                            'recommended_memory_mb': optimal_memory,
                            'current_cost': current_cost,
                            'optimized_cost': optimized_cost,
                            'estimated_savings': current_cost - optimized_cost
                        })
            
            logger.info(f"Identified {len(over_provisioned)} over-provisioned functions")
            return over_provisioned
            
        except Exception as e:
            logger.error(f"Failed to identify over-provisioned functions: {e}")
            return []
    
    def _get_all_functions(self) -> List[Any]:
        """Get all Cloud Functions"""
        try:
            parent = f"projects/{self.project_id}/locations/-"
            
            self.log_api_call()
            functions = list(self.functions_client.list_functions(parent=parent))
            
            return functions
            
        except Exception as e:
            logger.error(f"Failed to get Cloud Functions: {e}")
            return []
    
    def _get_function_metrics(
        self,
        function_name: str,
        region: str,
        lookback_days: int = 14
    ) -> Dict[str, float]:
        """Get function metrics from Cloud Monitoring"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=lookback_days)
            
            # Get execution count
            executions = self._get_monitoring_metric(
                function_name,
                region,
                'cloudfunctions.googleapis.com/function/execution_count',
                start_time,
                end_time,
                'sum'
            )
            
            # Get execution times
            exec_times = self._get_monitoring_metric(
                function_name,
                region,
                'cloudfunctions.googleapis.com/function/execution_times',
                start_time,
                end_time,
                'average'
            )
            
            # Get user memory
            memory = self._get_monitoring_metric(
                function_name,
                region,
                'cloudfunctions.googleapis.com/function/user_memory_bytes',
                start_time,
                end_time,
                'average'
            )
            
            total_executions = executions.get('sum', 0.0)
            
            return {
                'invocations': int(total_executions),
                'execution_time_avg': round(exec_times.get('average', 0.0), 2),
                'memory_used_mb': round(memory.get('average', 0.0) / (1024**2), 2)
            }
            
        except Exception as e:
            logger.warning(f"Failed to get metrics for {function_name}: {e}")
            return {
                'invocations': 0,
                'execution_time_avg': 0.0,
                'memory_used_mb': 0.0
            }
    
    def _get_monitoring_metric(
        self,
        function_name: str,
        region: str,
        metric_type: str,
        start_time: datetime,
        end_time: datetime,
        aggregation: str
    ) -> Dict[str, float]:
        """Get Cloud Monitoring metric for Cloud Function"""
        try:
            project_name = f"projects/{self.project_id}"
            
            interval = monitoring_v3.TimeInterval(
                {
                    "end_time": {"seconds": int(end_time.timestamp())},
                    "start_time": {"seconds": int(start_time.timestamp())},
                }
            )
            
            filter_str = (
                f'metric.type = "{metric_type}" '
                f'AND resource.labels.function_name = "{function_name}" '
                f'AND resource.labels.region = "{region}"'
            )
            
            request = monitoring_v3.ListTimeSeriesRequest(
                {
                    "name": project_name,
                    "filter": filter_str,
                    "interval": interval,
                    "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                }
            )
            
            self.log_api_call()
            results = self.monitoring_client.list_time_series(request=request)
            
            values = []
            for result in results:
                for point in result.points:
                    values.append(point.value.double_value)
            
            if not values:
                return {aggregation: 0.0}
            
            if aggregation == 'sum':
                return {'sum': sum(values)}
            else:  # average
                return {'average': sum(values) / len(values)}
            
        except Exception as e:
            logger.warning(f"Failed to get metric {metric_type}: {e}")
            return {aggregation: 0.0}
    
    def _calculate_function_cost(
        self,
        invocations: int,
        execution_time_ms: float,
        memory_mb: int
    ) -> float:
        """
        Calculate Cloud Functions cost.
        
        Pricing:
        - $0.40 per million invocations
        - $0.0000025 per GB-second
        """
        # Invocation cost
        invocation_cost = (invocations / 1_000_000) * 0.40
        
        # Compute cost
        gb_seconds = (invocations * (execution_time_ms / 1000) * (memory_mb / 1024))
        compute_cost = gb_seconds * 0.0000025
        
        return round(invocation_cost + compute_cost, 2)
    
    def _calculate_optimal_memory(
        self,
        execution_time_ms: float,
        current_memory_mb: int
    ) -> int:
        """Calculate optimal memory size"""
        # Simple heuristic: if very fast, can probably use less memory
        memory_options = [128, 256, 512, 1024, 2048, 4096, 8192]
        
        if execution_time_ms < 50:
            return 128
        elif execution_time_ms < 100:
            return 256
        elif execution_time_ms < 500:
            return 512
        else:
            # Keep current if execution time is significant
            return current_memory_mb
    
    def _analyze_function(
        self,
        function_data: Dict[str, Any],
        metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """Analyze function for optimization opportunities"""
        memory_mb = function_data['memory_mb']
        execution_time_avg = metrics['execution_time_avg']
        
        # Check if over-provisioned
        optimal_memory = self._calculate_optimal_memory(execution_time_avg, memory_mb)
        is_over_provisioned = optimal_memory < memory_mb
        
        return {
            'is_over_provisioned': is_over_provisioned,
            'recommended_memory_mb': optimal_memory if is_over_provisioned else memory_mb
        }
