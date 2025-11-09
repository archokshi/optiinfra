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
        
        Queries leverage histogram_quantile / rate to provide actionable values:
        - Latency percentiles (p50/p95/p99)
        - Requests per second
        - Token throughput
        - Queue depth / running requests
        - Error rate
        """
        self.logger.info("Collecting performance metrics from Prometheus")
        metrics: List[PerformanceMetric] = []
        resource_id = f"{self.config.provider}-llm"
        resource_name = f"{self.config.provider.upper()} LLM"
        
        # PromQL queries keyed by the metric name we want to persist.
        # Using actual available metrics from Prometheus GPU exporter
        prom_queries = {
            "gpu_utilization": 'gpu_utilization_percent',
            "latency_p95": 'histogram_quantile(0.95, sum(rate(vllm_request_latency_seconds_bucket[5m])) by (le))',
            "throughput": 'vllm_throughput_prompts_per_second',
            "total_requests": 'vllm_requests_total',
            "tokens_generated": 'vllm_tokens_generated_total',
            "batch_latency_p95": 'histogram_quantile(0.95, sum(rate(load_batch_latency_seconds_bucket[5m])) by (le))',
        }
        
        results: Dict[str, Optional[float]] = {}
        for name, query in prom_queries.items():
            try:
                value = await self._query_prometheus(query)
                if value is not None:
                    results[name] = value
                else:
                    self.logger.debug(f"No data returned for {name}")
            except Exception as exc:  # pragma: no cover - defensive logging
                self.logger.warning(f"Failed to collect {name}: {exc}")
        
        # Fallback for latency metrics if histogram data is unavailable.
        if results.get("latency_p95") is None:
            self.logger.debug("Latency percentiles missing, checking for raw latency data")
            try:
                latency_count = await self._query_prometheus('vllm_request_latency_seconds_count')
                latency_sum = await self._query_prometheus('vllm_request_latency_seconds_sum')
                if latency_count and latency_sum and latency_count > 0:
                    avg_latency = latency_sum / latency_count
                    results["latency_p95"] = avg_latency * 1000  # Convert to ms
            except Exception as exc:  # pragma: no cover - defensive logging
                self.logger.debug(f"Failed to compute latency fallback: {exc}")
        
        # Fallback for batch latency if histogram data is unavailable.
        if results.get("batch_latency_p95") is None:
            self.logger.debug("Batch latency percentiles missing, checking for raw batch data")
            try:
                batch_count = await self._query_prometheus('load_batch_latency_seconds_count')
                batch_sum = await self._query_prometheus('load_batch_latency_seconds_sum')
                if batch_count and batch_sum and batch_count > 0:
                    avg_batch_latency = batch_sum / batch_count
                    results["batch_latency_p95"] = avg_batch_latency * 1000  # Convert to ms
            except Exception as exc:  # pragma: no cover - defensive logging
                self.logger.debug(f"Failed to compute batch latency fallback: {exc}")
        
        # Persist each metric that has a value.
        for metric_name, raw_value in results.items():
            if raw_value is None:
                continue
            
            unit = "count"
            value = raw_value
            metadata: Dict[str, Any] = {}
            
            if metric_name == "gpu_utilization":
                unit = "percent"
                metadata["percentage"] = raw_value
            elif metric_name.startswith("latency") or metric_name.startswith("batch_latency"):
                # Convert seconds to milliseconds for display.
                value = raw_value * 1000
                unit = "milliseconds"
            elif metric_name == "throughput":
                unit = "prompts_per_second"
            elif metric_name == "total_requests":
                unit = "requests"
            elif metric_name == "tokens_generated":
                unit = "tokens"
            
            metrics.append(PerformanceMetric(
                customer_id=self.config.customer_id,
                provider=self.config.provider,
                metric_type="compute",
                resource_id=resource_id,
                resource_name=resource_name,
                metric_name=metric_name,
                metric_value=value,
                unit=unit,
                metadata=metadata,
                workload_type="llm_inference"
            ))
        
        self.logger.info(f"Collected {len(metrics)} performance metrics")
        return metrics
    
    async def _collect_resource_metrics(self) -> List[ResourceMetric]:
        """
        Collect resource metrics from Prometheus GPU exporter
        
        Queries:
        - GPU utilization
        - GPU memory usage
        - GPU temperature
        - GPU power draw
        """
        self.logger.info("Collecting resource metrics from Prometheus")
        metrics: List[ResourceMetric] = []
        resource_id = f"{self.config.provider}-gpu"
        resource_name = f"{self.config.provider.upper()} GPU"
        
        async def query_value(name: str, promql: str) -> Optional[float]:
            """Helper to run a Prometheus query with contextual logging."""
            try:
                value = await self._query_prometheus(promql)
                if value is None:
                    self.logger.debug(f"No datapoint for resource metric {name}")
                return value
            except Exception as exc:  # pragma: no cover - defensive logging
                self.logger.warning(f"Failed PromQL for {name}: {exc}")
                return None
        
        # GPU Utilization
        gpu_util = await query_value("gpu_utilization", 'gpu_utilization_percent')
        if gpu_util is not None:
            metrics.append(ResourceMetric(
                customer_id=self.config.customer_id,
                provider=self.config.provider,
                metric_type="inventory",
                resource_id=resource_id,
                resource_name=resource_name,
                resource_type="gpu",
                status="active",
                region="unknown",
                utilization=max(gpu_util, 0),
                capacity=gpu_util,
                unit="percent",
                metadata={"metric_name": "gpu_utilization"}
            ))
        
        # GPU Memory Utilization
        gpu_mem_util = await query_value("gpu_memory_utilization", 'gpu_memory_utilization_percent')
        if gpu_mem_util is not None:
            metrics.append(ResourceMetric(
                customer_id=self.config.customer_id,
                provider=self.config.provider,
                metric_type="inventory",
                resource_id=resource_id,
                resource_name=resource_name,
                resource_type="gpu_memory",
                status="active",
                region="unknown",
                utilization=max(gpu_mem_util, 0),
                capacity=gpu_mem_util,
                unit="percent",
                metadata={"metric_name": "gpu_memory_utilization"}
            ))
        
        # GPU Memory Used/Total
        gpu_mem_used = await query_value("gpu_memory_used_bytes", 'gpu_memory_used_bytes')
        gpu_mem_total = await query_value("gpu_memory_total_bytes", 'gpu_memory_total_bytes')
        if gpu_mem_used is not None and gpu_mem_total is not None:
            used_gb = gpu_mem_used / (1024**3)
            total_gb = gpu_mem_total / (1024**3)
            metrics.append(ResourceMetric(
                customer_id=self.config.customer_id,
                provider=self.config.provider,
                metric_type="inventory",
                resource_id=resource_id,
                resource_name=resource_name,
                resource_type="gpu_memory",
                status="active",
                region="unknown",
                utilization=used_gb,
                capacity=total_gb,
                unit="gigabytes",
                metadata={
                    "metric_name": "gpu_memory_bytes",
                    "used_gb": used_gb,
                    "total_gb": total_gb
                }
            ))
        
        # GPU Temperature
        gpu_temp = await query_value("gpu_temperature_celsius", 'gpu_temperature_celsius')
        if gpu_temp is not None:
            metrics.append(ResourceMetric(
                customer_id=self.config.customer_id,
                provider=self.config.provider,
                metric_type="inventory",
                resource_id=resource_id,
                resource_name=resource_name,
                resource_type="gpu_temperature",
                status="active",
                region="unknown",
                utilization=gpu_temp,
                capacity=gpu_temp,
                unit="celsius",
                metadata={"metric_name": "gpu_temperature"}
            ))
        
        # GPU Power Draw
        gpu_power = await query_value("gpu_power_draw_watts", 'gpu_power_draw_watts')
        if gpu_power is not None:
            metrics.append(ResourceMetric(
                customer_id=self.config.customer_id,
                provider=self.config.provider,
                metric_type="inventory",
                resource_id=resource_id,
                resource_name=resource_name,
                resource_type="gpu_power",
                status="active",
                region="unknown",
                utilization=gpu_power,
                capacity=gpu_power,
                unit="watts",
                metadata={"metric_name": "gpu_power_draw"}
            ))
        self.logger.info(f"Collected {len(metrics)} resource metrics")
        return metrics
    
    async def _collect_application_metrics(self) -> List[ApplicationMetric]:
        """
        Collect application health and quality metrics from Prometheus
        
        Queries:
        - Service health status
        - Quality score
        - Load phase activity
        - GPU cost per hour
        """
        self.logger.info("Collecting application metrics from Prometheus")
        metrics = []
        
        # Define Prometheus queries for application metrics
        queries = {
            "service_health": 'gpu_exporter_success',
            "quality_score": 'vllm_quality_score',
            "load_phase_active": 'load_phase_active_minutes',
            "gpu_cost_hourly": 'gpu_cost_hourly_usd',
        }
        
        for metric_name, query in queries.items():
            try:
                value = await self._query_prometheus(query)
                if value is not None:
                    # Convert to appropriate score/percentage for health metrics
                    score = value
                    if metric_name == "service_health":
                        score = value * 100  # Convert 0/1 to 0/100 percentage
                    elif metric_name in ["quality_score", "load_phase_active"]:
                        score = value  # Keep as is for these metrics
                    
                    metrics.append(ApplicationMetric(
                        customer_id=self.config.customer_id,
                        provider=self.config.provider,
                        application_id=f"{self.config.provider}-gpu",
                        application_name=f"{self.config.provider.upper()} GPU Service",
                        metric_type="health" if metric_name == "service_health" else "quality",
                        score=score,
                        model_name="NVIDIA L4",
                        metadata={
                            "metric": metric_name,
                            "unit": "percent" if metric_name == "service_health" else "score",
                            "raw_value": value
                        }
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
            
            resource_id = f"{self.config.provider}-gpu"
            resource_name = f"{self.config.provider.upper()} GPU"
            
            gpu_util = dcgm_metrics.get("DCGM_FI_DEV_GPU_UTIL")
            fb_used = dcgm_metrics.get("DCGM_FI_DEV_FB_USED")
            fb_free = dcgm_metrics.get("DCGM_FI_DEV_FB_FREE")
            power_usage = dcgm_metrics.get("DCGM_FI_DEV_POWER_USAGE")
            temperature = dcgm_metrics.get("DCGM_FI_DEV_GPU_TEMP")
            sm_clock = dcgm_metrics.get("DCGM_FI_DEV_SM_CLOCK")
            mem_clock = dcgm_metrics.get("DCGM_FI_DEV_MEM_CLOCK")
            
            used_gb = (fb_used or 0) / 1024 if fb_used is not None else None
            total_gb = ((fb_used or 0) + (fb_free or 0)) / 1024 if fb_used is not None or fb_free is not None else None
            
            if gpu_util is not None:
                metadata = {
                    "metric_name": "gpu_utilization",
                    "gpu_memory_used_gb": used_gb,
                    "gpu_memory_total_gb": total_gb,
                    "power_usage_watts": power_usage,
                    "temperature_celsius": temperature,
                    "sm_clock_mhz": sm_clock,
                    "mem_clock_mhz": mem_clock,
                }
                metrics.append(ResourceMetric(
                    customer_id=self.config.customer_id,
                    provider=self.config.provider,
                    metric_type="inventory",
                    resource_id=resource_id,
                    resource_name=resource_name,
                    resource_type="gpu",
                    status="active",
                    region="unknown",
                    utilization=gpu_util,
                    capacity=gpu_util,
                    unit="percent",
                    metadata=metadata
                ))
            
            if used_gb is not None:
                metadata = {
                    "metric_name": "gpu_memory_used",
                    "gpu_memory_used_gb": used_gb,
                    "gpu_memory_total_gb": total_gb,
                }
                metrics.append(ResourceMetric(
                    customer_id=self.config.customer_id,
                    provider=self.config.provider,
                    metric_type="inventory",
                    resource_id=resource_id,
                    resource_name=resource_name,
                    resource_type="gpu",
                    status="active",
                    region="unknown",
                    utilization=0,
                    capacity=used_gb,
                    unit="gigabytes",
                    metadata=metadata
                ))
            
            if power_usage is not None:
                metrics.append(ResourceMetric(
                    customer_id=self.config.customer_id,
                    provider=self.config.provider,
                    metric_type="inventory",
                    resource_id=resource_id,
                    resource_name=resource_name,
                    resource_type="gpu",
                    status="active",
                    region="unknown",
                    utilization=0,
                    capacity=power_usage,
                    unit="watts",
                    metadata={"metric_name": "gpu_power_usage"}
                ))
            
            if temperature is not None:
                metrics.append(ResourceMetric(
                    customer_id=self.config.customer_id,
                    provider=self.config.provider,
                    metric_type="inventory",
                    resource_id=resource_id,
                    resource_name=resource_name,
                    resource_type="gpu",
                    status="active",
                    region="unknown",
                    utilization=0,
                    capacity=temperature,
                    unit="celsius",
                    metadata={"metric_name": "gpu_temperature"}
                ))
            
            self.logger.info(f"Collected {len(metrics)} GPU metrics")
            
        except Exception as e:
            self.logger.error(f"Failed to collect GPU metrics: {e}")
        
        return metrics
    
    async def _collect_cost_metrics(self) -> List[CostMetric]:
        """
        Calculate cost metrics based on runtime and hourly rate
        Plus collect GPU cost metrics from Prometheus
        
        For providers without billing APIs (like RunPod), we calculate costs based on:
        - Hourly rate (configured)
        - Runtime (hours since pod started)
        
        Additional GPU cost metrics from Prometheus:
        - GPU hourly rate
        - GPU accumulated cost
        - Savings potential
        
        Returns:
            List of CostMetric objects
        """
        self.logger.info("Calculating cost metrics based on runtime")
        metrics = []
        
        try:
            # Original cost calculation based on configured hourly rate
            if not self.config.hourly_rate:
                self.logger.warning("No hourly rate configured, skipping cost calculation")
            else:
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
            
            # Collect GPU cost metrics from Prometheus
            gpu_cost_queries = {
                "gpu_hourly_rate": "gpu_cost_hourly_usd",
                "gpu_accumulated_cost": "gpu_cost_accumulated_usd_total", 
                "savings_potential": "savings_potential_usd",
            }
            
            for cost_type, query in gpu_cost_queries.items():
                try:
                    value = await self._query_prometheus(query)
                    if value is not None:
                        # Map cost_type to appropriate cost_type for CostMetric
                        metric_cost_type = {
                            "gpu_hourly_rate": "gpu_hourly",
                            "gpu_accumulated_cost": "gpu_accumulated",
                            "savings_potential": "savings"
                        }.get(cost_type, cost_type)
                        
                        metrics.append(CostMetric(
                            timestamp=datetime.now(),
                            customer_id=self.config.customer_id,
                            provider=self.config.provider,
                            instance_id=f"{self.config.instance_id}-gpu",
                            cost_type=metric_cost_type,
                            amount=round(value, 4),
                            currency="USD",
                            metadata={"source": "prometheus_gpu_exporter"}
                        ))
                        
                        self.logger.info(f"Collected GPU cost metric {cost_type}: ${value:.4f}")
                except Exception as exc:
                    self.logger.debug(f"Failed to collect GPU cost metric {cost_type}: {exc}")
            
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
