"""
Generic Collector for Universal Cloud Provider Support

This collector works with ANY cloud provider or infrastructure that exposes:
1. Prometheus metrics (required)
2. DCGM GPU metrics (optional)
3. Provider API (optional, for billing data)

Supports: Vultr, RunPod, DigitalOcean, Linode, Hetzner, OVHcloud,
          Lambda Labs, CoreWeave, Paperspace, On-Premises, Kubernetes, Docker
"""

import asyncio
import httpx
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import urljoin

from .base import BaseCollector
from ..models.metrics import (
    CollectionResult,
    PerformanceMetric,
    ResourceMetric,
    ApplicationMetric,
    CostMetric,
    Provider
)
from ..storage.clickhouse_writer import ClickHouseWriter


logger = logging.getLogger(__name__)


class GenericCollectorConfig:
    """Configuration for Generic Collector"""
    
    def __init__(
        self,
        provider: str,
        customer_id: str,
        prometheus_url: str,
        dcgm_url: Optional[str] = None,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
        retry_attempts: int = 3,
        hourly_rate: Optional[float] = None,
        instance_id: Optional[str] = None,
        pod_start_time: Optional[datetime] = None
    ):
        """
        Initialize Generic Collector configuration
        
        Args:
            provider: Provider name (vultr, runpod, digitalocean, etc.)
            customer_id: Customer ID
            prometheus_url: Prometheus endpoint URL (required)
            dcgm_url: DCGM exporter URL (optional, for GPU metrics)
            api_url: Provider API URL (optional, for billing data)
            api_key: Provider API key (optional)
            timeout: HTTP request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
            hourly_rate: Hourly cost rate for cost calculation (e.g., 0.50 for RunPod L4)
            instance_id: Instance/Pod ID for cost tracking
            pod_start_time: When the pod/instance started (for cost calculation)
        """
        self.provider = provider
        self.customer_id = customer_id
        self.prometheus_url = prometheus_url.rstrip('/')
        self.dcgm_url = dcgm_url.rstrip('/') if dcgm_url else None
        self.api_url = api_url.rstrip('/') if api_url else None
        self.api_key = api_key
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.hourly_rate = hourly_rate
        self.instance_id = instance_id or f"{provider}-instance"
        self.pod_start_time = pod_start_time or datetime.now()
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.prometheus_url:
            raise ValueError("Prometheus URL is required")
        if not self.customer_id:
            raise ValueError("Customer ID is required")
        if not self.provider:
            raise ValueError("Provider name is required")
        return True


class GenericCollector(BaseCollector):
    """
    Universal collector for any cloud provider
    
    Collection Strategy:
    1. Prometheus metrics (universal) - Performance, GPU, Application
    2. DCGM metrics (optional) - Detailed GPU metrics
    3. Provider API (optional) - Billing and cost data
    
    This collector can work in three modes:
    - Prometheus-only: Just Prometheus metrics (minimum viable)
    - Prometheus + DCGM: Add detailed GPU metrics
    - Full: Prometheus + DCGM + Provider API (complete)
    """
    
    def __init__(self, config: GenericCollectorConfig):
        """
        Initialize Generic Collector
        
        Args:
            config: GenericCollectorConfig instance
        """
        # Initialize base collector with minimal params
        super().__init__(
            api_key=config.api_key or "prometheus-only",
            customer_id=config.customer_id
        )
        
        self.config = config
        self.config.validate()
        
        # HTTP client for async requests
        self.client = None
        
        self.logger.info(
            f"Initialized Generic Collector for {config.provider} "
            f"(customer: {config.customer_id})"
        )
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return self.config.provider
    
    def get_data_type(self) -> str:
        """Get data type - generic collector handles all types"""
        return "all"
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.client = httpx.AsyncClient(
            timeout=self.config.timeout,
            follow_redirects=True
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.aclose()
    
    def validate_credentials(self) -> bool:
        """
        Validate credentials
        
        For Generic Collector, we validate by testing Prometheus connection
        """
        try:
            import requests
            response = requests.get(
                f"{self.config.prometheus_url}/api/v1/status/config",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Credential validation failed: {e}")
            return False
    
    def collect(self) -> CollectionResult:
        """
        Synchronous collect method (required by BaseCollector)
        
        This wraps the async collect_all_metrics method
        """
        try:
            # Check if there's already a running event loop
            try:
                loop = asyncio.get_running_loop()
                # If we're in an async context, we need to run in a thread pool
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.collect_all_metrics())
                    return future.result()
            except RuntimeError:
                # No running loop, safe to use asyncio.run()
                return asyncio.run(self.collect_all_metrics())
        except Exception as e:
            return self.handle_error(e)
    
    async def collect_all_metrics(self) -> CollectionResult:
        """
        Collect all metrics from all available sources and write to ClickHouse
        
        Returns:
            CollectionResult with aggregated metrics
        """
        self.log_collection_start()
        started_at = datetime.now()
        total_records = 0
        errors = []
        
        # Initialize ClickHouse writer
        clickhouse_writer = ClickHouseWriter()
        
        try:
            async with self:
                # Collect from all sources in parallel
                tasks = [
                    self._collect_performance_metrics(),
                    self._collect_resource_metrics(),
                    self._collect_application_metrics()
                ]
                
                # Add cost metrics if hourly rate is configured
                if self.config.hourly_rate:
                    tasks.append(self._collect_cost_metrics())
                
                # Add GPU metrics if DCGM URL provided
                if self.config.dcgm_url:
                    tasks.append(self._collect_gpu_metrics())
                
                # Execute all collections in parallel
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results and write to ClickHouse
                for result in results:
                    if isinstance(result, Exception):
                        errors.append(str(result))
                        self.logger.error(f"Collection error: {result}")
                    elif isinstance(result, list) and len(result) > 0:
                        # Write metrics to ClickHouse based on type
                        if isinstance(result[0], PerformanceMetric):
                            written = clickhouse_writer.write_performance_metrics(result)
                            self.logger.info(f"Wrote {written} performance metrics to ClickHouse")
                            total_records += written
                        elif isinstance(result[0], ResourceMetric):
                            written = clickhouse_writer.write_resource_metrics(result)
                            self.logger.info(f"Wrote {written} resource metrics to ClickHouse")
                            total_records += written
                        elif isinstance(result[0], ApplicationMetric):
                            written = clickhouse_writer.write_application_metrics(result)
                            self.logger.info(f"Wrote {written} application metrics to ClickHouse")
                            total_records += written
                        elif isinstance(result[0], CostMetric):
                            written = clickhouse_writer.write_cost_metrics(result)
                            self.logger.info(f"Wrote {written} cost metrics to ClickHouse")
                            total_records += written
                
                # Create collection result
                completed_at = datetime.now()
                success = len(errors) == 0 or total_records > 0
                
                result = CollectionResult(
                    customer_id=self.config.customer_id,
                    provider=self.config.provider,
                    data_type="all",
                    success=success,
                    records_collected=total_records,
                    started_at=started_at,
                    completed_at=completed_at,
                    error_message="; ".join(errors) if errors else None,
                    metadata={
                        "prometheus_url": self.config.prometheus_url,
                        "dcgm_enabled": self.config.dcgm_url is not None,
                        "api_enabled": self.config.api_key is not None
                    }
                )
                
                self.log_collection_end(result)
                return result
                
        except Exception as e:
            return self.handle_error(e)
        finally:
            # Close ClickHouse connection
            clickhouse_writer.close()
    
    async def _collect_performance_metrics(self) -> List[PerformanceMetric]:
        """
        Collect performance metrics from Prometheus
        
        Queries:
        - Request latency (P50, P95, P99)
        - Throughput (requests per second)
        - Queue size
        - Tokens per second
        """
        self.logger.info("Collecting performance metrics from Prometheus")
        metrics = []
        
        # Define Prometheus queries for vLLM/LLM metrics
        # Use simple counter/gauge queries that don't require rate calculations
        queries = {
            "request_count": 'vllm:e2e_request_latency_seconds_count',
            "latency_sum": 'vllm:e2e_request_latency_seconds_sum',
            "queue_size": 'vllm:num_requests_waiting',
            "requests_running": 'vllm:num_requests_running',
            "tokens_generated_total": 'vllm:generation_tokens_total',
            "tokens_prompt_total": 'vllm:prompt_tokens_total',
            "kv_cache_usage": 'vllm:kv_cache_usage_perc',
            "request_success_total": 'vllm:request_success_total',
        }
        
        for metric_name, query in queries.items():
            try:
                value = await self._query_prometheus(query)
                if value is not None:
                    metrics.append(PerformanceMetric(
                        customer_id=self.config.customer_id,
                        provider=self.config.provider,
                        metric_type="compute",
                        resource_id=f"{self.config.provider}-llm",
                        resource_name=f"{self.config.provider.upper()} LLM",
                        metric_name=metric_name,
                        metric_value=value,
                        unit="seconds" if "latency" in metric_name else "count",
                        workload_type="llm_inference"
                    ))
            except Exception as e:
                self.logger.warning(f"Failed to collect {metric_name}: {e}")
        
        self.logger.info(f"Collected {len(metrics)} performance metrics")
        return metrics
    
    async def _collect_resource_metrics(self) -> List[ResourceMetric]:
        """
        Collect resource metrics from Prometheus
        
        Queries:
        - CPU utilization
        - Memory usage
        - Disk I/O
        - Network I/O
        """
        self.logger.info("Collecting resource metrics from Prometheus")
        metrics = []
        
        # Define Prometheus queries for system metrics
        queries = {
            "cpu_utilization": '100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
            "memory_used": 'node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes',
            "memory_total": 'node_memory_MemTotal_bytes',
            "disk_read_bytes": 'rate(node_disk_read_bytes_total[5m])',
            "disk_write_bytes": 'rate(node_disk_written_bytes_total[5m])',
            "network_receive_bytes": 'rate(node_network_receive_bytes_total[5m])',
            "network_transmit_bytes": 'rate(node_network_transmit_bytes_total[5m])',
        }
        
        for metric_name, query in queries.items():
            try:
                value = await self._query_prometheus(query)
                if value is not None:
                    # Calculate utilization for memory
                    if metric_name == "memory_used":
                        memory_total = await self._query_prometheus(queries["memory_total"])
                        utilization = (value / memory_total * 100) if memory_total else 0
                    else:
                        utilization = value if "utilization" in metric_name else 0
                    
                    metrics.append(ResourceMetric(
                        customer_id=self.config.customer_id,
                        provider=self.config.provider,
                        metric_type="inventory",
                        resource_id=f"{self.config.provider}-instance",
                        resource_name=f"{self.config.provider.upper()} Instance",
                        resource_type="instance",
                        status="active",
                        region="unknown",
                        utilization=utilization,
                        capacity=value,
                        unit="percent" if "utilization" in metric_name else "bytes"
                    ))
            except Exception as e:
                self.logger.warning(f"Failed to collect {metric_name}: {e}")
        
        self.logger.info(f"Collected {len(metrics)} resource metrics")
        return metrics
    
    async def _collect_application_metrics(self) -> List[ApplicationMetric]:
        """
        Collect application quality metrics from Prometheus
        
        Queries:
        - Request success rate
        - Error rate
        - Response quality (if available)
        """
        self.logger.info("Collecting application metrics from Prometheus")
        metrics = []
        
        # Define Prometheus queries for application metrics
        queries = {
            "success_rate": 'rate(vllm_request_success_total[5m]) / (rate(vllm_request_success_total[5m]) + rate(vllm_request_failure_total[5m]))',
            "error_rate": 'rate(vllm_request_failure_total[5m]) / (rate(vllm_request_success_total[5m]) + rate(vllm_request_failure_total[5m]))',
        }
        
        for metric_name, query in queries.items():
            try:
                value = await self._query_prometheus(query)
                if value is not None:
                    metrics.append(ApplicationMetric(
                        customer_id=self.config.customer_id,
                        provider=self.config.provider,
                        application_id=f"{self.config.provider}-llm",
                        application_name=f"{self.config.provider.upper()} LLM",
                        metric_type="quality",
                        score=value * 100,  # Convert to percentage
                        model_name="unknown",
                        metadata={"metric": metric_name}
                    ))
            except Exception as e:
                self.logger.warning(f"Failed to collect {metric_name}: {e}")
        
        self.logger.info(f"Collected {len(metrics)} application metrics")
        return metrics
    
    async def _collect_gpu_metrics(self) -> List[ResourceMetric]:
        """
        Collect GPU metrics from DCGM exporter
        
        Metrics:
        - GPU utilization
        - GPU memory used/total
        - GPU power usage
        - GPU temperature
        """
        if not self.config.dcgm_url:
            return []
        
        self.logger.info("Collecting GPU metrics from DCGM")
        metrics = []
        
        try:
            # Scrape DCGM metrics endpoint
            response = await self.client.get(f"{self.config.dcgm_url}/metrics")
            response.raise_for_status()
            
            # Parse Prometheus format metrics
            dcgm_metrics = self._parse_prometheus_text(response.text)
            
            # Extract GPU metrics
            gpu_metrics_map = {
                "DCGM_FI_DEV_GPU_UTIL": ("gpu_utilization", "percent"),
                "DCGM_FI_DEV_FB_USED": ("gpu_memory_used", "MB"),
                "DCGM_FI_DEV_FB_FREE": ("gpu_memory_free", "MB"),
                "DCGM_FI_DEV_POWER_USAGE": ("gpu_power_usage", "watts"),
                "DCGM_FI_DEV_GPU_TEMP": ("gpu_temperature", "celsius"),
                "DCGM_FI_DEV_SM_CLOCK": ("gpu_sm_clock", "MHz"),
                "DCGM_FI_DEV_MEM_CLOCK": ("gpu_mem_clock", "MHz"),
            }
            
            for dcgm_name, (metric_name, unit) in gpu_metrics_map.items():
                if dcgm_name in dcgm_metrics:
                    value = dcgm_metrics[dcgm_name]
                    metrics.append(ResourceMetric(
                        customer_id=self.config.customer_id,
                        provider=self.config.provider,
                        metric_type="inventory",
                        resource_id=f"{self.config.provider}-gpu",
                        resource_name=f"{self.config.provider.upper()} GPU",
                        resource_type="gpu",
                        status="active",
                        region="unknown",
                        utilization=value if "util" in metric_name else 0,
                        capacity=value,
                        unit=unit
                    ))
            
            self.logger.info(f"Collected {len(metrics)} GPU metrics")
            
        except Exception as e:
            self.logger.error(f"Failed to collect GPU metrics: {e}")
        
        return metrics
    
    async def _collect_cost_metrics(self) -> List[CostMetric]:
        """
        Calculate cost metrics based on runtime and hourly rate
        
        For providers without billing APIs (like RunPod), we calculate costs based on:
        - Hourly rate (configured)
        - Runtime (hours since pod started)
        
        Returns:
            List of CostMetric objects
        """
        self.logger.info("Calculating cost metrics based on runtime")
        metrics = []
        
        try:
            if not self.config.hourly_rate:
                self.logger.warning("No hourly rate configured, skipping cost calculation")
                return metrics
            
            # Calculate hours running
            now = datetime.now()
            runtime_hours = (now - self.config.pod_start_time).total_seconds() / 3600
            
            # Calculate total cost
            total_cost = self.config.hourly_rate * runtime_hours
            
            # Create cost metric
            metrics.append(CostMetric(
                timestamp=now,
                customer_id=self.config.customer_id,
                provider=self.config.provider,
                instance_id=self.config.instance_id,
                cost_type="compute",
                amount=round(total_cost, 4),
                currency="USD"
            ))
            
            self.logger.info(f"Calculated cost: ${total_cost:.4f} ({runtime_hours:.2f} hours @ ${self.config.hourly_rate}/hour)")
            
        except Exception as e:
            self.logger.error(f"Failed to calculate cost metrics: {e}")
        
        return metrics
    
    async def _query_prometheus(self, query: str) -> Optional[float]:
        """
        Query Prometheus and return single value
        
        Args:
            query: PromQL query string
        
        Returns:
            Float value or None if query failed
        """
        try:
            url = f"{self.config.prometheus_url}/api/v1/query"
            params = {"query": query}
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") == "success":
                result = data.get("data", {}).get("result", [])
                if result and len(result) > 0:
                    value = result[0].get("value", [None, None])[1]
                    if value is not None and value != "NaN":
                        try:
                            return float(value)
                        except (ValueError, TypeError):
                            self.logger.warning(f"Could not convert value to float: {value} for query: {query}")
                            return None
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Prometheus query failed: {query} - {e}")
            return None
    
    def _parse_prometheus_text(self, text: str) -> Dict[str, float]:
        """
        Parse Prometheus text format metrics
        
        Args:
            text: Prometheus metrics text
        
        Returns:
            Dict of metric_name -> value
        """
        metrics = {}
        
        for line in text.split('\n'):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            try:
                # Parse metric line: metric_name{labels} value timestamp
                parts = line.split()
                if len(parts) >= 2:
                    metric_full = parts[0]
                    value = float(parts[1])
                    
                    # Extract metric name (before {)
                    metric_name = metric_full.split('{')[0]
                    metrics[metric_name] = value
                    
            except (ValueError, IndexError) as e:
                self.logger.debug(f"Failed to parse metric line: {line} - {e}")
                continue
        
        return metrics
    
    async def _retry_request(self, func, *args, **kwargs):
        """
        Retry a request with exponential backoff
        
        Args:
            func: Async function to retry
            *args, **kwargs: Arguments to pass to function
        
        Returns:
            Function result
        """
        for attempt in range(self.config.retry_attempts):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.config.retry_attempts - 1:
                    raise
                
                wait_time = 2 ** attempt  # Exponential backoff
                self.logger.warning(
                    f"Request failed (attempt {attempt + 1}/{self.config.retry_attempts}), "
                    f"retrying in {wait_time}s: {e}"
                )
                await asyncio.sleep(wait_time)
