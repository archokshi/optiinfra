"""
AWS Lambda Cost Collector

Collects Lambda function costs and identifies optimization opportunities.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from src.collectors.aws.base import AWSBaseCollector

logger = logging.getLogger(__name__)


class LambdaCostCollector(AWSBaseCollector):
    """Collector for Lambda function costs and optimization opportunities"""
    
    def __init__(self, **kwargs):
        """Initialize Lambda cost collector"""
        super().__init__(**kwargs)
        self.lambda_client = self.get_client('lambda')
        self.cloudwatch_client = self.get_client('cloudwatch')
    
    def collect_lambda_costs(
        self,
        include_metrics: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Collect per-function Lambda costs.
        
        Args:
            include_metrics: Include CloudWatch metrics
        
        Returns:
            List of Lambda function cost data
        """
        try:
            functions = self._get_all_functions()
            logger.info(f"Found {len(functions)} Lambda functions")
            
            function_costs = []
            
            for function in functions:
                function_name = function['FunctionName']
                memory_mb = function['MemorySize']
                runtime = function['Runtime']
                
                function_data = {
                    'function_name': function_name,
                    'memory_mb': memory_mb,
                    'runtime': runtime,
                    'timeout': function.get('Timeout', 3),
                    'region': self.region
                }
                
                # Add metrics if requested
                if include_metrics:
                    metrics = self._get_function_metrics(function_name)
                    function_data['metrics'] = metrics
                    
                    # Calculate cost
                    monthly_cost = self._calculate_function_cost(
                        metrics['invocations'],
                        metrics['duration_avg'],
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
            logger.error(f"Failed to collect Lambda costs: {e}")
            raise
    
    def identify_over_provisioned(
        self,
        lookback_days: int = 14
    ) -> List[Dict[str, Any]]:
        """
        Identify over-provisioned Lambda functions.
        
        Args:
            lookback_days: Days to analyze
        
        Returns:
            List of over-provisioned functions
        """
        try:
            functions = self._get_all_functions()
            over_provisioned = []
            
            for function in functions:
                function_name = function['FunctionName']
                memory_mb = function['MemorySize']
                
                # Get actual memory usage (would need X-Ray or custom metrics)
                # For now, use heuristic based on duration
                metrics = self._get_function_metrics(function_name, lookback_days)
                
                # If function completes quickly, might be over-provisioned
                if metrics['duration_avg'] < 100:  # < 100ms
                    optimal_memory = self._calculate_optimal_memory(
                        metrics['duration_avg'],
                        memory_mb
                    )
                    
                    if optimal_memory < memory_mb:
                        current_cost = self._calculate_function_cost(
                            metrics['invocations'],
                            metrics['duration_avg'],
                            memory_mb
                        )
                        
                        optimized_cost = self._calculate_function_cost(
                            metrics['invocations'],
                            metrics['duration_avg'],
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
    
    def _get_all_functions(self) -> List[Dict[str, Any]]:
        """Get all Lambda functions"""
        try:
            self.log_api_call('lambda', 'ListFunctions')
            
            functions = self.paginate_results(
                self.lambda_client,
                'list_functions',
                'Functions'
            )
            
            return functions
            
        except Exception as e:
            logger.error(f"Failed to get Lambda functions: {e}")
            return []
    
    def _get_function_metrics(
        self,
        function_name: str,
        lookback_days: int = 14
    ) -> Dict[str, float]:
        """Get function metrics from CloudWatch"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=lookback_days)
            
            # Get invocations
            invocations = self._get_cloudwatch_metric(
                function_name,
                'Invocations',
                start_time,
                end_time,
                'Sum'
            )
            
            # Get duration
            duration = self._get_cloudwatch_metric(
                function_name,
                'Duration',
                start_time,
                end_time,
                'Average'
            )
            
            # Get errors
            errors = self._get_cloudwatch_metric(
                function_name,
                'Errors',
                start_time,
                end_time,
                'Sum'
            )
            
            # Get throttles
            throttles = self._get_cloudwatch_metric(
                function_name,
                'Throttles',
                start_time,
                end_time,
                'Sum'
            )
            
            total_invocations = invocations.get('Sum', 0.0)
            
            return {
                'invocations': int(total_invocations),
                'duration_avg': round(duration.get('Average', 0.0), 2),
                'errors': int(errors.get('Sum', 0.0)),
                'throttles': int(throttles.get('Sum', 0.0)),
                'error_rate': round(
                    (errors.get('Sum', 0.0) / total_invocations * 100)
                    if total_invocations > 0 else 0.0,
                    2
                )
            }
            
        except Exception as e:
            logger.warning(f"Failed to get metrics for {function_name}: {e}")
            return {
                'invocations': 0,
                'duration_avg': 0.0,
                'errors': 0,
                'throttles': 0,
                'error_rate': 0.0
            }
    
    def _get_cloudwatch_metric(
        self,
        function_name: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        statistic: str
    ) -> Dict[str, float]:
        """Get CloudWatch metric for Lambda function"""
        try:
            self.log_api_call('cloudwatch', 'GetMetricStatistics')
            
            response = self.cloudwatch_client.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName=metric_name,
                Dimensions=[
                    {'Name': 'FunctionName', 'Value': function_name}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=[statistic]
            )
            
            datapoints = response.get('Datapoints', [])
            
            if not datapoints:
                return {statistic: 0.0}
            
            if statistic == 'Sum':
                value = sum(d[statistic] for d in datapoints)
            else:  # Average
                value = sum(d[statistic] for d in datapoints) / len(datapoints)
            
            return {statistic: value}
            
        except Exception as e:
            logger.warning(f"Failed to get metric {metric_name}: {e}")
            return {statistic: 0.0}
    
    def _calculate_function_cost(
        self,
        invocations: int,
        duration_ms: float,
        memory_mb: int
    ) -> float:
        """
        Calculate Lambda function cost.
        
        Lambda pricing:
        - $0.20 per 1M requests
        - $0.0000166667 per GB-second
        """
        # Request cost
        request_cost = (invocations / 1_000_000) * 0.20
        
        # Compute cost
        gb_seconds = (invocations * (duration_ms / 1000) * (memory_mb / 1024))
        compute_cost = gb_seconds * 0.0000166667
        
        return round(request_cost + compute_cost, 2)
    
    def _calculate_optimal_memory(
        self,
        duration_ms: float,
        current_memory_mb: int
    ) -> int:
        """Calculate optimal memory size"""
        # Simple heuristic: if very fast, can probably use less memory
        memory_options = [128, 256, 512, 1024, 1536, 2048, 3008]
        
        if duration_ms < 50:
            return 128
        elif duration_ms < 100:
            return 256
        elif duration_ms < 500:
            return 512
        else:
            # Keep current if duration is significant
            return current_memory_mb
    
    def _analyze_function(
        self,
        function_data: Dict[str, Any],
        metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """Analyze function for optimization opportunities"""
        memory_mb = function_data['memory_mb']
        duration_avg = metrics['duration_avg']
        error_rate = metrics['error_rate']
        
        # Check if over-provisioned
        optimal_memory = self._calculate_optimal_memory(duration_avg, memory_mb)
        is_over_provisioned = optimal_memory < memory_mb
        
        # Check error rate
        has_high_errors = error_rate > 5.0
        
        return {
            'is_over_provisioned': is_over_provisioned,
            'recommended_memory_mb': optimal_memory if is_over_provisioned else memory_mb,
            'has_high_errors': has_high_errors,
            'error_rate': error_rate
        }
