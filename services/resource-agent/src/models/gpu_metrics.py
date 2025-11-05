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
