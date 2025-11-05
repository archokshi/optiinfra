"""
System Metrics Collector

Collects CPU, memory, disk, and network metrics using psutil.
"""

import logging
import psutil
from typing import Optional
from datetime import datetime

from src.models.system_metrics import (
    SystemMetricsCollection,
    CPUMetrics,
    CPUTimes,
    CPUFrequency,
    MemoryMetrics,
    DiskMetrics,
    DiskPartition,
    DiskIOCounters,
    NetworkMetrics,
    NetworkIOCounters
)

logger = logging.getLogger("resource_agent.system_collector")


class SystemCollector:
    """Collector for system metrics using psutil."""
    
    def __init__(self):
        """Initialize system collector."""
        self.boot_time = datetime.fromtimestamp(psutil.boot_time())
        logger.info("System collector initialized")
    
    def collect_cpu_metrics(self) -> CPUMetrics:
        """
        Collect CPU metrics.
        
        Returns:
            CPUMetrics: CPU metrics
        """
        try:
            # Overall utilization
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Per-core utilization
            per_core = psutil.cpu_percent(interval=0.1, percpu=True)
            
            # CPU counts
            logical_cores = psutil.cpu_count(logical=True)
            physical_cores = psutil.cpu_count(logical=False)
            
            # CPU frequency
            freq = psutil.cpu_freq()
            frequency = None
            if freq:
                frequency = CPUFrequency(
                    current_mhz=freq.current,
                    min_mhz=freq.min,
                    max_mhz=freq.max
                )
            
            # Load average (Unix only)
            load_avg = None
            load_1m = load_5m = load_15m = None
            try:
                load_avg = psutil.getloadavg()
                load_1m, load_5m, load_15m = load_avg
            except (AttributeError, OSError):
                pass
            
            # CPU times
            cpu_times = psutil.cpu_times()
            times = CPUTimes(
                user=cpu_times.user,
                system=cpu_times.system,
                idle=cpu_times.idle,
                iowait=getattr(cpu_times, 'iowait', None)
            )
            
            # Context switches (if available)
            ctx_switches = None
            try:
                stats = psutil.cpu_stats()
                ctx_switches = stats.ctx_switches
            except AttributeError:
                pass
            
            return CPUMetrics(
                utilization_percent=cpu_percent,
                per_core_utilization=per_core,
                logical_cores=logical_cores,
                physical_cores=physical_cores,
                frequency=frequency,
                load_average_1m=load_1m,
                load_average_5m=load_5m,
                load_average_15m=load_15m,
                cpu_times=times,
                context_switches=ctx_switches
            )
            
        except Exception as e:
            logger.error(f"Failed to collect CPU metrics: {e}")
            raise
    
    def collect_memory_metrics(self) -> MemoryMetrics:
        """
        Collect memory metrics.
        
        Returns:
            MemoryMetrics: Memory metrics
        """
        try:
            # Virtual memory
            vmem = psutil.virtual_memory()
            
            # Swap memory
            swap = psutil.swap_memory()
            
            # Additional memory info (Linux)
            cached_mb = None
            buffers_mb = None
            if hasattr(vmem, 'cached'):
                cached_mb = vmem.cached / (1024 * 1024)
            if hasattr(vmem, 'buffers'):
                buffers_mb = vmem.buffers / (1024 * 1024)
            
            return MemoryMetrics(
                total_mb=vmem.total / (1024 * 1024),
                available_mb=vmem.available / (1024 * 1024),
                used_mb=vmem.used / (1024 * 1024),
                free_mb=vmem.free / (1024 * 1024),
                utilization_percent=vmem.percent,
                swap_total_mb=swap.total / (1024 * 1024),
                swap_used_mb=swap.used / (1024 * 1024),
                swap_free_mb=swap.free / (1024 * 1024),
                swap_utilization_percent=swap.percent,
                cached_mb=cached_mb,
                buffers_mb=buffers_mb
            )
            
        except Exception as e:
            logger.error(f"Failed to collect memory metrics: {e}")
            raise
    
    def collect_disk_metrics(self) -> Optional[DiskMetrics]:
        """
        Collect disk metrics.
        
        Returns:
            DiskMetrics or None if collection fails
        """
        try:
            partitions = []
            
            # Disk partitions
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partitions.append(DiskPartition(
                        device=partition.device,
                        mountpoint=partition.mountpoint,
                        fstype=partition.fstype,
                        total_mb=usage.total / (1024 * 1024),
                        used_mb=usage.used / (1024 * 1024),
                        free_mb=usage.free / (1024 * 1024),
                        utilization_percent=usage.percent
                    ))
                except (PermissionError, OSError):
                    continue
            
            # Disk I/O counters
            io_counters = None
            try:
                io = psutil.disk_io_counters()
                if io:
                    io_counters = DiskIOCounters(
                        read_bytes=io.read_bytes,
                        write_bytes=io.write_bytes,
                        read_count=io.read_count,
                        write_count=io.write_count
                    )
            except Exception:
                pass
            
            return DiskMetrics(
                partitions=partitions,
                io_counters=io_counters
            )
            
        except Exception as e:
            logger.error(f"Failed to collect disk metrics: {e}")
            return None
    
    def collect_network_metrics(self) -> Optional[NetworkMetrics]:
        """
        Collect network metrics.
        
        Returns:
            NetworkMetrics or None if collection fails
        """
        try:
            # Network I/O counters
            net_io = psutil.net_io_counters()
            
            io_counters = NetworkIOCounters(
                bytes_sent=net_io.bytes_sent,
                bytes_recv=net_io.bytes_recv,
                packets_sent=net_io.packets_sent,
                packets_recv=net_io.packets_recv,
                errin=net_io.errin,
                errout=net_io.errout,
                dropin=net_io.dropin,
                dropout=net_io.dropout
            )
            
            # Connection count
            connections_count = None
            try:
                connections = psutil.net_connections()
                connections_count = len(connections)
            except (PermissionError, psutil.AccessDenied):
                pass
            
            return NetworkMetrics(
                io_counters=io_counters,
                connections_count=connections_count
            )
            
        except Exception as e:
            logger.error(f"Failed to collect network metrics: {e}")
            return None
    
    def collect(self, instance_id: str) -> SystemMetricsCollection:
        """
        Collect all system metrics.
        
        Args:
            instance_id: Instance identifier
            
        Returns:
            SystemMetricsCollection: Complete system metrics
        """
        try:
            # Collect core metrics
            cpu_metrics = self.collect_cpu_metrics()
            memory_metrics = self.collect_memory_metrics()
            
            # Collect optional metrics
            disk_metrics = self.collect_disk_metrics()
            network_metrics = self.collect_network_metrics()
            
            # Calculate uptime
            uptime = (datetime.utcnow() - self.boot_time).total_seconds()
            
            return SystemMetricsCollection(
                instance_id=instance_id,
                cpu=cpu_metrics,
                memory=memory_metrics,
                disk=disk_metrics,
                network=network_metrics,
                boot_time=self.boot_time,
                uptime_seconds=uptime
            )
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            raise
