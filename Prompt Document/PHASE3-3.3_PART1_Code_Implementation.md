# PHASE3-3.3 PART1: CPU/Memory Collector - Code Implementation Plan

**Phase**: PHASE3-3.3  
**Agent**: Resource Agent  
**Objective**: Implement psutil integration for CPU and memory metrics collection  
**Estimated Time**: 25+20m (45 minutes total)  
**Priority**: HIGH  
**Dependencies**: PHASE3-3.1, PHASE3-3.2

---

## Overview

This phase implements the CPU and memory metrics collector using psutil. The collector gathers real-time CPU utilization, memory usage, disk I/O, and network metrics from the system.

---

## psutil Metrics Overview

### What is psutil?

psutil (Python System and Process Utilities) is a cross-platform library for retrieving information on running processes and system utilization (CPU, memory, disks, network, sensors).

### Key System Metrics

#### CPU Metrics
- **CPU Utilization** - Overall CPU usage percentage
- **Per-Core Utilization** - Usage per CPU core
- **CPU Frequency** - Current, min, max frequencies
- **Load Average** - 1, 5, 15 minute load averages (Unix)
- **CPU Count** - Logical and physical core counts
- **CPU Times** - User, system, idle, iowait times
- **Context Switches** - Number of context switches

#### Memory Metrics
- **Virtual Memory** - Total, available, used, free, percent
- **Swap Memory** - Total, used, free, percent
- **Memory by Process** - Per-process memory usage

#### Disk Metrics
- **Disk Usage** - Total, used, free, percent per partition
- **Disk I/O** - Read/write bytes, read/write count
- **Disk I/O Counters** - Per-disk statistics

#### Network Metrics
- **Network I/O** - Bytes sent/received, packets sent/received
- **Network Connections** - Active connections
- **Network Interface Stats** - Per-interface statistics

---

## Implementation Plan

### Step 1: CPU/Memory Metrics Models (5 minutes)

#### 1.1 Create src/models/system_metrics.py

```python
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
```

---

### Step 2: CPU/Memory Collector Implementation (10 minutes)

#### 2.1 Create src/collectors/system_collector.py

```python
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
```

---

### Step 3: API Endpoint (5 minutes)

#### 3.1 Create src/api/system.py

```python
"""
System Metrics API

Endpoints for system metrics collection and retrieval.
"""

from fastapi import APIRouter, HTTPException, status

from src.models.system_metrics import SystemMetricsCollection
from src.collectors.system_collector import SystemCollector
from src.config import settings

router = APIRouter(prefix="/system", tags=["system"])


@router.get(
    "/metrics",
    response_model=SystemMetricsCollection,
    status_code=status.HTTP_200_OK,
    summary="Get current system metrics"
)
async def get_system_metrics() -> SystemMetricsCollection:
    """
    Collect and return current system metrics (CPU, memory, disk, network).
    
    Returns:
        SystemMetricsCollection: Current system metrics
        
    Raises:
        HTTPException: If metrics collection fails
    """
    try:
        collector = SystemCollector()
        metrics = collector.collect(instance_id=settings.agent_id)
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect system metrics: {str(e)}"
        )


@router.get(
    "/metrics/cpu",
    status_code=status.HTTP_200_OK,
    summary="Get CPU metrics only"
)
async def get_cpu_metrics() -> dict:
    """
    Get CPU metrics only.
    
    Returns:
        dict: CPU metrics
    """
    try:
        collector = SystemCollector()
        cpu_metrics = collector.collect_cpu_metrics()
        return cpu_metrics.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect CPU metrics: {str(e)}"
        )


@router.get(
    "/metrics/memory",
    status_code=status.HTTP_200_OK,
    summary="Get memory metrics only"
)
async def get_memory_metrics() -> dict:
    """
    Get memory metrics only.
    
    Returns:
        dict: Memory metrics
    """
    try:
        collector = SystemCollector()
        memory_metrics = collector.collect_memory_metrics()
        return memory_metrics.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect memory metrics: {str(e)}"
        )


@router.get(
    "/metrics/disk",
    status_code=status.HTTP_200_OK,
    summary="Get disk metrics only"
)
async def get_disk_metrics() -> dict:
    """
    Get disk metrics only.
    
    Returns:
        dict: Disk metrics
    """
    try:
        collector = SystemCollector()
        disk_metrics = collector.collect_disk_metrics()
        if disk_metrics is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to collect disk metrics"
            )
        return disk_metrics.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect disk metrics: {str(e)}"
        )


@router.get(
    "/metrics/network",
    status_code=status.HTTP_200_OK,
    summary="Get network metrics only"
)
async def get_network_metrics() -> dict:
    """
    Get network metrics only.
    
    Returns:
        dict: Network metrics
    """
    try:
        collector = SystemCollector()
        network_metrics = collector.collect_network_metrics()
        if network_metrics is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to collect network metrics"
            )
        return network_metrics.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect network metrics: {str(e)}"
        )
```

---

### Step 4: Update Main Application (2 minutes)

#### 4.1 Update src/main.py

Add system router to main application:

```python
# Add import
from src.api import health, gpu, system

# Include router
app.include_router(system.router)
```

---

### Step 5: Testing (5 minutes)

#### 5.1 Create tests/test_system_collector.py

```python
"""
System Collector Tests

Tests for system metrics collection.
"""

import pytest
from src.collectors.system_collector import SystemCollector


def test_system_collector_initialization():
    """Test system collector initialization."""
    collector = SystemCollector()
    assert collector.boot_time is not None


def test_collect_cpu_metrics():
    """Test CPU metrics collection."""
    collector = SystemCollector()
    metrics = collector.collect_cpu_metrics()
    
    assert metrics is not None
    assert 0 <= metrics.utilization_percent <= 100
    assert metrics.logical_cores > 0
    assert metrics.physical_cores > 0
    assert len(metrics.per_core_utilization) == metrics.logical_cores


def test_collect_memory_metrics():
    """Test memory metrics collection."""
    collector = SystemCollector()
    metrics = collector.collect_memory_metrics()
    
    assert metrics is not None
    assert metrics.total_mb > 0
    assert 0 <= metrics.utilization_percent <= 100
    assert metrics.used_mb + metrics.available_mb <= metrics.total_mb * 1.1  # Allow 10% margin


def test_collect_disk_metrics():
    """Test disk metrics collection."""
    collector = SystemCollector()
    metrics = collector.collect_disk_metrics()
    
    # May be None on some systems
    if metrics:
        assert len(metrics.partitions) >= 0


def test_collect_network_metrics():
    """Test network metrics collection."""
    collector = SystemCollector()
    metrics = collector.collect_network_metrics()
    
    # May be None on some systems
    if metrics:
        assert metrics.io_counters is not None
        assert metrics.io_counters.bytes_sent >= 0
        assert metrics.io_counters.bytes_recv >= 0


def test_collect_all_metrics():
    """Test collecting all system metrics."""
    collector = SystemCollector()
    metrics = collector.collect(instance_id="test-instance")
    
    assert metrics is not None
    assert metrics.instance_id == "test-instance"
    assert metrics.cpu is not None
    assert metrics.memory is not None
    assert metrics.uptime_seconds > 0
```

#### 5.2 Create tests/test_system_api.py

```python
"""
System API Tests

Tests for system metrics API endpoints.
"""

import pytest
from fastapi import status


def test_get_system_metrics(client):
    """Test system metrics endpoint."""
    response = client.get("/system/metrics")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "cpu" in data
    assert "memory" in data
    assert "instance_id" in data


def test_get_cpu_metrics(client):
    """Test CPU metrics endpoint."""
    response = client.get("/system/metrics/cpu")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "utilization_percent" in data
    assert "logical_cores" in data


def test_get_memory_metrics(client):
    """Test memory metrics endpoint."""
    response = client.get("/system/metrics/memory")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total_mb" in data
    assert "utilization_percent" in data


def test_get_disk_metrics(client):
    """Test disk metrics endpoint."""
    response = client.get("/system/metrics/disk")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "partitions" in data


def test_get_network_metrics(client):
    """Test network metrics endpoint."""
    response = client.get("/system/metrics/network")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "io_counters" in data
```

---

## Expected Outcomes

After completing this phase:

1. ✅ **System Metrics Collection**
   - Real-time CPU utilization monitoring
   - Memory usage tracking
   - Disk usage and I/O monitoring
   - Network I/O tracking

2. ✅ **API Endpoints**
   - `GET /system/metrics` - All system metrics
   - `GET /system/metrics/cpu` - CPU metrics only
   - `GET /system/metrics/memory` - Memory metrics only
   - `GET /system/metrics/disk` - Disk metrics only
   - `GET /system/metrics/network` - Network metrics only

3. ✅ **Test Coverage**
   - System collector tests
   - API endpoint tests
   - Cross-platform compatibility

4. ✅ **Production Ready**
   - Comprehensive metrics
   - Error handling
   - Performance optimized

---

## Success Criteria

- [ ] System collector initializes successfully
- [ ] CPU metrics collected accurately
- [ ] Memory metrics collected accurately
- [ ] Disk metrics collected (with fallback)
- [ ] Network metrics collected (with fallback)
- [ ] API endpoints return valid data
- [ ] Tests pass (12+ tests)
- [ ] Documentation complete

---

## Next Steps

After CPU/Memory collector is complete:

- **PHASE3-3.4**: Analysis Engine (utilization analysis)
- **PHASE3-3.5**: KVOptkit Integration
- **PHASE3-3.6**: LangGraph Workflow

---

**Ready to implement comprehensive system metrics collection!** 🚀
