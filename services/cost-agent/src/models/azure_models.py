"""
Azure Pydantic Models

Data models for Azure cost collection API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class AzureCredentials(BaseModel):
    """Azure authentication credentials"""
    subscription_id: str = Field(..., description="Azure subscription ID")
    tenant_id: Optional[str] = Field(None, description="Azure AD tenant ID")
    client_id: Optional[str] = Field(None, description="Service Principal client ID")
    client_secret: Optional[str] = Field(None, description="Service Principal client secret")


class AzureCollectionRequest(BaseModel):
    """Request to collect Azure cost data"""
    subscription_id: str = Field(..., description="Azure subscription ID")
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    lookback_days: int = Field(30, ge=1, le=90, description="Days to look back")
    include_utilization: bool = Field(True, description="Include utilization metrics")


class AzureTestConnectionRequest(BaseModel):
    """Request to test Azure connection"""
    subscription_id: str
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None


class AzureTestConnectionResponse(BaseModel):
    """Response from Azure connection test"""
    success: bool
    subscription_id: str
    tenant_id: Optional[str] = None
    message: str
    accessible_services: List[str] = []


class AzureCostQuery(BaseModel):
    """Query parameters for Azure costs"""
    subscription_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    service: Optional[str] = None
    resource_group: Optional[str] = None
    location: Optional[str] = None


class AzureCostBreakdown(BaseModel):
    """Cost breakdown by different dimensions"""
    by_service: Dict[str, float] = {}
    by_resource_group: Dict[str, float] = {}
    by_location: Dict[str, float] = {}
    daily: List[Dict] = []


class AzureVMMetrics(BaseModel):
    """Virtual Machine metrics"""
    vm_id: str
    vm_name: str
    vm_size: str
    location: str
    resource_group: str
    power_state: str
    monthly_cost: float
    disk_cost: float
    total_cost: float
    cpu_avg: Optional[float] = None
    memory_avg: Optional[float] = None
    network_in_gb: Optional[float] = None
    network_out_gb: Optional[float] = None
    is_idle: bool = False
    is_underutilized: bool = False
    spot_eligible: bool = False


class AzureSQLMetrics(BaseModel):
    """SQL Database metrics"""
    database_id: str
    database_name: str
    server_name: str
    tier: str
    sku: str
    monthly_cost: float
    connections_avg: Optional[float] = None
    dtu_avg: Optional[float] = None
    is_idle: bool = False


class AzureFunctionMetrics(BaseModel):
    """Function App metrics"""
    function_app_id: str
    function_app_name: str
    plan_type: str
    monthly_cost: float
    executions_total: Optional[int] = None
    memory_avg: Optional[float] = None
    is_over_provisioned: bool = False


class AzureStorageMetrics(BaseModel):
    """Storage Account metrics"""
    storage_account_id: str
    storage_account_name: str
    sku: str
    monthly_cost: float
    capacity_gb: Optional[float] = None
    transactions_total: Optional[int] = None
    has_lifecycle_policy: bool = False


class AzureOpportunity(BaseModel):
    """Optimization opportunity"""
    service: str
    type: str
    resource_id: str
    resource_name: str
    reason: str
    action: str
    estimated_savings: float
    priority: str = "medium"
    confidence: float = 0.85


class AzureServiceSummary(BaseModel):
    """Summary for a specific service"""
    total_resources: int
    total_monthly_cost: float
    idle_resources: int = 0
    underutilized_resources: int = 0
    opportunities_count: int = 0


class AzureCollectionResponse(BaseModel):
    """Response from Azure cost collection"""
    subscription_id: str
    time_period: Dict[str, str]
    total_cost: float
    cost_breakdown: AzureCostBreakdown
    services: Dict[str, AzureServiceSummary]
    optimization: Dict
    anomalies: List[Dict] = []
    forecast: Dict = {}
    analyzed_at: str


class AzureOpportunityQuery(BaseModel):
    """Query parameters for opportunities"""
    subscription_id: str
    min_savings: float = Field(0, ge=0, description="Minimum savings threshold")
    service: Optional[str] = None
    priority: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)


class AzureOpportunityResponse(BaseModel):
    """Response with optimization opportunities"""
    subscription_id: str
    total_opportunities: int
    total_potential_savings: float
    opportunities: List[AzureOpportunity]


class AzureForecastResponse(BaseModel):
    """Cost forecast response"""
    subscription_id: str
    forecast: Dict
    analyzed_at: str
