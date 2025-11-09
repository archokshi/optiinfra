"""
ClickHouse writer for metrics data
"""
from typing import List, Dict, Any
import logging
from datetime import datetime
import json

from clickhouse_driver import Client

from ..config import config
from ..models.metrics import CostMetric, PerformanceMetric, ResourceMetric, ApplicationMetric
from ..models.runpod import (
    RunPodBillingSnapshot,
    RunPodEndpointConfig,
    RunPodEndpointHealthSnapshot,
    RunPodJobTelemetry,
    RunPodPodSnapshot,
)

logger = logging.getLogger(__name__)


class ClickHouseWriter:
    """
    Writes metrics data to ClickHouse
    """
    
    def __init__(self):
        """Initialize ClickHouse writer"""
        self.client = None
        self._connect()
    
    def _connect(self):
        """Connect to ClickHouse"""
        try:
            self.client = Client(
                host=config.CLICKHOUSE_HOST,
                port=config.CLICKHOUSE_PORT,
                database=config.CLICKHOUSE_DATABASE,
                user=config.CLICKHOUSE_USER,
                password=config.CLICKHOUSE_PASSWORD
            )
            logger.info(f"Connected to ClickHouse at {config.CLICKHOUSE_HOST}:{config.CLICKHOUSE_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to ClickHouse: {e}")
            raise
    
    def write_cost_metrics(self, metrics: List[CostMetric]) -> int:
        """
        Write cost metrics to ClickHouse
        
        Args:
            metrics: List of CostMetric objects
        
        Returns:
            Number of records written
        """
        if not metrics:
            return 0
        
        try:
            # Prepare data for batch insert
            data = []
            for metric in metrics:
                data.append((
                    metric.timestamp,
                    metric.customer_id,
                    metric.provider,
                    metric.instance_id or '',
                    metric.cost_type,
                    metric.amount,
                    metric.currency
                ))
            
            # Insert into ClickHouse
            query = """
                INSERT INTO cost_metrics 
                (timestamp, customer_id, provider, instance_id, cost_type, amount, currency)
                VALUES
            """
            
            self.client.execute(query, data)
            logger.info(f"Wrote {len(data)} cost metrics to ClickHouse")
            return len(data)
            
        except Exception as e:
            logger.error(f"Failed to write cost metrics: {e}")
            raise
    
    def write_performance_metrics(self, metrics: List[PerformanceMetric]) -> int:
        """
        Write performance metrics to ClickHouse (Phase 6.4 Enhanced)
        
        Args:
            metrics: List of PerformanceMetric objects
        
        Returns:
            Number of records written
        """
        if not metrics:
            return 0
        
        try:
            data = []
            for metric in metrics:
                # Convert metadata dict to JSON string if it's a dict
                metadata_str = ''
                if metric.metadata:
                    metadata_str = json.dumps(metric.metadata)
                
                data.append((
                    metric.timestamp,
                    metric.customer_id,
                    metric.provider,
                    metric.metric_type,
                    metric.resource_id,
                    metric.resource_name,
                    metric.metric_name,
                    metric.metric_value,
                    metric.unit,
                    metadata_str,
                    metric.workload_type or ''
                ))
            
            query = """
                INSERT INTO performance_metrics 
                (timestamp, customer_id, provider, metric_type, resource_id, resource_name, 
                 metric_name, metric_value, unit, metadata, workload_type)
                VALUES
            """
            
            self.client.execute(query, data)
            logger.info(f"Wrote {len(data)} performance metrics to ClickHouse")
            return len(data)
            
        except Exception as e:
            logger.error(f"Failed to write performance metrics: {e}")
            raise
    
    def write_resource_metrics(self, metrics: List[ResourceMetric]) -> int:
        """
        Write resource metrics to ClickHouse (Phase 6.4 Enhanced)
        
        Args:
            metrics: List of ResourceMetric objects
        
        Returns:
            Number of records written
        """
        if not metrics:
            return 0
        
        try:
            data = []
            for metric in metrics:
                metadata_str = ""
                if metric.metadata:
                    try:
                        metadata_str = json.dumps(metric.metadata)
                    except (TypeError, ValueError):
                        logger.debug(f"Unable to JSON encode metadata for resource metric: {metric.metadata}")
                        metadata_str = ""
                
                data.append((
                    metric.timestamp,
                    metric.customer_id,
                    metric.provider,
                    metric.metric_type,
                    metric.resource_id,
                    metric.resource_name,
                    metric.resource_type,
                    metric.status,
                    metric.region,
                    metric.utilization,
                    metric.capacity,
                    metric.unit,
                    metadata_str
                ))
            
            query = """
                INSERT INTO resource_metrics 
                (timestamp, customer_id, provider, metric_type, resource_id, resource_name,
                 resource_type, status, region, utilization, capacity, unit, metadata)
                VALUES
            """
            
            self.client.execute(query, data)
            logger.info(f"Wrote {len(data)} resource metrics to ClickHouse")
            return len(data)
            
        except Exception as e:
            logger.error(f"Failed to write resource metrics: {e}")
            raise
    
    def write_application_metrics(self, metrics: List[ApplicationMetric]) -> int:
        """
        Write application metrics to ClickHouse (Phase 6.5 Enhanced)
        
        Args:
            metrics: List of ApplicationMetric objects
        
        Returns:
            Number of records written
        """
        if not metrics:
            return 0
        
        try:
            data = []
            for metric in metrics:
                # Convert metadata dict to JSON string if it's a dict
                metadata_str = ''
                if metric.metadata:
                    import json
                    metadata_str = json.dumps(metric.metadata)
                
                data.append((
                    metric.timestamp,
                    metric.customer_id,
                    metric.provider,
                    metric.application_id,
                    metric.application_name,
                    metric.metric_type,
                    metric.score,
                    metric.details or '',
                    metric.model_name,
                    metric.prompt_text or '',
                    metric.response_text or '',
                    metadata_str
                ))
            
            query = """
                INSERT INTO application_metrics 
                (timestamp, customer_id, provider, application_id, application_name,
                 metric_type, score, details, model_name, prompt_text, response_text, metadata)
                VALUES
            """
            
            self.client.execute(query, data)
            logger.info(f"Wrote {len(data)} application metrics to ClickHouse")
            return len(data)
            
        except Exception as e:
            logger.error(f"Failed to write application metrics: {e}")
            raise

    # ------------------------------------------------------------------
    # RunPod staging writers
    # ------------------------------------------------------------------

    def write_runpod_pods(self, snapshots: List[RunPodPodSnapshot]) -> int:
        if not snapshots:
            return 0

        rows = [snapshot.to_row() for snapshot in snapshots]
        query = """
            INSERT INTO runpod_pods (
                snapshot_ts,
                customer_id,
                pod_id,
                gpu_type_id,
                gpu_count,
                vcpu_count,
                memory_gb,
                region,
                status,
                uptime_seconds,
                cost_per_hour,
                metadata_json
            ) VALUES
        """
        try:
            self.client.execute(query, rows)
            logger.info("Wrote %s RunPod pod snapshots", len(rows))
            return len(rows)
        except Exception as exc:
            logger.error("Failed to write RunPod pod snapshots: %s", exc)
            raise

    def write_runpod_endpoints(self, configs: List[RunPodEndpointConfig]) -> int:
        if not configs:
            return 0

        rows = [config.to_row() for config in configs]
        query = """
            INSERT INTO runpod_endpoints (
                snapshot_ts,
                customer_id,
                endpoint_id,
                name,
                compute_type,
                gpu_type_ids,
                workers_min,
                workers_max,
                scaler_type,
                idle_timeout,
                execution_timeout_ms,
                metadata_json
            ) VALUES
        """
        try:
            self.client.execute(query, rows)
            logger.info("Wrote %s RunPod endpoint configs", len(rows))
            return len(rows)
        except Exception as exc:
            logger.error("Failed to write RunPod endpoint configs: %s", exc)
            raise

    def write_runpod_jobs(self, jobs: List[RunPodJobTelemetry]) -> int:
        if not jobs:
            return 0

        rows = [job.to_row() for job in jobs]
        query = """
            INSERT INTO runpod_jobs (
                observed_ts,
                customer_id,
                endpoint_id,
                job_id,
                status,
                delay_ms,
                execution_ms,
                input_tokens,
                output_tokens,
                throughput,
                metadata_json
            ) VALUES
        """
        try:
            self.client.execute(query, rows)
            logger.info("Wrote %s RunPod job telemetry rows", len(rows))
            return len(rows)
        except Exception as exc:
            logger.error("Failed to write RunPod job telemetry: %s", exc)
            raise

    def write_runpod_endpoint_health(self, snapshots: List[RunPodEndpointHealthSnapshot]) -> int:
        if not snapshots:
            return 0

        rows = [snapshot.to_row() for snapshot in snapshots]
        query = """
            INSERT INTO runpod_endpoint_health (
                observed_ts,
                customer_id,
                endpoint_id,
                jobs_completed,
                jobs_failed,
                jobs_in_progress,
                jobs_in_queue,
                workers_idle,
                workers_running,
                workers_throttled,
                metadata_json
            ) VALUES
        """
        try:
            self.client.execute(query, rows)
            logger.info("Wrote %s RunPod endpoint health snapshots", len(rows))
            return len(rows)
        except Exception as exc:
            logger.error("Failed to write RunPod endpoint health snapshots: %s", exc)
            raise

    def write_runpod_billing(self, snapshots: List[RunPodBillingSnapshot]) -> int:
        if not snapshots:
            return 0

        rows = [snapshot.to_row() for snapshot in snapshots]
        query = """
            INSERT INTO runpod_billing_snapshots (
                snapshot_ts,
                customer_id,
                current_spend_per_hr,
                lifetime_spend,
                balance,
                spend_breakdown_json
            ) VALUES
        """
        try:
            self.client.execute(query, rows)
            logger.info("Wrote %s RunPod billing snapshots", len(rows))
            return len(rows)
        except Exception as exc:
            logger.error("Failed to write RunPod billing snapshots: %s", exc)
            raise
    
    def close(self):
        """Close ClickHouse connection"""
        if self.client:
            self.client.disconnect()
            logger.info("Disconnected from ClickHouse")
