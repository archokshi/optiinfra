"""
Pydantic models for metrics data
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class Provider(str, Enum):
    """Cloud provider enum"""
    # Big 3 - Dedicated Collectors
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    
    # Generic Collector - GPU Clouds
    VULTR = "vultr"
    RUNPOD = "runpod"
    LAMBDA_LABS = "lambda_labs"
    COREWEAVE = "coreweave"
    PAPERSPACE = "paperspace"
    
    # Generic Collector - General Compute
    DIGITALOCEAN = "digitalocean"
    LINODE = "linode"
    HETZNER = "hetzner"
    OVH = "ovh"
    
    # Generic Collector - Self-Hosted
    ON_PREMISES = "on_premises"
    KUBERNETES = "kubernetes"
    DOCKER = "docker"
    
    # Generic fallback
    GENERIC = "generic"


class CostType(str, Enum):
    """Cost type enum"""
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    OTHER = "other"


class CostMetric(BaseModel):
    """Cost metric model"""
    timestamp: datetime = Field(default_factory=datetime.now)
    customer_id: str
    provider: Provider
    instance_id: Optional[str] = None
    cost_type: CostType
    amount: float
    currency: str = "USD"
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True


class PerformanceMetric(BaseModel):
    """Performance metric model (Phase 6.4 Enhanced)"""
    timestamp: datetime = Field(default_factory=datetime.now)
    customer_id: str
    provider: Provider
    metric_type: str  # compute, memory, storage, network
    resource_id: str
    resource_name: str
    metric_name: str  # cpu_utilization, memory_used, disk_io, etc.
    metric_value: float
    unit: str
    metadata: Optional[Dict[str, Any]] = None
    workload_type: Optional[str] = None  # instance, container, function
    
    class Config:
        use_enum_values = True


class ResourceMetric(BaseModel):
    """Resource metric model (Phase 6.4 Enhanced)"""
    timestamp: datetime = Field(default_factory=datetime.now)
    customer_id: str
    provider: Provider
    metric_type: str  # inventory, configuration, compliance
    resource_id: str
    resource_name: str
    resource_type: str  # instance, block_storage, load_balancer, database, etc.
    status: str  # active, stopped, pending, etc.
    region: str
    utilization: float = 0.0
    capacity: float = 0.0
    unit: str = ""
    metadata: Optional[Dict[str, Any]] = None  # Additional context per metric
    
    class Config:
        use_enum_values = True


class ApplicationMetric(BaseModel):
    """Application metric model (Phase 6.5 Enhanced)"""
    timestamp: datetime = Field(default_factory=datetime.now)
    customer_id: str
    provider: Provider
    application_id: str
    application_name: str
    metric_type: str  # quality, hallucination, toxicity, latency
    score: float
    details: Optional[str] = None
    model_name: str
    prompt_text: Optional[str] = None
    response_text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True


class CollectionResult(BaseModel):
    """Result of a collection operation"""
    customer_id: str
    provider: Provider
    data_type: str  # cost, performance, resource, application
    success: bool
    records_collected: int
    started_at: datetime
    completed_at: datetime
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True
