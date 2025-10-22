"""
AWS Cost Explorer Client

Wrapper for AWS Cost Explorer API to retrieve cost and usage data.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.collectors.aws.base import AWSBaseCollector

logger = logging.getLogger(__name__)


class CostExplorerClient(AWSBaseCollector):
    """Client for AWS Cost Explorer API"""
    
    def __init__(self, **kwargs):
        """Initialize Cost Explorer client"""
        super().__init__(**kwargs)
        self.ce_client = self.get_client('ce', region='us-east-1')  # Cost Explorer is global
    
    def get_cost_and_usage(
        self,
        start_date: str,
        end_date: str,
        granularity: str = 'DAILY',
        metrics: Optional[List[str]] = None,
        group_by: Optional[List[Dict[str, str]]] = None,
        filter_expr: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get cost and usage data from Cost Explorer.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            granularity: DAILY or MONTHLY
            metrics: List of metrics (default: ['UnblendedCost'])
            group_by: Group by dimensions (e.g., [{'Type': 'DIMENSION', 'Key': 'SERVICE'}])
            filter_expr: Filter expression
        
        Returns:
            Cost and usage data
        """
        if metrics is None:
            metrics = ['UnblendedCost']
        
        try:
            self.log_api_call('cost_explorer', 'GetCostAndUsage')
            
            params = {
                'TimePeriod': {
                    'Start': start_date,
                    'End': end_date
                },
                'Granularity': granularity,
                'Metrics': metrics
            }
            
            if group_by:
                params['GroupBy'] = group_by
            
            if filter_expr:
                params['Filter'] = filter_expr
            
            response = self.handle_throttling(
                self.ce_client.get_cost_and_usage,
                **params
            )
            
            logger.info(
                f"Retrieved cost data: {start_date} to {end_date}, "
                f"{len(response.get('ResultsByTime', []))} time periods"
            )
            
            return self._transform_cost_response(response)
            
        except Exception as e:
            logger.error(f"Failed to get cost and usage: {e}")
            raise
    
    def get_cost_forecast(
        self,
        start_date: str,
        end_date: str,
        metric: str = 'UNBLENDED_COST',
        granularity: str = 'MONTHLY'
    ) -> Dict[str, Any]:
        """
        Get cost forecast for next 30 days.
        
        Args:
            start_date: Forecast start date (YYYY-MM-DD)
            end_date: Forecast end date (YYYY-MM-DD)
            metric: Metric to forecast
            granularity: DAILY or MONTHLY
        
        Returns:
            Forecast data
        """
        try:
            self.log_api_call('cost_explorer', 'GetCostForecast')
            
            response = self.handle_throttling(
                self.ce_client.get_cost_forecast,
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Metric=metric,
                Granularity=granularity
            )
            
            total_forecast = float(response.get('Total', {}).get('Amount', 0))
            
            logger.info(f"Cost forecast: ${total_forecast:.2f}")
            
            return {
                'time_period': {
                    'start': start_date,
                    'end': end_date
                },
                'projected_cost': total_forecast,
                'confidence_interval': {
                    'lower': total_forecast * 0.95,  # Approximate
                    'upper': total_forecast * 1.05
                },
                'forecast_by_time': response.get('ForecastResultsByTime', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to get cost forecast: {e}")
            raise
    
    def get_savings_plans_utilization(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Get Savings Plans utilization.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            Savings Plans utilization data
        """
        try:
            self.log_api_call('cost_explorer', 'GetSavingsPlansUtilization')
            
            response = self.handle_throttling(
                self.ce_client.get_savings_plans_utilization,
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                }
            )
            
            total = response.get('Total', {})
            utilization = total.get('Utilization', {})
            
            return {
                'time_period': {'start': start_date, 'end': end_date},
                'utilization_percentage': float(utilization.get('UtilizationPercentage', 0)),
                'total_commitment': float(total.get('TotalCommitment', {}).get('Amount', 0)),
                'used_commitment': float(total.get('UsedCommitment', {}).get('Amount', 0)),
                'unused_commitment': float(total.get('UnusedCommitment', {}).get('Amount', 0))
            }
            
        except Exception as e:
            logger.warning(f"Failed to get Savings Plans utilization: {e}")
            return {}
    
    def get_reservation_utilization(
        self,
        start_date: str,
        end_date: str,
        granularity: str = 'MONTHLY'
    ) -> Dict[str, Any]:
        """
        Get Reserved Instance utilization.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            granularity: DAILY or MONTHLY
        
        Returns:
            RI utilization data
        """
        try:
            self.log_api_call('cost_explorer', 'GetReservationUtilization')
            
            response = self.handle_throttling(
                self.ce_client.get_reservation_utilization,
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity=granularity
            )
            
            total = response.get('Total', {})
            utilization = total.get('UtilizationPercentage', '0')
            
            return {
                'time_period': {'start': start_date, 'end': end_date},
                'utilization_percentage': float(utilization),
                'purchased_hours': float(total.get('PurchasedHours', 0)),
                'total_actual_hours': float(total.get('TotalActualHours', 0)),
                'unused_hours': float(total.get('UnusedHours', 0))
            }
            
        except Exception as e:
            logger.warning(f"Failed to get RI utilization: {e}")
            return {}
    
    def get_rightsizing_recommendations(
        self,
        service: str = 'AmazonEC2'
    ) -> List[Dict[str, Any]]:
        """
        Get AWS rightsizing recommendations.
        
        Args:
            service: AWS service (default: AmazonEC2)
        
        Returns:
            List of rightsizing recommendations
        """
        try:
            self.log_api_call('cost_explorer', 'GetRightsizingRecommendation')
            
            response = self.handle_throttling(
                self.ce_client.get_rightsizing_recommendation,
                Service=service
            )
            
            recommendations = []
            for rec in response.get('RightsizingRecommendations', []):
                current = rec.get('CurrentInstance', {})
                modify_rec = rec.get('ModifyRecommendationDetail', {})
                terminate_rec = rec.get('TerminateRecommendationDetail', {})
                
                if modify_rec:
                    target_instances = modify_rec.get('TargetInstances', [])
                    if target_instances:
                        target = target_instances[0]
                        recommendations.append({
                            'type': 'modify',
                            'resource_id': current.get('ResourceId'),
                            'current_instance_type': current.get('InstanceType'),
                            'recommended_instance_type': target.get('InstanceType'),
                            'estimated_monthly_savings': float(
                                target.get('EstimatedMonthlySavings', {}).get('Amount', 0)
                            ),
                            'estimated_monthly_cost': float(
                                target.get('EstimatedMonthlyCost', {}).get('Amount', 0)
                            )
                        })
                
                if terminate_rec:
                    recommendations.append({
                        'type': 'terminate',
                        'resource_id': current.get('ResourceId'),
                        'current_instance_type': current.get('InstanceType'),
                        'estimated_monthly_savings': float(
                            terminate_rec.get('EstimatedMonthlySavings', {}).get('Amount', 0)
                        )
                    })
            
            logger.info(f"Retrieved {len(recommendations)} rightsizing recommendations")
            return recommendations
            
        except Exception as e:
            logger.warning(f"Failed to get rightsizing recommendations: {e}")
            return []
    
    def _transform_cost_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Cost Explorer response to OptiInfra format.
        
        Args:
            response: Raw Cost Explorer response
        
        Returns:
            Transformed cost data
        """
        results_by_time = response.get('ResultsByTime', [])
        
        if not results_by_time:
            return {
                'total_cost': 0.0,
                'by_service': {},
                'by_region': {},
                'daily_breakdown': []
            }
        
        total_cost = 0.0
        by_service = {}
        daily_breakdown = []
        
        for result in results_by_time:
            time_period = result.get('TimePeriod', {})
            groups = result.get('Groups', [])
            
            # If grouped by service
            if groups:
                for group in groups:
                    keys = group.get('Keys', [])
                    metrics = group.get('Metrics', {})
                    
                    if keys:
                        service = keys[0]
                        cost = float(metrics.get('UnblendedCost', {}).get('Amount', 0))
                        
                        by_service[service] = by_service.get(service, 0.0) + cost
                        total_cost += cost
            else:
                # No grouping, just total
                metrics = result.get('Total', {})
                cost = float(metrics.get('UnblendedCost', {}).get('Amount', 0))
                total_cost += cost
            
            # Daily breakdown
            daily_cost = float(
                result.get('Total', {}).get('UnblendedCost', {}).get('Amount', 0)
            )
            daily_breakdown.append({
                'date': time_period.get('Start'),
                'cost': daily_cost
            })
        
        return {
            'total_cost': round(total_cost, 2),
            'by_service': {k: round(v, 2) for k, v in by_service.items()},
            'by_region': {},  # Would need separate query with region grouping
            'daily_breakdown': daily_breakdown
        }
