"""
System Metrics Models

Pydantic models for CPU, memory, disk, and network metrics.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class CPUTimes(BaseModel):
    """CPU time statistics."""
    
    user: float = Field(..., description="Time spent in user mode")
    system: float = Field(..., description="Time spent in system mode")
    idle: float = Field(..., description="Time spent idle")
    iowait: Optional[float] = Field(None, description="Time spent waiting for I/O")


class CPUFrequency(BaseModel):
    """CPU frequency information."""
    
    current_mhz: float = Field(..., description="Current frequency (MHz)")
    min_mhz: float = Field(..., description="Minimum frequency (MHz)")
    max_mhz: float = Field(..., description="Maximum frequency (MHz)")


class CPUMetrics(BaseModel):
    """CPU metrics."""
    
    # Overall utilization
    utilization_percent: float = Field(..., ge=0, le=100, description="Overall CPU utilization %")
    
    # Per-core utilization
    per_core_utilization: List[float] = Field(default_factory=list, description="Per-core utilization %")
    
    # CPU counts
    logical_cores: int = Field(..., description="Number of logical cores")
    physical_cores: int = Field(..., description="Number of physical cores")
    
    # Frequency
    frequency: Optional[CPUFrequency] = Field(None, description="CPU frequency")
    
    # Load average (Unix only)
    load_average_1m: Optional[float] = Field(None, description="1-minute load average")
    load_average_5m: Optional[float] = Field(None, description="5-minute load average")
    load_average_15m: Optional[float] = Field(None, description="15-minute load average")
    
    # CPU times
    cpu_times: CPUTimes = Field(..., description="CPU time statistics")
    
    # Context switches
    context_switches: Optional[int] = Field(None, description="Number of context switches")


class MemoryMetrics(BaseModel):
    """Memory metrics."""
    
    # Virtual memory
    total_mb: float = Field(..., ge=0, description="Total memory (MB)")
    available_mb: float = Field(..., ge=0, description="Available memory (MB)")
    used_mb: float = Field(..., ge=0, description="Used memory (MB)")
    free_mb: float = Field(..., ge=0, description="Free memory (MB)")
    utilization_percent: float = Field(..., ge=0, le=100, description="Memory utilization %")
    
    # Swap memory
    swap_total_mb: float = Field(..., ge=0, description="Total swap (MB)")
    swap_used_mb: float = Field(..., ge=0, description="Used swap (MB)")
    swap_free_mb: float = Field(..., ge=0, description="Free swap (MB)")
    swap_utilization_percent: float = Field(..., ge=0, le=100, description="Swap utilization %")
    
    # Additional memory info
    cached_mb: Optional[float] = Field(None, ge=0, description="Cached memory (MB)")
    buffers_mb: Optional[float] = Field(None, ge=0, description="Buffer memory (MB)")


class DiskPartition(BaseModel):
    """Disk partition information."""
    
    device: str = Field(..., description="Device name")
    mountpoint: str = Field(..., description="Mount point")
    fstype: str = Field(..., description="Filesystem type")
    total_mb: float = Field(..., ge=0, description="Total size (MB)")
    used_mb: float = Field(..., ge=0, description="Used space (MB)")
    free_mb: float = Field(..., ge=0, description="Free space (MB)")
    utilization_percent: float = Field(..., ge=0, le=100, description="Disk utilization %")


class DiskIOCounters(BaseModel):
    """Disk I/O counters."""
    
    read_bytes: int = Field(..., ge=0, description="Bytes read")
    write_bytes: int = Field(..., ge=0, description="Bytes written")
    read_count: int = Field(..., ge=0, description="Number of reads")
    write_count: int = Field(..., ge=0, description="Number of writes")


class DiskMetrics(BaseModel):
    """Disk metrics."""
    
    partitions: List[DiskPartition] = Field(default_factory=list, description="Disk partitions")
    io_counters: Optional[DiskIOCounters] = Field(None, description="Disk I/O counters")


class NetworkIOCounters(BaseModel):
    """Network I/O counters."""
    
    bytes_sent: int = Field(..., ge=0, description="Bytes sent")
    bytes_recv: int = Field(..., ge=0, description="Bytes received")
    packets_sent: int = Field(..., ge=0, description="Packets sent")
    packets_recv: int = Field(..., ge=0, description="Packets received")
    errin: int = Field(default=0, ge=0, description="Incoming errors")
    errout: int = Field(default=0, ge=0, description="Outgoing errors")
    dropin: int = Field(default=0, ge=0, description="Incoming packets dropped")
    dropout: int = Field(default=0, ge=0, description="Outgoing packets dropped")


class NetworkMetrics(BaseModel):
    """Network metrics."""
    
    io_counters: NetworkIOCounters = Field(..., description="Network I/O counters")
    connections_count: Optional[int] = Field(None, description="Number of active connections")


class SystemMetricsCollection(BaseModel):
    """Collection of all system metrics."""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    instance_id: str = Field(..., description="Instance identifier")
    
    # Core metrics
    cpu: CPUMetrics = Field(..., description="CPU metrics")
    memory: MemoryMetrics = Field(..., description="Memory metrics")
    
    # Optional metrics
    disk: Optional[DiskMetrics] = Field(None, description="Disk metrics")
    network: Optional[NetworkMetrics] = Field(None, description="Network metrics")
    
    # System info
    boot_time: datetime = Field(..., description="System boot time")
    uptime_seconds: float = Field(..., ge=0, description="System uptime in seconds")
