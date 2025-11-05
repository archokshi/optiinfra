# PHASE3-3.2 PART1: GPU Collector - Code Implementation Plan

**Phase**: PHASE3-3.2  
**Agent**: Resource Agent  
**Objective**: Implement nvidia-smi integration for GPU metrics collection  
**Estimated Time**: 25+20m (45 minutes total)  
**Priority**: HIGH  
**Dependencies**: PHASE3-3.1

---

## Overview

This phase implements the GPU metrics collector using nvidia-smi Python bindings (pynvml). The collector gathers real-time GPU utilization, memory usage, temperature, and power consumption metrics from NVIDIA GPUs.

---

## NVIDIA GPU Metrics Overview

### What is nvidia-smi?

NVIDIA System Management Interface (nvidia-smi) is a command-line utility for monitoring and managing NVIDIA GPU devices. The Python bindings (pynvml) provide programmatic access to GPU metrics.

### Key GPU Metrics

#### Utilization Metrics
- **GPU Utilization** - Percentage of time GPU was actively processing (0-100%)
- **Memory Utilization** - Percentage of memory bandwidth used (0-100%)
- **Encoder Utilization** - Video encoder usage
- **Decoder Utilization** - Video decoder usage

#### Memory Metrics
- **Memory Used** - Currently used GPU memory (bytes)
- **Memory Total** - Total available GPU memory (bytes)
- **Memory Free** - Available GPU memory (bytes)

#### Temperature & Power
- **Temperature** - GPU temperature (Celsius)
- **Power Draw** - Current power consumption (Watts)
- **Power Limit** - Maximum power limit (Watts)

#### Process Information
- **Running Processes** - List of processes using the GPU
- **Process Memory** - Memory used by each process

#### Clock Speeds
- **Graphics Clock** - Current graphics clock speed (MHz)
- **SM Clock** - Streaming multiprocessor clock speed (MHz)
- **Memory Clock** - Memory clock speed (MHz)

---

## Implementation Plan

### Step 1: GPU Metrics Models (5 minutes)

#### 1.1 Create src/models/gpu_metrics.py

```python
"""
GPU Metrics Models

Pydantic models for NVIDIA GPU metrics.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class GPUProcessInfo(BaseModel):
    """Information about a process using the GPU."""
    
    pid: int = Field(..., description="Process ID")
    process_name: str = Field(..., description="Process name")
    used_memory_mb: float = Field(..., ge=0, description="Memory used by process (MB)")


class GPUClockSpeeds(BaseModel):
    """GPU clock speeds."""
    
    graphics_clock_mhz: float = Field(..., description="Graphics clock (MHz)")
    sm_clock_mhz: float = Field(..., description="SM clock (MHz)")
    memory_clock_mhz: float = Field(..., description="Memory clock (MHz)")


class GPUUtilization(BaseModel):
    """GPU utilization metrics."""
    
    gpu_percent: float = Field(..., ge=0, le=100, description="GPU utilization %")
    memory_percent: float = Field(..., ge=0, le=100, description="Memory utilization %")
    encoder_percent: Optional[float] = Field(None, ge=0, le=100, description="Encoder utilization %")
    decoder_percent: Optional[float] = Field(None, ge=0, le=100, description="Decoder utilization %")


class GPUMemory(BaseModel):
    """GPU memory metrics."""
    
    total_mb: float = Field(..., ge=0, description="Total memory (MB)")
    used_mb: float = Field(..., ge=0, description="Used memory (MB)")
    free_mb: float = Field(..., ge=0, description="Free memory (MB)")
    utilization_percent: float = Field(..., ge=0, le=100, description="Memory utilization %")


class GPUPower(BaseModel):
    """GPU power metrics."""
    
    power_draw_watts: float = Field(..., ge=0, description="Current power draw (W)")
    power_limit_watts: float = Field(..., ge=0, description="Power limit (W)")
    power_usage_percent: float = Field(..., ge=0, le=100, description="Power usage %")


class GPUTemperature(BaseModel):
    """GPU temperature metrics."""
    
    current_celsius: float = Field(..., description="Current temperature (°C)")
    slowdown_threshold_celsius: Optional[float] = Field(None, description="Slowdown threshold (°C)")
    shutdown_threshold_celsius: Optional[float] = Field(None, description="Shutdown threshold (°C)")


class SingleGPUMetrics(BaseModel):
    """Metrics for a single GPU."""
    
    gpu_id: int = Field(..., ge=0, description="GPU index")
    gpu_name: str = Field(..., description="GPU model name")
    gpu_uuid: str = Field(..., description="GPU UUID")
    driver_version: str = Field(..., description="Driver version")
    
    # Utilization
    utilization: GPUUtilization = Field(..., description="Utilization metrics")
    
    # Memory
    memory: GPUMemory = Field(..., description="Memory metrics")
    
    # Temperature
    temperature: GPUTemperature = Field(..., description="Temperature metrics")
    
    # Power
    power: GPUPower = Field(..., description="Power metrics")
    
    # Clock speeds
    clocks: GPUClockSpeeds = Field(..., description="Clock speeds")
    
    # Processes
    processes: List[GPUProcessInfo] = Field(default_factory=list, description="Running processes")
    
    # Performance state (P0-P12, P0 = max performance)
    performance_state: str = Field(..., description="Performance state")
    
    # Fan speed
    fan_speed_percent: Optional[float] = Field(None, ge=0, le=100, description="Fan speed %")


class GPUMetricsCollection(BaseModel):
    """Collection of metrics from all GPUs."""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    instance_id: str = Field(..., description="Instance identifier")
    gpu_count: int = Field(..., ge=0, description="Number of GPUs")
    gpus: List[SingleGPUMetrics] = Field(default_factory=list, description="Per-GPU metrics")
    
    # Aggregate metrics
    total_memory_used_mb: float = Field(default=0.0, description="Total memory used across all GPUs")
    total_memory_total_mb: float = Field(default=0.0, description="Total memory across all GPUs")
    average_gpu_utilization: float = Field(default=0.0, ge=0, le=100, description="Average GPU utilization")
    average_memory_utilization: float = Field(default=0.0, ge=0, le=100, description="Average memory utilization")
    average_temperature: float = Field(default=0.0, description="Average temperature")
    total_power_draw_watts: float = Field(default=0.0, description="Total power draw")
```

---

### Step 2: GPU Collector Implementation (10 minutes)

#### 2.1 Create src/collectors/__init__.py

```python
"""Metrics collectors for Resource Agent."""
```

#### 2.2 Create src/collectors/gpu_collector.py

```python
"""
GPU Metrics Collector

Collects GPU metrics using nvidia-smi (pynvml).
"""

import logging
from typing import Optional, List
from datetime import datetime

try:
    import pynvml
    PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False
    logging.warning("pynvml not available - GPU metrics collection disabled")

from src.models.gpu_metrics import (
    GPUMetricsCollection,
    SingleGPUMetrics,
    GPUUtilization,
    GPUMemory,
    GPUPower,
    GPUTemperature,
    GPUClockSpeeds,
    GPUProcessInfo
)

logger = logging.getLogger("resource_agent.gpu_collector")


class GPUCollector:
    """Collector for NVIDIA GPU metrics using pynvml."""
    
    def __init__(self):
        """Initialize GPU collector."""
        self.initialized = False
        self.gpu_count = 0
        
        if PYNVML_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self.gpu_count = pynvml.nvmlDeviceGetCount()
                self.initialized = True
                logger.info(f"GPU collector initialized with {self.gpu_count} GPUs")
            except Exception as e:
                logger.error(f"Failed to initialize pynvml: {e}")
                self.initialized = False
        else:
            logger.warning("pynvml not available - GPU metrics collection disabled")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()
    
    def shutdown(self):
        """Shutdown pynvml."""
        if self.initialized and PYNVML_AVAILABLE:
            try:
                pynvml.nvmlShutdown()
                logger.info("GPU collector shutdown")
            except Exception as e:
                logger.error(f"Error shutting down pynvml: {e}")
    
    def is_available(self) -> bool:
        """Check if GPU metrics collection is available."""
        return self.initialized and PYNVML_AVAILABLE
    
    def collect_gpu_metrics(self, gpu_index: int) -> Optional[SingleGPUMetrics]:
        """
        Collect metrics for a single GPU.
        
        Args:
            gpu_index: GPU index (0-based)
            
        Returns:
            SingleGPUMetrics or None if collection fails
        """
        if not self.is_available():
            return None
        
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_index)
            
            # Basic info
            name = pynvml.nvmlDeviceGetName(handle)
            uuid = pynvml.nvmlDeviceGetUUID(handle)
            driver_version = pynvml.nvmlSystemGetDriverVersion()
            
            # Utilization
            utilization_rates = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpu_util = utilization_rates.gpu
            memory_util = utilization_rates.memory
            
            # Try to get encoder/decoder utilization (may not be available on all GPUs)
            try:
                encoder_util = pynvml.nvmlDeviceGetEncoderUtilization(handle)[0]
                decoder_util = pynvml.nvmlDeviceGetDecoderUtilization(handle)[0]
            except:
                encoder_util = None
                decoder_util = None
            
            utilization = GPUUtilization(
                gpu_percent=float(gpu_util),
                memory_percent=float(memory_util),
                encoder_percent=float(encoder_util) if encoder_util is not None else None,
                decoder_percent=float(decoder_util) if decoder_util is not None else None
            )
            
            # Memory
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            memory = GPUMemory(
                total_mb=memory_info.total / (1024 * 1024),
                used_mb=memory_info.used / (1024 * 1024),
                free_mb=memory_info.free / (1024 * 1024),
                utilization_percent=(memory_info.used / memory_info.total) * 100
            )
            
            # Temperature
            temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            try:
                slowdown_temp = pynvml.nvmlDeviceGetTemperatureThreshold(
                    handle, pynvml.NVML_TEMPERATURE_THRESHOLD_SLOWDOWN
                )
                shutdown_temp = pynvml.nvmlDeviceGetTemperatureThreshold(
                    handle, pynvml.NVML_TEMPERATURE_THRESHOLD_SHUTDOWN
                )
            except:
                slowdown_temp = None
                shutdown_temp = None
            
            temperature = GPUTemperature(
                current_celsius=float(temp),
                slowdown_threshold_celsius=float(slowdown_temp) if slowdown_temp else None,
                shutdown_threshold_celsius=float(shutdown_temp) if shutdown_temp else None
            )
            
            # Power
            power_draw = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # mW to W
            power_limit = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / 1000.0  # mW to W
            power = GPUPower(
                power_draw_watts=power_draw,
                power_limit_watts=power_limit,
                power_usage_percent=(power_draw / power_limit) * 100 if power_limit > 0 else 0.0
            )
            
            # Clock speeds
            graphics_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
            sm_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_SM)
            memory_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
            clocks = GPUClockSpeeds(
                graphics_clock_mhz=float(graphics_clock),
                sm_clock_mhz=float(sm_clock),
                memory_clock_mhz=float(memory_clock)
            )
            
            # Processes
            processes = []
            try:
                compute_processes = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
                for proc in compute_processes:
                    try:
                        proc_name = pynvml.nvmlSystemGetProcessName(proc.pid)
                        processes.append(GPUProcessInfo(
                            pid=proc.pid,
                            process_name=proc_name,
                            used_memory_mb=proc.usedGpuMemory / (1024 * 1024) if proc.usedGpuMemory else 0.0
                        ))
                    except:
                        pass
            except:
                pass
            
            # Performance state
            try:
                perf_state = pynvml.nvmlDeviceGetPerformanceState(handle)
                perf_state_str = f"P{perf_state}"
            except:
                perf_state_str = "Unknown"
            
            # Fan speed
            try:
                fan_speed = pynvml.nvmlDeviceGetFanSpeed(handle)
            except:
                fan_speed = None
            
            return SingleGPUMetrics(
                gpu_id=gpu_index,
                gpu_name=name,
                gpu_uuid=uuid,
                driver_version=driver_version,
                utilization=utilization,
                memory=memory,
                temperature=temperature,
                power=power,
                clocks=clocks,
                processes=processes,
                performance_state=perf_state_str,
                fan_speed_percent=float(fan_speed) if fan_speed is not None else None
            )
            
        except Exception as e:
            logger.error(f"Failed to collect metrics for GPU {gpu_index}: {e}")
            return None
    
    def collect(self, instance_id: str) -> Optional[GPUMetricsCollection]:
        """
        Collect metrics from all GPUs.
        
        Args:
            instance_id: Instance identifier
            
        Returns:
            GPUMetricsCollection or None if collection fails
        """
        if not self.is_available():
            logger.warning("GPU metrics collection not available")
            return None
        
        try:
            gpus = []
            total_memory_used = 0.0
            total_memory_total = 0.0
            total_gpu_util = 0.0
            total_memory_util = 0.0
            total_temp = 0.0
            total_power = 0.0
            
            for i in range(self.gpu_count):
                gpu_metrics = self.collect_gpu_metrics(i)
                if gpu_metrics:
                    gpus.append(gpu_metrics)
                    total_memory_used += gpu_metrics.memory.used_mb
                    total_memory_total += gpu_metrics.memory.total_mb
                    total_gpu_util += gpu_metrics.utilization.gpu_percent
                    total_memory_util += gpu_metrics.utilization.memory_percent
                    total_temp += gpu_metrics.temperature.current_celsius
                    total_power += gpu_metrics.power.power_draw_watts
            
            if not gpus:
                return None
            
            # Calculate averages
            gpu_count = len(gpus)
            avg_gpu_util = total_gpu_util / gpu_count if gpu_count > 0 else 0.0
            avg_memory_util = total_memory_util / gpu_count if gpu_count > 0 else 0.0
            avg_temp = total_temp / gpu_count if gpu_count > 0 else 0.0
            
            return GPUMetricsCollection(
                instance_id=instance_id,
                gpu_count=gpu_count,
                gpus=gpus,
                total_memory_used_mb=total_memory_used,
                total_memory_total_mb=total_memory_total,
                average_gpu_utilization=avg_gpu_util,
                average_memory_utilization=avg_memory_util,
                average_temperature=avg_temp,
                total_power_draw_watts=total_power
            )
            
        except Exception as e:
            logger.error(f"Failed to collect GPU metrics: {e}")
            return None
```

---

### Step 3: API Endpoint (5 minutes)

#### 3.1 Create src/api/gpu.py

```python
"""
GPU Metrics API

Endpoints for GPU metrics collection and retrieval.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional

from src.models.gpu_metrics import GPUMetricsCollection
from src.collectors.gpu_collector import GPUCollector
from src.config import settings

router = APIRouter(prefix="/gpu", tags=["gpu"])


@router.get(
    "/metrics",
    response_model=GPUMetricsCollection,
    status_code=status.HTTP_200_OK,
    summary="Get current GPU metrics"
)
async def get_gpu_metrics() -> GPUMetricsCollection:
    """
    Collect and return current GPU metrics from all GPUs.
    
    Returns:
        GPUMetricsCollection: Current GPU metrics
        
    Raises:
        HTTPException: If GPU metrics collection is not available
    """
    with GPUCollector() as collector:
        if not collector.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GPU metrics collection not available (no NVIDIA GPUs or pynvml not installed)"
            )
        
        metrics = collector.collect(instance_id=settings.agent_id)
        
        if metrics is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to collect GPU metrics"
            )
        
        return metrics


@router.get(
    "/metrics/{gpu_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get metrics for specific GPU"
)
async def get_single_gpu_metrics(gpu_id: int) -> dict:
    """
    Get metrics for a specific GPU.
    
    Args:
        gpu_id: GPU index (0-based)
        
    Returns:
        dict: GPU metrics
        
    Raises:
        HTTPException: If GPU not found or metrics unavailable
    """
    with GPUCollector() as collector:
        if not collector.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GPU metrics collection not available"
            )
        
        if gpu_id >= collector.gpu_count:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"GPU {gpu_id} not found (available: 0-{collector.gpu_count-1})"
            )
        
        gpu_metrics = collector.collect_gpu_metrics(gpu_id)
        
        if gpu_metrics is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to collect metrics for GPU {gpu_id}"
            )
        
        return gpu_metrics.model_dump()


@router.get(
    "/info",
    status_code=status.HTTP_200_OK,
    summary="Get GPU information"
)
async def get_gpu_info() -> dict:
    """
    Get basic GPU information.
    
    Returns:
        dict: GPU count and availability
    """
    with GPUCollector() as collector:
        return {
            "available": collector.is_available(),
            "gpu_count": collector.gpu_count if collector.is_available() else 0,
            "pynvml_installed": collector.initialized
        }
```

---

### Step 4: Update Main Application (2 minutes)

#### 4.1 Update src/main.py

Add GPU router to main application:

```python
# Add import
from src.api import health, gpu

# Include router
app.include_router(gpu.router)
```

---

### Step 5: Testing (5 minutes)

#### 5.1 Create tests/test_gpu_collector.py

```python
"""
GPU Collector Tests

Tests for GPU metrics collection.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.collectors.gpu_collector import GPUCollector, PYNVML_AVAILABLE


@pytest.fixture
def mock_pynvml():
    """Mock pynvml module."""
    with patch('src.collectors.gpu_collector.pynvml') as mock:
        # Mock device handle
        mock_handle = Mock()
        mock.nvmlDeviceGetHandleByIndex.return_value = mock_handle
        
        # Mock basic info
        mock.nvmlDeviceGetName.return_value = "NVIDIA A100"
        mock.nvmlDeviceGetUUID.return_value = "GPU-12345"
        mock.nvmlSystemGetDriverVersion.return_value = "525.60.13"
        
        # Mock utilization
        util_mock = Mock()
        util_mock.gpu = 75
        util_mock.memory = 60
        mock.nvmlDeviceGetUtilizationRates.return_value = util_mock
        
        # Mock memory
        memory_mock = Mock()
        memory_mock.total = 80 * 1024 * 1024 * 1024  # 80GB
        memory_mock.used = 40 * 1024 * 1024 * 1024   # 40GB
        memory_mock.free = 40 * 1024 * 1024 * 1024   # 40GB
        mock.nvmlDeviceGetMemoryInfo.return_value = memory_mock
        
        # Mock temperature
        mock.nvmlDeviceGetTemperature.return_value = 65
        
        # Mock power
        mock.nvmlDeviceGetPowerUsage.return_value = 300000  # 300W in mW
        mock.nvmlDeviceGetPowerManagementLimit.return_value = 400000  # 400W in mW
        
        # Mock clocks
        mock.nvmlDeviceGetClockInfo.side_effect = [1410, 1410, 1215]  # Graphics, SM, Memory
        
        # Mock processes
        mock.nvmlDeviceGetComputeRunningProcesses.return_value = []
        
        # Mock performance state
        mock.nvmlDeviceGetPerformanceState.return_value = 0  # P0
        
        # Mock fan speed
        mock.nvmlDeviceGetFanSpeed.return_value = 50
        
        # Mock device count
        mock.nvmlDeviceGetCount.return_value = 1
        
        yield mock


@pytest.mark.skipif(not PYNVML_AVAILABLE, reason="pynvml not available")
def test_gpu_collector_initialization(mock_pynvml):
    """Test GPU collector initialization."""
    with GPUCollector() as collector:
        assert collector.is_available()
        assert collector.gpu_count == 1


@pytest.mark.skipif(not PYNVML_AVAILABLE, reason="pynvml not available")
def test_collect_single_gpu_metrics(mock_pynvml):
    """Test collecting metrics from a single GPU."""
    with GPUCollector() as collector:
        metrics = collector.collect_gpu_metrics(0)
        
        assert metrics is not None
        assert metrics.gpu_id == 0
        assert metrics.gpu_name == "NVIDIA A100"
        assert metrics.utilization.gpu_percent == 75.0
        assert metrics.memory.total_mb > 0


@pytest.mark.skipif(not PYNVML_AVAILABLE, reason="pynvml not available")
def test_collect_all_gpu_metrics(mock_pynvml):
    """Test collecting metrics from all GPUs."""
    with GPUCollector() as collector:
        metrics = collector.collect(instance_id="test-instance")
        
        assert metrics is not None
        assert metrics.gpu_count == 1
        assert len(metrics.gpus) == 1
        assert metrics.average_gpu_utilization == 75.0


def test_gpu_collector_without_pynvml():
    """Test GPU collector when pynvml is not available."""
    with patch('src.collectors.gpu_collector.PYNVML_AVAILABLE', False):
        with GPUCollector() as collector:
            assert not collector.is_available()
            assert collector.gpu_count == 0
            
            metrics = collector.collect("test")
            assert metrics is None
```

#### 5.2 Create tests/test_gpu_api.py

```python
"""
GPU API Tests

Tests for GPU metrics API endpoints.
"""

import pytest
from fastapi import status
from unittest.mock import patch, Mock


def test_get_gpu_info(client):
    """Test GPU info endpoint."""
    response = client.get("/gpu/info")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "available" in data
    assert "gpu_count" in data


@pytest.mark.skipif(True, reason="Requires GPU hardware")
def test_get_gpu_metrics(client):
    """Test GPU metrics endpoint."""
    response = client.get("/gpu/metrics")
    
    # Will return 503 if no GPU available
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]


@pytest.mark.skipif(True, reason="Requires GPU hardware")
def test_get_single_gpu_metrics(client):
    """Test single GPU metrics endpoint."""
    response = client.get("/gpu/metrics/0")
    
    # Will return 503 if no GPU available, 404 if GPU not found
    assert response.status_code in [
        status.HTTP_200_OK,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_503_SERVICE_UNAVAILABLE
    ]
```

---

## Expected Outcomes

After completing this phase:

1. ✅ **GPU Metrics Collection**
   - Real-time GPU utilization monitoring
   - Memory usage tracking
   - Temperature and power monitoring
   - Process-level GPU usage

2. ✅ **API Endpoints**
   - `GET /gpu/metrics` - All GPU metrics
   - `GET /gpu/metrics/{gpu_id}` - Single GPU metrics
   - `GET /gpu/info` - GPU availability info

3. ✅ **Test Coverage**
   - GPU collector tests
   - API endpoint tests
   - Mock tests for systems without GPU

4. ✅ **Graceful Degradation**
   - Works without NVIDIA GPUs
   - Clear error messages
   - Fallback behavior

---

## Integration Points

### With Other Components

1. **Analysis Engine** (PHASE3-3.4)
   - GPU metrics feed into utilization analysis
   - Identify underutilized GPUs
   - Detect memory bottlenecks

2. **Scaling Recommendations** (PHASE3-3.4)
   - Use GPU utilization for scaling decisions
   - Recommend consolidation for low utilization
   - Suggest scale-up for high utilization

3. **KVOptkit Integration** (PHASE3-3.5)
   - GPU memory metrics for KV cache optimization
   - Memory pressure detection

---

## Success Criteria

- [ ] GPU collector initializes successfully
- [ ] Metrics collected from all available GPUs
- [ ] API endpoints return valid data
- [ ] Tests pass (with and without GPU)
- [ ] Graceful handling of missing GPUs
- [ ] Documentation complete

---

## Next Steps

After GPU collector is complete:

- **PHASE3-3.3**: CPU/Memory Collector (psutil integration)
- **PHASE3-3.4**: Analysis Engine (utilization analysis)
- **PHASE3-3.5**: KVOptkit Integration

---

**Ready to implement GPU metrics collection!** 🚀
