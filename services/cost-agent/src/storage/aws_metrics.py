"""
AWS Metrics Storage

Stores AWS cost metrics in ClickHouse for time-series analysis.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from shared.database.connections import get_clickhouse_client

logger = logging.getLogger(__name__)


class AWSMetricsStorage:
    """Storage layer for AWS cost metrics in ClickHouse"""
    
    def __init__(self):
        """Initialize AWS metrics storage"""
        self.client = get_clickhouse_client()
        logger.info("Initialized AWS Metrics Storage")
    
    def store_cost_metrics(
        self,
        cost_data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Store cost metrics in ClickHouse.
        
        Args:
            cost_data: Cost data from Cost Explorer
            timestamp: Optional timestamp (default: now)
        
        Returns:
            True if successful
        """
        try:
            if timestamp is None:
                timestamp = datetime.utcnow()
            
            # Store daily breakdown
            daily_breakdown = cost_data.get('daily_breakdown', [])
            
            for day_data in daily_breakdown:
                date_str = day_data['date']
                cost = day_data['cost']
                
                # Insert into cost_metrics table
                query = """
                INSERT INTO cost_metrics (
                    timestamp, date, provider, service, region, cost
                ) VALUES
                """
                
                # Insert for each service
                by_service = cost_data.get('by_service', {})
                
                if by_service:
                    for service, service_cost in by_service.items():
                        self.client.execute(
                            query,
                            [{
                                'timestamp': timestamp,
                                'date': date_str,
                                'provider': 'aws',
                                'service': service,
                                'region': 'all',  # Would need region breakdown
                                'cost': service_cost / len(daily_breakdown)  # Distribute evenly
                            }]
                        )
                else:
                    # No service breakdown, store total
                    self.client.execute(
                        query,
                        [{
                            'timestamp': timestamp,
                            'date': date_str,
                            'provider': 'aws',
                            'service': 'total',
                            'region': 'all',
                            'cost': cost
                        }]
                    )
            
            logger.info(f"Stored {len(daily_breakdown)} cost metric records")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store cost metrics: {e}")
            return False
    
    def store_instance_metrics(
        self,
        instances: List[Dict[str, Any]],
        provider: str = 'aws',
        resource_type: str = 'ec2_instance'
    ) -> bool:
        """
        Store per-instance metrics.
        
        Args:
            instances: List of instance data
            provider: Cloud provider
            resource_type: Type of resource
        
        Returns:
            True if successful
        """
        try:
            timestamp = datetime.utcnow()
            
            query = """
            INSERT INTO resource_metrics (
                timestamp, provider, resource_id, resource_type, region,
                cpu_utilization, memory_utilization, network_in, network_out,
                disk_read, disk_write, cost
            ) VALUES
            """
            
            records = []
            for instance in instances:
                utilization = instance.get('utilization', {})
                
                records.append({
                    'timestamp': timestamp,
                    'provider': provider,
                    'resource_id': instance.get('instance_id', instance.get('db_instance_id', 'unknown')),
                    'resource_type': resource_type,
                    'region': instance.get('region', 'unknown'),
                    'cpu_utilization': utilization.get('cpu_avg', 0.0),
                    'memory_utilization': 0.0,  # Would need actual data
                    'network_in': utilization.get('network_mb_day', 0.0),
                    'network_out': 0.0,
                    'disk_read': 0.0,
                    'disk_write': 0.0,
                    'cost': instance.get('monthly_cost', 0.0)
                })
            
            if records:
                self.client.execute(query, records)
                logger.info(f"Stored {len(records)} instance metric records")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store instance metrics: {e}")
            return False
    
    def store_optimization_opportunities(
        self,
        opportunities: List[Dict[str, Any]]
    ) -> bool:
        """
        Store optimization opportunities.
        
        Args:
            opportunities: List of opportunities
        
        Returns:
            True if successful
        """
        try:
            timestamp = datetime.utcnow()
            
            query = """
            INSERT INTO optimization_opportunities (
                timestamp, provider, opportunity_type, service, resource_id,
                description, estimated_savings, confidence, priority, status
            ) VALUES
            """
            
            records = []
            for opp in opportunities:
                resource_ids = opp.get('resource_ids', [])
                resource_id = resource_ids[0] if resource_ids else 'multiple'
                
                records.append({
                    'timestamp': timestamp,
                    'provider': 'aws',
                    'opportunity_type': opp.get('type', 'unknown'),
                    'service': opp.get('service', 'unknown'),
                    'resource_id': resource_id,
                    'description': opp.get('description', ''),
                    'estimated_savings': opp.get('estimated_savings', 0.0),
                    'confidence': opp.get('confidence', 0.5),
                    'priority': opp.get('priority', 'medium'),
                    'status': 'identified'
                })
            
            if records:
                self.client.execute(query, records)
                logger.info(f"Stored {len(records)} optimization opportunities")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store opportunities: {e}")
            return False
    
    def query_cost_trends(
        self,
        start_date: str,
        end_date: str,
        service: Optional[str] = None,
        region: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query cost trends over time.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            service: Optional service filter
            region: Optional region filter
        
        Returns:
            List of cost trend data
        """
        try:
            query = """
            SELECT 
                date,
                service,
                region,
                SUM(cost) as total_cost
            FROM cost_metrics
            WHERE provider = 'aws'
                AND date >= %(start_date)s
                AND date <= %(end_date)s
            """
            
            params = {
                'start_date': start_date,
                'end_date': end_date
            }
            
            if service:
                query += " AND service = %(service)s"
                params['service'] = service
            
            if region:
                query += " AND region = %(region)s"
                params['region'] = region
            
            query += " GROUP BY date, service, region ORDER BY date DESC"
            
            result = self.client.execute(query, params)
            
            trends = []
            for row in result:
                trends.append({
                    'date': row[0],
                    'service': row[1],
                    'region': row[2],
                    'total_cost': float(row[3])
                })
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to query cost trends: {e}")
            return []
    
    def query_by_service(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, float]:
        """
        Query costs grouped by service.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            Dict of service -> cost
        """
        try:
            query = """
            SELECT 
                service,
                SUM(cost) as total_cost
            FROM cost_metrics
            WHERE provider = 'aws'
                AND date >= %(start_date)s
                AND date <= %(end_date)s
            GROUP BY service
            ORDER BY total_cost DESC
            """
            
            result = self.client.execute(query, {
                'start_date': start_date,
                'end_date': end_date
            })
            
            by_service = {}
            for row in result:
                by_service[row[0]] = float(row[1])
            
            return by_service
            
        except Exception as e:
            logger.error(f"Failed to query by service: {e}")
            return {}
    
    def query_by_region(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, float]:
        """
        Query costs grouped by region.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            Dict of region -> cost
        """
        try:
            query = """
            SELECT 
                region,
                SUM(cost) as total_cost
            FROM cost_metrics
            WHERE provider = 'aws'
                AND date >= %(start_date)s
                AND date <= %(end_date)s
            GROUP BY region
            ORDER BY total_cost DESC
            """
            
            result = self.client.execute(query, {
                'start_date': start_date,
                'end_date': end_date
            })
            
            by_region = {}
            for row in result:
                by_region[row[0]] = float(row[1])
            
            return by_region
            
        except Exception as e:
            logger.error(f"Failed to query by region: {e}")
            return {}
    
    def get_idle_resources(
        self,
        lookback_days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get idle resources from recent data.
        
        Args:
            lookback_days: Days to look back
        
        Returns:
            List of idle resources
        """
        try:
            query = """
            SELECT 
                resource_id,
                resource_type,
                region,
                AVG(cpu_utilization) as avg_cpu,
                AVG(cost) as avg_cost
            FROM resource_metrics
            WHERE provider = 'aws'
                AND timestamp >= now() - INTERVAL %(days)s DAY
            GROUP BY resource_id, resource_type, region
            HAVING avg_cpu < 5.0
            ORDER BY avg_cost DESC
            """
            
            result = self.client.execute(query, {'days': lookback_days})
            
            idle_resources = []
            for row in result:
                idle_resources.append({
                    'resource_id': row[0],
                    'resource_type': row[1],
                    'region': row[2],
                    'avg_cpu': float(row[3]),
                    'avg_cost': float(row[4])
                })
            
            return idle_resources
            
        except Exception as e:
            logger.error(f"Failed to get idle resources: {e}")
            return []
