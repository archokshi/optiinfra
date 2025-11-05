"""
Resource Metrics Models

Pydantic models for resource metrics endpoints.
"""

from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class GPUMetrics(BaseModel):
    """GPU metrics model."""
    
    gpu_id: int = Field(..., description="GPU identifier")
    gpu_name: str = Field(..., description="GPU name")
    utilization_percent: float = Field(..., ge=0, le=100, description="GPU utilization %")
    memory_used_mb: float = Field(..., ge=0, description="Memory used (MB)")
    memory_total_mb: float = Field(..., ge=0, description="Total memory (MB)")
    memory_utilization_percent: float = Field(..., ge=0, le=100, description="Memory utilization %")
    temperature_celsius: float = Field(..., description="GPU temperature (°C)")
    power_draw_watts: float = Field(..., description="Power draw (W)")


class CPUMetrics(BaseModel):
    """CPU metrics model."""
    
    cpu_count: int = Field(..., description="Number of CPUs")
    cpu_utilization_percent: float = Field(..., ge=0, le=100, description="CPU utilization %")
    cpu_frequency_mhz: float = Field(..., description="CPU frequency (MHz)")
    load_average_1m: float = Field(..., description="1-minute load average")
    load_average_5m: float = Field(..., description="5-minute load average")
    load_average_15m: float = Field(..., description="15-minute load average")


class MemoryMetrics(BaseModel):
    """Memory metrics model."""
    
    total_mb: float = Field(..., ge=0, description="Total memory (MB)")
    available_mb: float = Field(..., ge=0, description="Available memory (MB)")
    used_mb: float = Field(..., ge=0, description="Used memory (MB)")
    utilization_percent: float = Field(..., ge=0, le=100, description="Memory utilization %")
    swap_total_mb: float = Field(..., ge=0, description="Total swap (MB)")
    swap_used_mb: float = Field(..., ge=0, description="Used swap (MB)")


class ResourceMetrics(BaseModel):
    """Combined resource metrics."""
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    instance_id: str = Field(..., description="Instance identifier")
    gpus: List[GPUMetrics] = Field(default_factory=list, description="GPU metrics")
    cpu: CPUMetrics = Field(..., description="CPU metrics")
    memory: MemoryMetrics = Field(..., description="Memory metrics")
