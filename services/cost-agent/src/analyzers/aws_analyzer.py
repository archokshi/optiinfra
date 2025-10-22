"""
AWS Cost Analyzer

Aggregates data from all AWS collectors and performs comprehensive analysis.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid

from src.collectors.aws.cost_explorer import CostExplorerClient
from src.collectors.aws.ec2 import EC2CostCollector
from src.collectors.aws.rds import RDSCostCollector
from src.collectors.aws.lambda_costs import LambdaCostCollector
from src.collectors.aws.s3 import S3CostCollector

logger = logging.getLogger(__name__)


class AWSCostAnalyzer:
    """Comprehensive AWS cost analyzer"""
    
    def __init__(self, **aws_config):
        """
        Initialize AWS cost analyzer.
        
        Args:
            **aws_config: AWS configuration (access_key_id, secret_access_key, region)
        """
        self.config = aws_config
        
        # Initialize collectors
        self.cost_explorer = CostExplorerClient(**aws_config)
        self.ec2_collector = EC2CostCollector(**aws_config)
        self.rds_collector = RDSCostCollector(**aws_config)
        self.lambda_collector = LambdaCostCollector(**aws_config)
        self.s3_collector = S3CostCollector(**aws_config)
        
        logger.info("Initialized AWS Cost Analyzer")
    
    def analyze_all_services(
        self,
        start_date: str,
        end_date: str,
        detect_anomalies: bool = True,
        forecast: bool = True
    ) -> Dict[str, Any]:
        """
        Perform comprehensive analysis across all AWS services.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            detect_anomalies: Run anomaly detection
            forecast: Generate cost forecast
        
        Returns:
            Complete analysis results
        """
        analysis_id = f"analysis-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        logger.info(f"Starting comprehensive AWS analysis: {analysis_id}")
        
        try:
            # Get overall cost data
            cost_data = self.cost_explorer.get_cost_and_usage(
                start_date,
                end_date,
                granularity='DAILY',
                group_by=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
            )
            
            # Collect service-specific data
            ec2_data = self.ec2_collector.collect_instance_costs(
                start_date,
                end_date,
                include_utilization=True
            )
            
            rds_data = self.rds_collector.collect_rds_costs(
                include_utilization=True
            )
            
            lambda_data = self.lambda_collector.collect_lambda_costs(
                include_metrics=True
            )
            
            s3_data = self.s3_collector.collect_bucket_costs()
            
            # Identify opportunities
            opportunities = self._identify_all_opportunities()
            
            # Calculate waste
            waste_summary = self._calculate_waste(opportunities)
            
            # Detect anomalies if requested
            anomalies = []
            if detect_anomalies:
                anomalies = self.detect_anomalies(cost_data)
            
            # Generate forecast if requested
            forecast_data = {}
            if forecast:
                forecast_start = end_date
                forecast_end = (
                    datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=30)
                ).strftime('%Y-%m-%d')
                
                forecast_data = self.cost_explorer.get_cost_forecast(
                    forecast_start,
                    forecast_end
                )
            
            # Calculate trends
            trends = self._calculate_trends(cost_data)
            
            # Generate summary
            summary = {
                'total_monthly_cost': cost_data['total_cost'],
                'total_waste': waste_summary['total_waste'],
                'waste_percentage': waste_summary['waste_percentage'],
                'optimization_potential': waste_summary['total_savings']
            }
            
            # Compile full analysis
            analysis = {
                'analysis_id': analysis_id,
                'timestamp': datetime.utcnow().isoformat(),
                'time_period': {'start': start_date, 'end': end_date},
                'summary': summary,
                'cost_breakdown': cost_data,
                'service_details': {
                    'ec2': {
                        'instance_count': len(ec2_data),
                        'instances': ec2_data
                    },
                    'rds': {
                        'instance_count': len(rds_data),
                        'instances': rds_data
                    },
                    'lambda': {
                        'function_count': len(lambda_data),
                        'functions': lambda_data
                    },
                    's3': {
                        'bucket_count': len(s3_data),
                        'buckets': s3_data
                    }
                },
                'opportunities': opportunities,
                'waste_summary': waste_summary,
                'trends': trends,
                'anomalies': anomalies,
                'forecast': forecast_data
            }
            
            logger.info(
                f"Analysis complete: ${summary['total_monthly_cost']:.2f} total, "
                f"${summary['total_waste']:.2f} waste ({summary['waste_percentage']:.1f}%)"
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise
    
    def detect_anomalies(
        self,
        cost_data: Dict[str, Any],
        threshold_percentage: float = 20.0
    ) -> List[Dict[str, Any]]:
        """
        Detect cost anomalies (unusual spikes).
        
        Args:
            cost_data: Cost data with daily breakdown
            threshold_percentage: Anomaly threshold (% change)
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        try:
            daily_breakdown = cost_data.get('daily_breakdown', [])
            
            if len(daily_breakdown) < 2:
                return anomalies
            
            # Calculate day-over-day changes
            for i in range(1, len(daily_breakdown)):
                prev_day = daily_breakdown[i-1]
                curr_day = daily_breakdown[i]
                
                prev_cost = prev_day['cost']
                curr_cost = curr_day['cost']
                
                if prev_cost == 0:
                    continue
                
                change_pct = ((curr_cost - prev_cost) / prev_cost) * 100
                
                if abs(change_pct) > threshold_percentage:
                    anomalies.append({
                        'date': curr_day['date'],
                        'metric': 'daily_cost',
                        'expected_cost': round(prev_cost, 2),
                        'actual_cost': round(curr_cost, 2),
                        'change_percentage': round(change_pct, 2),
                        'severity': 'high' if abs(change_pct) > 50 else 'medium'
                    })
            
            logger.info(f"Detected {len(anomalies)} cost anomalies")
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
        
        return anomalies
    
    def calculate_waste(self) -> Dict[str, Any]:
        """
        Calculate total waste across all services.
        
        Returns:
            Waste summary
        """
        opportunities = self._identify_all_opportunities()
        return self._calculate_waste(opportunities)
    
    def prioritize_opportunities(
        self,
        opportunities: List[Dict[str, Any]],
        min_savings: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Prioritize optimization opportunities.
        
        Args:
            opportunities: List of opportunities
            min_savings: Minimum savings threshold
        
        Returns:
            Sorted and prioritized opportunities
        """
        # Filter by minimum savings
        filtered = [
            opp for opp in opportunities
            if opp.get('estimated_savings', 0) >= min_savings
        ]
        
        # Calculate priority score
        for opp in filtered:
            savings = opp.get('estimated_savings', 0)
            confidence = opp.get('confidence', 0.5)
            
            # Priority score = savings * confidence
            opp['priority_score'] = savings * confidence
            
            # Assign priority level
            if opp['priority_score'] > 10000:
                opp['priority'] = 'high'
            elif opp['priority_score'] > 1000:
                opp['priority'] = 'medium'
            else:
                opp['priority'] = 'low'
        
        # Sort by priority score (descending)
        sorted_opps = sorted(
            filtered,
            key=lambda x: x['priority_score'],
            reverse=True
        )
        
        return sorted_opps
    
    def generate_summary_report(
        self,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate executive summary report.
        
        Args:
            analysis: Full analysis results
        
        Returns:
            Executive summary
        """
        summary = analysis.get('summary', {})
        opportunities = analysis.get('opportunities', [])
        
        # Group opportunities by type
        by_type = {}
        for opp in opportunities:
            opp_type = opp.get('type', 'unknown')
            if opp_type not in by_type:
                by_type[opp_type] = {
                    'count': 0,
                    'total_savings': 0.0
                }
            by_type[opp_type]['count'] += 1
            by_type[opp_type]['total_savings'] += opp.get('estimated_savings', 0)
        
        # Top opportunities
        top_opportunities = sorted(
            opportunities,
            key=lambda x: x.get('estimated_savings', 0),
            reverse=True
        )[:10]
        
        return {
            'total_monthly_cost': summary.get('total_monthly_cost', 0),
            'total_waste': summary.get('total_waste', 0),
            'waste_percentage': summary.get('waste_percentage', 0),
            'total_opportunities': len(opportunities),
            'opportunities_by_type': by_type,
            'top_10_opportunities': top_opportunities,
            'high_priority_count': len([o for o in opportunities if o.get('priority') == 'high']),
            'medium_priority_count': len([o for o in opportunities if o.get('priority') == 'medium']),
            'low_priority_count': len([o for o in opportunities if o.get('priority') == 'low'])
        }
    
    def _identify_all_opportunities(self) -> List[Dict[str, Any]]:
        """Identify all optimization opportunities across services"""
        opportunities = []
        
        try:
            # EC2 opportunities
            idle_ec2 = self.ec2_collector.identify_idle_instances()
            for instance in idle_ec2:
                opportunities.append({
                    'id': f"opp-ec2-idle-{uuid.uuid4().hex[:8]}",
                    'type': 'idle_resource',
                    'service': 'EC2',
                    'resource_ids': [instance['instance_id']],
                    'description': f"Idle EC2 instance: {instance['instance_id']}",
                    'estimated_savings': instance['monthly_cost'],
                    'confidence': 0.95,
                    'effort': 'low',
                    'risk': 'low'
                })
            
            underutilized_ec2 = self.ec2_collector.identify_underutilized_instances()
            for instance in underutilized_ec2:
                opportunities.append({
                    'id': f"opp-ec2-rightsize-{uuid.uuid4().hex[:8]}",
                    'type': 'rightsizing',
                    'service': 'EC2',
                    'resource_ids': [instance['instance_id']],
                    'description': f"Rightsize {instance['instance_type']} to {instance['recommended_instance_type']}",
                    'estimated_savings': instance['estimated_savings'],
                    'confidence': 0.90,
                    'effort': 'low',
                    'risk': 'low'
                })
            
            spot_opportunities = self.ec2_collector.get_spot_opportunities()
            if spot_opportunities:
                total_savings = sum(opp['monthly_savings'] for opp in spot_opportunities)
                opportunities.append({
                    'id': f"opp-ec2-spot-{uuid.uuid4().hex[:8]}",
                    'type': 'spot_migration',
                    'service': 'EC2',
                    'resource_ids': [opp['instance_id'] for opp in spot_opportunities],
                    'description': f"Migrate {len(spot_opportunities)} instances to spot",
                    'estimated_savings': total_savings,
                    'confidence': 0.85,
                    'effort': 'medium',
                    'risk': 'low'
                })
            
            # RDS opportunities
            idle_rds = self.rds_collector.identify_idle_databases()
            for db in idle_rds:
                opportunities.append({
                    'id': f"opp-rds-idle-{uuid.uuid4().hex[:8]}",
                    'type': 'idle_resource',
                    'service': 'RDS',
                    'resource_ids': [db['db_instance_id']],
                    'description': f"Idle RDS database: {db['db_instance_id']}",
                    'estimated_savings': db['monthly_cost'],
                    'confidence': 0.95,
                    'effort': 'low',
                    'risk': 'low'
                })
            
            # Lambda opportunities
            over_provisioned_lambda = self.lambda_collector.identify_over_provisioned()
            for func in over_provisioned_lambda:
                opportunities.append({
                    'id': f"opp-lambda-{uuid.uuid4().hex[:8]}",
                    'type': 'rightsizing',
                    'service': 'Lambda',
                    'resource_ids': [func['function_name']],
                    'description': f"Reduce Lambda memory: {func['function_name']}",
                    'estimated_savings': func['estimated_savings'],
                    'confidence': 0.80,
                    'effort': 'low',
                    'risk': 'low'
                })
            
            # S3 opportunities
            s3_analysis = self.s3_collector.analyze_storage_classes()
            for opp in s3_analysis.get('lifecycle_opportunities', []):
                opportunities.append({
                    'id': f"opp-s3-{uuid.uuid4().hex[:8]}",
                    'type': 'storage_optimization',
                    'service': 'S3',
                    'resource_ids': [opp['bucket_name']],
                    'description': f"Add lifecycle policy to {opp['bucket_name']}",
                    'estimated_savings': opp['potential_monthly_savings'],
                    'confidence': 0.85,
                    'effort': 'low',
                    'risk': 'low'
                })
            
            # Prioritize opportunities
            opportunities = self.prioritize_opportunities(opportunities)
            
            logger.info(f"Identified {len(opportunities)} total opportunities")
            
        except Exception as e:
            logger.error(f"Failed to identify opportunities: {e}")
        
        return opportunities
    
    def _calculate_waste(
        self,
        opportunities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate waste summary from opportunities"""
        total_savings = sum(
            opp.get('estimated_savings', 0)
            for opp in opportunities
        )
        
        # Group by service
        by_service = {}
        for opp in opportunities:
            service = opp.get('service', 'Unknown')
            if service not in by_service:
                by_service[service] = 0.0
            by_service[service] += opp.get('estimated_savings', 0)
        
        # Estimate total cost (would need actual data)
        # For now, assume waste is part of total
        total_cost = total_savings * 2  # Rough estimate
        waste_percentage = (total_savings / total_cost * 100) if total_cost > 0 else 0
        
        return {
            'total_waste': round(total_savings, 2),
            'total_savings': round(total_savings, 2),
            'waste_percentage': round(waste_percentage, 2),
            'by_service': {k: round(v, 2) for k, v in by_service.items()}
        }
    
    def _calculate_trends(
        self,
        cost_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate cost trends"""
        daily_breakdown = cost_data.get('daily_breakdown', [])
        
        if len(daily_breakdown) < 7:
            return {}
        
        # Calculate 7-day and 30-day changes
        recent_7d = daily_breakdown[-7:]
        recent_30d = daily_breakdown[-30:] if len(daily_breakdown) >= 30 else daily_breakdown
        
        avg_7d = sum(d['cost'] for d in recent_7d) / len(recent_7d)
        avg_30d = sum(d['cost'] for d in recent_30d) / len(recent_30d)
        
        change_7d = ((avg_7d - avg_30d) / avg_30d * 100) if avg_30d > 0 else 0
        
        # Find fastest growing service (would need service breakdown)
        by_service = cost_data.get('by_service', {})
        fastest_growing = max(by_service.items(), key=lambda x: x[1])[0] if by_service else 'Unknown'
        
        return {
            'cost_change_7d': round(change_7d, 2),
            'cost_change_30d': 0.0,  # Would need historical data
            'average_daily_cost_7d': round(avg_7d, 2),
            'average_daily_cost_30d': round(avg_30d, 2),
            'fastest_growing_service': fastest_growing
        }
