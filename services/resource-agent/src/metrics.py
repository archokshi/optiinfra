"""
Resource Agent Specific Metrics

Metrics for tracking resource utilization and scaling.
"""

from prometheus_client import Counter, Gauge, Histogram, REGISTRY
from shared.utils.prometheus_metrics import BaseMetrics


class ResourceAgentMetrics(BaseMetrics):
    """Metrics specific to the Resource Agent"""
    
    def __init__(self):
        super().__init__('resource-agent', REGISTRY)
        
        # GPU metrics
        self.gpu_utilization = Gauge(
            'gpu_utilization',
            'GPU utilization percentage (0-1)',
            ['gpu_id', 'node'],
            registry=self.registry
        )
        
        self.gpu_memory_used_bytes = Gauge(
            'gpu_memory_used_bytes',
            'GPU memory used in bytes',
            ['gpu_id', 'node'],
            registry=self.registry
        )
        
        self.gpu_memory_total_bytes = Gauge(
            'gpu_memory_total_bytes',
            'Total GPU memory in bytes',
            ['gpu_id', 'node'],
            registry=self.registry
        )
        
        self.gpu_temperature_celsius = Gauge(
            'gpu_temperature_celsius',
            'GPU temperature in Celsius',
            ['gpu_id', 'node'],
            registry=self.registry
        )
        
        self.gpu_power_watts = Gauge(
            'gpu_power_watts',
            'GPU power consumption in watts',
            ['gpu_id', 'node'],
            registry=self.registry
        )
        
        # Scaling metrics
        self.scaling_events_total = Counter(
            'scaling_events_total',
            'Total scaling events',
            ['direction', 'resource_type'],  # direction: up, down
            registry=self.registry
        )
        
        self.active_instances = Gauge(
            'active_instances',
            'Number of active instances',
            ['resource_type'],
            registry=self.registry
        )
        
        self.scaling_duration_seconds = Histogram(
            'scaling_duration_seconds',
            'Duration of scaling operations in seconds',
            ['direction'],
            buckets=(1, 5, 10, 30, 60, 120, 300),
            registry=self.registry
        )
        
        # Resource consolidation
        self.resource_consolidation_ratio = Gauge(
            'resource_consolidation_ratio',
            'Resource consolidation ratio (0-1)',
            registry=self.registry
        )
        
        self.consolidation_savings_total = Counter(
            'consolidation_savings_total',
            'Total savings from resource consolidation (USD)',
            registry=self.registry
        )
        
        # CPU metrics
        self.cpu_utilization = Gauge(
            'cpu_utilization',
            'CPU utilization percentage (0-1)',
            ['node'],
            registry=self.registry
        )
        
        self.cpu_cores_total = Gauge(
            'cpu_cores_total',
            'Total CPU cores',
            ['node'],
            registry=self.registry
        )
        
        # Memory metrics
        self.memory_used_bytes = Gauge(
            'memory_used_bytes',
            'Memory used in bytes',
            ['node'],
            registry=self.registry
        )
        
        self.memory_total_bytes = Gauge(
            'memory_total_bytes',
            'Total memory in bytes',
            ['node'],
            registry=self.registry
        )
        
        # Disk metrics
        self.disk_io_read_bytes_total = Counter(
            'disk_io_read_bytes_total',
            'Total disk read bytes',
            ['node'],
            registry=self.registry
        )
        
        self.disk_io_write_bytes_total = Counter(
            'disk_io_write_bytes_total',
            'Total disk write bytes',
            ['node'],
            registry=self.registry
        )
        
        # Network metrics
        self.network_receive_bytes_total = Counter(
            'network_receive_bytes_total',
            'Total network bytes received',
            ['node'],
            registry=self.registry
        )
        
        self.network_transmit_bytes_total = Counter(
            'network_transmit_bytes_total',
            'Total network bytes transmitted',
            ['node'],
            registry=self.registry
        )
        
        # KVOptkit metrics
        self.kv_optimization_events_total = Counter(
            'kv_optimization_events_total',
            'Total KV cache optimization events',
            ['optimization_type'],
            registry=self.registry
        )
        
        self.kv_memory_saved_bytes = Counter(
            'kv_memory_saved_bytes',
            'Total memory saved by KV optimizations',
            registry=self.registry
        )
        
        # Resource cost
        self.resource_cost_per_hour = Gauge(
            'resource_cost_per_hour',
            'Resource cost per hour (USD)',
            ['resource_type'],
            registry=self.registry
        )
        
        self.idle_resource_cost_per_hour = Gauge(
            'idle_resource_cost_per_hour',
            'Cost of idle resources per hour (USD)',
            ['resource_type'],
            registry=self.registry
        )
    
    def update_gpu_metrics(self, gpu_id: str, node: str, utilization: float, 
                          memory_used: int, memory_total: int, 
                          temperature: float, power: float):
        """Update GPU metrics"""
        self.gpu_utilization.labels(gpu_id=gpu_id, node=node).set(utilization)
        self.gpu_memory_used_bytes.labels(gpu_id=gpu_id, node=node).set(memory_used)
        self.gpu_memory_total_bytes.labels(gpu_id=gpu_id, node=node).set(memory_total)
        self.gpu_temperature_celsius.labels(gpu_id=gpu_id, node=node).set(temperature)
        self.gpu_power_watts.labels(gpu_id=gpu_id, node=node).set(power)
    
    def record_scaling_event(self, direction: str, resource_type: str, duration: float):
        """Record a scaling event"""
        self.scaling_events_total.labels(
            direction=direction,
            resource_type=resource_type
        ).inc()
        
        self.scaling_duration_seconds.labels(direction=direction).observe(duration)
    
    def update_active_instances(self, resource_type: str, count: int):
        """Update active instance count"""
        self.active_instances.labels(resource_type=resource_type).set(count)
    
    def update_consolidation(self, ratio: float, savings: float):
        """Update resource consolidation metrics"""
        self.resource_consolidation_ratio.set(ratio)
        if savings > 0:
            self.consolidation_savings_total.inc(savings)
    
    def update_cpu_metrics(self, node: str, utilization: float, cores: int):
        """Update CPU metrics"""
        self.cpu_utilization.labels(node=node).set(utilization)
        self.cpu_cores_total.labels(node=node).set(cores)
    
    def update_memory_metrics(self, node: str, used: int, total: int):
        """Update memory metrics"""
        self.memory_used_bytes.labels(node=node).set(used)
        self.memory_total_bytes.labels(node=node).set(total)
    
    def record_disk_io(self, node: str, read_bytes: int, write_bytes: int):
        """Record disk I/O"""
        self.disk_io_read_bytes_total.labels(node=node).inc(read_bytes)
        self.disk_io_write_bytes_total.labels(node=node).inc(write_bytes)
    
    def record_network_io(self, node: str, rx_bytes: int, tx_bytes: int):
        """Record network I/O"""
        self.network_receive_bytes_total.labels(node=node).inc(rx_bytes)
        self.network_transmit_bytes_total.labels(node=node).inc(tx_bytes)
    
    def record_kv_optimization(self, opt_type: str, memory_saved: int):
        """Record KV cache optimization"""
        self.kv_optimization_events_total.labels(
            optimization_type=opt_type
        ).inc()
        
        if memory_saved > 0:
            self.kv_memory_saved_bytes.inc(memory_saved)
    
    def update_resource_costs(self, resource_type: str, cost_per_hour: float, 
                             idle_cost_per_hour: float):
        """Update resource cost metrics"""
        self.resource_cost_per_hour.labels(resource_type=resource_type).set(cost_per_hour)
        self.idle_resource_cost_per_hour.labels(resource_type=resource_type).set(idle_cost_per_hour)
