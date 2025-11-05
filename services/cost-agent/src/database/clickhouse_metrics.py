"""
ClickHouse metrics storage for spot migration workflow.
Production-ready metrics storage with automatic table creation and TTL.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from clickhouse_driver import Client
from src.config import settings

logger = logging.getLogger(__name__)


class SpotMigrationMetrics:
    """
    Store and query spot migration metrics in ClickHouse.
    Provides high-performance time-series storage for migration events.
    """
    
    def __init__(self):
        """Initialize ClickHouse client and ensure tables exist"""
        try:
            self.client = Client(
                host=getattr(settings, 'CLICKHOUSE_HOST', 'localhost'),
                port=getattr(settings, 'CLICKHOUSE_PORT', 9000),
                database=getattr(settings, 'CLICKHOUSE_DATABASE', 'optiinfra')
            )
            self._ensure_tables()
            logger.info("ClickHouse metrics client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ClickHouse client: {e}")
            # Don't fail if ClickHouse is not available (graceful degradation)
            self.client = None
    
    def _ensure_tables(self):
        """Create tables if they don't exist"""
        if not self.client:
            return
        
        try:
            self.client.execute("""
                CREATE TABLE IF NOT EXISTS spot_migration_events (
                    timestamp DateTime,
                    request_id String,
                    customer_id String,
                    cloud_provider String,
                    workflow_phase String,
                    instances_analyzed UInt32,
                    opportunities_found UInt32,
                    total_savings Float64,
                    migration_phase String,
                    success UInt8,
                    error_message String,
                    duration_ms UInt32
                ) ENGINE = MergeTree()
                ORDER BY (timestamp, customer_id)
                TTL timestamp + INTERVAL 90 DAY
            """)
            
            # Create RI optimization events table
            self.client.execute("""
                CREATE TABLE IF NOT EXISTS ri_optimization_events (
                    timestamp DateTime,
                    request_id String,
                    customer_id String,
                    cloud_provider String,
                    service_type String,
                    workflow_phase String,
                    instances_analyzed UInt32,
                    stable_workloads_found UInt32,
                    ris_recommended UInt32,
                    total_upfront_cost Float64,
                    monthly_savings Float64,
                    annual_savings Float64,
                    three_year_savings Float64,
                    average_breakeven_months Float32,
                    one_year_ris UInt32,
                    three_year_ris UInt32,
                    success UInt8,
                    error_message String,
                    duration_ms UInt32
                ) ENGINE = MergeTree()
                ORDER BY (timestamp, customer_id)
                TTL timestamp + INTERVAL 90 DAY
            """)
            
            # Create right-sizing optimization events table
            self.client.execute("""
                CREATE TABLE IF NOT EXISTS rightsizing_optimization_events (
                    timestamp DateTime,
                    request_id String,
                    customer_id String,
                    cloud_provider String,
                    service_type String,
                    workflow_phase String,
                    instances_analyzed UInt32,
                    optimization_candidates UInt32,
                    over_provisioned_count UInt32,
                    under_provisioned_count UInt32,
                    recommendations_generated UInt32,
                    downsize_count UInt32,
                    upsize_count UInt32,
                    family_change_count UInt32,
                    total_current_cost Float64,
                    total_recommended_cost Float64,
                    monthly_savings Float64,
                    annual_savings Float64,
                    average_savings_percent Float32,
                    low_risk_count UInt32,
                    medium_risk_count UInt32,
                    high_risk_count UInt32,
                    simple_migrations UInt32,
                    moderate_migrations UInt32,
                    complex_migrations UInt32,
                    success UInt8,
                    error_message String,
                    duration_ms UInt32
                ) ENGINE = MergeTree()
                ORDER BY (timestamp, customer_id)
                TTL timestamp + INTERVAL 90 DAY
            """)
            
            # Create analysis engine events table
            self.client.execute("""
                CREATE TABLE IF NOT EXISTS analysis_engine_events (
                    timestamp DateTime,
                    request_id String,
                    customer_id String,
                    cloud_provider String,
                    analysis_type String,
                    total_resources_analyzed UInt32,
                    idle_resources_found UInt32,
                    critical_idle_count UInt32,
                    high_idle_count UInt32,
                    medium_idle_count UInt32,
                    low_idle_count UInt32,
                    total_monthly_waste Float64,
                    total_annual_waste Float64,
                    total_anomalies_found UInt32,
                    cost_anomalies UInt32,
                    usage_anomalies UInt32,
                    config_anomalies UInt32,
                    security_anomalies UInt32,
                    critical_anomalies UInt32,
                    high_anomalies UInt32,
                    success UInt8,
                    error_message String,
                    duration_ms UInt32
                ) ENGINE = MergeTree()
                ORDER BY (timestamp, customer_id)
                TTL timestamp + INTERVAL 90 DAY
            """)
            
            logger.info("ClickHouse tables ensured")
        except Exception as e:
            logger.error(f"Failed to create ClickHouse tables: {e}")
    
    async def insert_migration_event(
        self,
        event: Dict[str, Any]
    ) -> None:
        """
        Insert spot migration event.
        
        Args:
            event: Event data dict with keys:
                - request_id: str
                - customer_id: str
                - cloud_provider: str (optional, default 'aws')
                - workflow_phase: str
                - instances_analyzed: int (optional)
                - opportunities_found: int (optional)
                - total_savings: float (optional)
                - migration_phase: str (optional)
                - success: bool (optional)
                - error_message: str (optional)
                - duration_ms: int (optional)
        """
        if not self.client:
            logger.warning("ClickHouse client not available, skipping insert")
            return
        
        try:
            self.client.execute(
                "INSERT INTO spot_migration_events VALUES",
                [{
                    "timestamp": event.get("timestamp", datetime.utcnow()),
                    "request_id": event["request_id"],
                    "customer_id": event["customer_id"],
                    "cloud_provider": event.get("cloud_provider", "aws"),
                    "workflow_phase": event["workflow_phase"],
                    "instances_analyzed": event.get("instances_analyzed", 0),
                    "opportunities_found": event.get("opportunities_found", 0),
                    "total_savings": event.get("total_savings", 0.0),
                    "migration_phase": event.get("migration_phase", ""),
                    "success": 1 if event.get("success", False) else 0,
                    "error_message": event.get("error_message", ""),
                    "duration_ms": event.get("duration_ms", 0)
                }]
            )
            
            logger.debug(
                "Inserted spot migration event to ClickHouse",
                extra={"request_id": event["request_id"]}
            )
            
        except Exception as e:
            logger.error(
                f"Failed to insert event to ClickHouse: {e}",
                extra={"request_id": event.get("request_id")}
            )
    
    async def get_customer_savings(
        self,
        customer_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get total savings for customer over time period.
        
        Args:
            customer_id: Customer identifier
            days: Number of days to look back
        
        Returns:
            Savings summary dict with keys:
                - customer_id: str
                - period_days: int
                - migration_count: int
                - total_savings: float
                - avg_savings_per_migration: float
                - total_opportunities: int
        """
        if not self.client:
            logger.warning("ClickHouse client not available")
            return {
                "customer_id": customer_id,
                "period_days": days,
                "migration_count": 0,
                "total_savings": 0.0,
                "avg_savings_per_migration": 0.0,
                "total_opportunities": 0
            }
        
        try:
            result = self.client.execute(
                """
                SELECT
                    count() as migration_count,
                    sum(total_savings) as total_savings,
                    avg(total_savings) as avg_savings,
                    sum(opportunities_found) as total_opportunities
                FROM spot_migration_events
                WHERE customer_id = %(customer_id)s
                  AND timestamp >= now() - INTERVAL %(days)s DAY
                  AND success = 1
                """,
                {"customer_id": customer_id, "days": days}
            )
            
            if result:
                row = result[0]
                return {
                    "customer_id": customer_id,
                    "period_days": days,
                    "migration_count": row[0],
                    "total_savings": float(row[1]) if row[1] else 0.0,
                    "avg_savings_per_migration": float(row[2]) if row[2] else 0.0,
                    "total_opportunities": row[3]
                }
            
        except Exception as e:
            logger.error(f"Failed to query customer savings: {e}")
        
        return {
            "customer_id": customer_id,
            "period_days": days,
            "migration_count": 0,
            "total_savings": 0.0,
            "avg_savings_per_migration": 0.0,
            "total_opportunities": 0
        }
    
    async def get_recent_migrations(
        self,
        customer_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent migration events for customer.
        
        Args:
            customer_id: Customer identifier
            limit: Maximum number of events to return
        
        Returns:
            List of migration event dicts
        """
        if not self.client:
            logger.warning("ClickHouse client not available")
            return []
        
        try:
            result = self.client.execute(
                """
                SELECT
                    timestamp,
                    request_id,
                    workflow_phase,
                    total_savings,
                    success,
                    error_message
                FROM spot_migration_events
                WHERE customer_id = %(customer_id)s
                ORDER BY timestamp DESC
                LIMIT %(limit)s
                """,
                {"customer_id": customer_id, "limit": limit}
            )
            
            events = []
            for row in result:
                events.append({
                    "timestamp": row[0],
                    "request_id": row[1],
                    "workflow_phase": row[2],
                    "total_savings": float(row[3]),
                    "success": bool(row[4]),
                    "error_message": row[5]
                })
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to query recent migrations: {e}")
            return []
    
    async def insert_ri_optimization_event(
        self,
        event: Dict[str, Any]
    ) -> None:
        """
        Insert RI optimization event.
        
        Args:
            event: Event data dict with keys:
                - request_id: str
                - customer_id: str
                - cloud_provider: str
                - service_type: str
                - workflow_phase: str
                - instances_analyzed: int
                - stable_workloads_found: int
                - ris_recommended: int
                - total_upfront_cost: float
                - monthly_savings: float
                - annual_savings: float
                - three_year_savings: float
                - average_breakeven_months: float
                - one_year_ris: int
                - three_year_ris: int
                - success: int (0 or 1)
                - error_message: str
                - duration_ms: int
        """
        if not self.client:
            logger.warning("ClickHouse client not available, skipping RI event insert")
            return
        
        try:
            self.client.execute(
                "INSERT INTO ri_optimization_events VALUES",
                [{
                    "timestamp": event.get("timestamp", datetime.utcnow()),
                    "request_id": event["request_id"],
                    "customer_id": event["customer_id"],
                    "cloud_provider": event.get("cloud_provider", "aws"),
                    "service_type": event.get("service_type", "ec2"),
                    "workflow_phase": event.get("workflow_phase", "unknown"),
                    "instances_analyzed": event.get("instances_analyzed", 0),
                    "stable_workloads_found": event.get("stable_workloads_found", 0),
                    "ris_recommended": event.get("ris_recommended", 0),
                    "total_upfront_cost": event.get("total_upfront_cost", 0.0),
                    "monthly_savings": event.get("monthly_savings", 0.0),
                    "annual_savings": event.get("annual_savings", 0.0),
                    "three_year_savings": event.get("three_year_savings", 0.0),
                    "average_breakeven_months": event.get("average_breakeven_months", 0.0),
                    "one_year_ris": event.get("one_year_ris", 0),
                    "three_year_ris": event.get("three_year_ris", 0),
                    "success": event.get("success", 1),
                    "error_message": event.get("error_message", ""),
                    "duration_ms": event.get("duration_ms", 0)
                }]
            )
            
            logger.debug(
                f"Inserted RI optimization event for customer {event['customer_id']}",
                extra={"request_id": event["request_id"]}
            )
            
        except Exception as e:
            logger.error(f"Failed to insert RI optimization event: {e}")
    
    async def get_customer_ri_savings(
        self,
        customer_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get customer RI optimization savings summary.
        
        Args:
            customer_id: Customer identifier
            days: Number of days to look back
            
        Returns:
            Dictionary with RI savings summary
        """
        if not self.client:
            logger.warning("ClickHouse client not available")
            return {
                "optimization_count": 0,
                "total_annual_savings": 0.0,
                "total_ris_recommended": 0,
                "average_breakeven_months": 0.0
            }
        
        try:
            result = self.client.execute(
                """
                SELECT
                    COUNT(*) as optimization_count,
                    SUM(annual_savings) as total_annual_savings,
                    SUM(ris_recommended) as total_ris_recommended,
                    AVG(average_breakeven_months) as avg_breakeven
                FROM ri_optimization_events
                WHERE customer_id = %(customer_id)s
                    AND timestamp >= now() - INTERVAL %(days)s DAY
                    AND success = 1
                """,
                {"customer_id": customer_id, "days": days}
            )
            
            if result:
                row = result[0]
                return {
                    "optimization_count": int(row[0]),
                    "total_annual_savings": float(row[1] or 0),
                    "total_ris_recommended": int(row[2] or 0),
                    "average_breakeven_months": float(row[3] or 0)
                }
            
            return {
                "optimization_count": 0,
                "total_annual_savings": 0.0,
                "total_ris_recommended": 0,
                "average_breakeven_months": 0.0
            }
            
        except Exception as e:
            logger.error(f"Failed to query RI savings: {e}")
            return {
                "optimization_count": 0,
                "total_annual_savings": 0.0,
                "total_ris_recommended": 0,
                "average_breakeven_months": 0.0
            }
    
    async def insert_rightsizing_optimization_event(
        self,
        event: Dict[str, Any]
    ) -> None:
        """
        Insert right-sizing optimization event.
        
        Args:
            event: Event data dict with keys:
                - request_id, customer_id, cloud_provider, service_type
                - workflow_phase, instances_analyzed, optimization_candidates
                - over_provisioned_count, under_provisioned_count
                - recommendations_generated, downsize_count, upsize_count
                - family_change_count, total_current_cost, total_recommended_cost
                - monthly_savings, annual_savings, average_savings_percent
                - low_risk_count, medium_risk_count, high_risk_count
                - simple_migrations, moderate_migrations, complex_migrations
                - success, error_message, duration_ms
        """
        if not self.client:
            logger.warning("ClickHouse client not available, skipping right-sizing event insert")
            return
        
        try:
            self.client.execute(
                "INSERT INTO rightsizing_optimization_events VALUES",
                [{
                    "timestamp": event.get("timestamp", datetime.utcnow()),
                    "request_id": event["request_id"],
                    "customer_id": event["customer_id"],
                    "cloud_provider": event.get("cloud_provider", "aws"),
                    "service_type": event.get("service_type", "ec2"),
                    "workflow_phase": event.get("workflow_phase", "unknown"),
                    "instances_analyzed": event.get("instances_analyzed", 0),
                    "optimization_candidates": event.get("optimization_candidates", 0),
                    "over_provisioned_count": event.get("over_provisioned_count", 0),
                    "under_provisioned_count": event.get("under_provisioned_count", 0),
                    "recommendations_generated": event.get("recommendations_generated", 0),
                    "downsize_count": event.get("downsize_count", 0),
                    "upsize_count": event.get("upsize_count", 0),
                    "family_change_count": event.get("family_change_count", 0),
                    "total_current_cost": event.get("total_current_cost", 0.0),
                    "total_recommended_cost": event.get("total_recommended_cost", 0.0),
                    "monthly_savings": event.get("monthly_savings", 0.0),
                    "annual_savings": event.get("annual_savings", 0.0),
                    "average_savings_percent": event.get("average_savings_percent", 0.0),
                    "low_risk_count": event.get("low_risk_count", 0),
                    "medium_risk_count": event.get("medium_risk_count", 0),
                    "high_risk_count": event.get("high_risk_count", 0),
                    "simple_migrations": event.get("simple_migrations", 0),
                    "moderate_migrations": event.get("moderate_migrations", 0),
                    "complex_migrations": event.get("complex_migrations", 0),
                    "success": event.get("success", 1),
                    "error_message": event.get("error_message", ""),
                    "duration_ms": event.get("duration_ms", 0)
                }]
            )
            
            logger.debug(
                f"Inserted right-sizing optimization event for customer {event['customer_id']}",
                extra={"request_id": event["request_id"]}
            )
            
        except Exception as e:
            logger.error(f"Failed to insert right-sizing optimization event: {e}")
    
    async def get_customer_rightsizing_savings(
        self,
        customer_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get customer right-sizing optimization savings summary.
        
        Args:
            customer_id: Customer identifier
            days: Number of days to look back
            
        Returns:
            Dictionary with right-sizing savings summary
        """
        if not self.client:
            logger.warning("ClickHouse client not available")
            return {
                "optimization_count": 0,
                "total_annual_savings": 0.0,
                "total_recommendations": 0,
                "average_savings_percent": 0.0
            }
        
        try:
            result = self.client.execute(
                """
                SELECT
                    COUNT(*) as optimization_count,
                    SUM(annual_savings) as total_annual_savings,
                    SUM(recommendations_generated) as total_recommendations,
                    AVG(average_savings_percent) as avg_savings_percent
                FROM rightsizing_optimization_events
                WHERE customer_id = %(customer_id)s
                    AND timestamp >= now() - INTERVAL %(days)s DAY
                    AND success = 1
                """,
                {"customer_id": customer_id, "days": days}
            )
            
            if result:
                row = result[0]
                return {
                    "optimization_count": int(row[0]),
                    "total_annual_savings": float(row[1] or 0),
                    "total_recommendations": int(row[2] or 0),
                    "average_savings_percent": float(row[3] or 0)
                }
            
            return {
                "optimization_count": 0,
                "total_annual_savings": 0.0,
                "total_recommendations": 0,
                "average_savings_percent": 0.0
            }
            
        except Exception as e:
            logger.error(f"Failed to query right-sizing savings: {e}")
            return {
                "optimization_count": 0,
                "total_annual_savings": 0.0,
                "total_recommendations": 0,
                "average_savings_percent": 0.0
            }
    
    async def insert_analysis_engine_event(
        self,
        event: Dict[str, Any]
    ) -> None:
        """
        Insert analysis engine event.
        
        Args:
            event: Event data dict with analysis engine metrics
        """
        if not self.client:
            logger.warning("ClickHouse client not available, skipping analysis engine event insert")
            return
        
        try:
            self.client.execute(
                "INSERT INTO analysis_engine_events VALUES",
                [{
                    "timestamp": event.get("timestamp", datetime.utcnow()),
                    "request_id": event["request_id"],
                    "customer_id": event["customer_id"],
                    "cloud_provider": event.get("cloud_provider", "aws"),
                    "analysis_type": event.get("analysis_type", "idle,anomaly"),
                    "total_resources_analyzed": event.get("total_resources_analyzed", 0),
                    "idle_resources_found": event.get("idle_resources_found", 0),
                    "critical_idle_count": event.get("critical_idle_count", 0),
                    "high_idle_count": event.get("high_idle_count", 0),
                    "medium_idle_count": event.get("medium_idle_count", 0),
                    "low_idle_count": event.get("low_idle_count", 0),
                    "total_monthly_waste": event.get("total_monthly_waste", 0.0),
                    "total_annual_waste": event.get("total_annual_waste", 0.0),
                    "total_anomalies_found": event.get("total_anomalies_found", 0),
                    "cost_anomalies": event.get("cost_anomalies", 0),
                    "usage_anomalies": event.get("usage_anomalies", 0),
                    "config_anomalies": event.get("config_anomalies", 0),
                    "security_anomalies": event.get("security_anomalies", 0),
                    "critical_anomalies": event.get("critical_anomalies", 0),
                    "high_anomalies": event.get("high_anomalies", 0),
                    "success": event.get("success", 1),
                    "error_message": event.get("error_message", ""),
                    "duration_ms": event.get("duration_ms", 0)
                }]
            )
            
            logger.debug(
                f"Inserted analysis engine event for customer {event['customer_id']}",
                extra={"request_id": event["request_id"]}
            )
            
        except Exception as e:
            logger.error(f"Failed to insert analysis engine event: {e}")
    
    async def get_customer_waste_trends(
        self,
        customer_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get customer waste trends from analysis engine.
        
        Args:
            customer_id: Customer identifier
            days: Number of days to look back
            
        Returns:
            Dictionary with waste trends
        """
        if not self.client:
            logger.warning("ClickHouse client not available")
            return {
                "analysis_count": 0,
                "total_monthly_waste": 0.0,
                "avg_idle_resources": 0.0
            }
        
        try:
            result = self.client.execute(
                """
                SELECT
                    COUNT(*) as analysis_count,
                    SUM(total_monthly_waste) as total_waste,
                    AVG(idle_resources_found) as avg_idle
                FROM analysis_engine_events
                WHERE customer_id = %(customer_id)s
                    AND timestamp >= now() - INTERVAL %(days)s DAY
                    AND success = 1
                """,
                {"customer_id": customer_id, "days": days}
            )
            
            if result:
                row = result[0]
                return {
                    "analysis_count": int(row[0]),
                    "total_monthly_waste": float(row[1] or 0),
                    "avg_idle_resources": float(row[2] or 0)
                }
            
            return {
                "analysis_count": 0,
                "total_monthly_waste": 0.0,
                "avg_idle_resources": 0.0
            }
            
        except Exception as e:
            logger.error(f"Failed to query waste trends: {e}")
            return {
                "analysis_count": 0,
                "total_monthly_waste": 0.0,
                "avg_idle_resources": 0.0
            }


# Global instance
_metrics_instance: Optional[SpotMigrationMetrics] = None


def get_metrics_client() -> SpotMigrationMetrics:
    """
    Get or create global metrics client instance.
    
    Returns:
        SpotMigrationMetrics instance
    """
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = SpotMigrationMetrics()
    return _metrics_instance
