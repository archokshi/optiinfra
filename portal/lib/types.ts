/**
 * OptiInfra Portal - Type Definitions
 */

export type AgentType = "cost" | "performance" | "resource" | "application";
export type AgentStatus = "active" | "inactive" | "degraded" | "error";

export interface Agent {
  agent_id: string;
  agent_name: string;
  agent_type: AgentType;
  version: string;
  status: AgentStatus;
  last_heartbeat: string;
  capabilities: string[];
  host: string;
  port: number;
}

export interface Metric {
  name: string;
  value: number;
  unit: string;
  timestamp: string;
  trend?: "up" | "down" | "stable";
}

export interface DashboardTimeseriesPoint {
  timestamp: string;
  cost?: number;
  latency?: number;
  gpu?: number;
  quality?: number;
  [metric: string]: string | number | undefined;
}

export interface CostMetrics {
  total_cost: number;
  daily_cost: number;
  monthly_cost: number;
  cost_trend: number;
  savings_potential: number;
  currency: string;
}

export interface PerformanceMetrics {
  latency_p50: number;
  latency_p95: number;
  latency_p99: number;
  throughput: number;
  requests_per_second: number;
  error_rate: number;
}

export interface ResourceMetrics {
  gpu_utilization: number;
  cpu_utilization: number;
  memory_utilization: number;
  gpu_memory_used: number;
  gpu_memory_total: number;
}

export interface QualityMetrics {
  quality_score: number;
  relevance_score: number;
  coherence_score: number;
  hallucination_rate: number;
  toxicity_score: number;
}

export type RecommendationType = 
  | "spot_migration"
  | "reserved_instance"
  | "right_sizing"
  | "kv_cache_optimization"
  | "quantization"
  | "batch_optimization"
  | "gpu_scaling"
  | "memory_optimization";

export type RecommendationStatus = 
  | "pending"
  | "approved"
  | "rejected"
  | "executing"
  | "completed"
  | "failed";

export interface Recommendation {
  id: string;
  agent_type: AgentType;
  type: RecommendationType;
  title: string;
  description: string;
  estimated_savings?: number;
  estimated_improvement?: number;
  risk_level: "low" | "medium" | "high";
  status: RecommendationStatus;
  created_at: string;
  updated_at: string;
}

export interface Execution {
  id: string;
  recommendation_id: string;
  agent_type: AgentType;
  type: RecommendationType;
  status: "success" | "failed" | "in_progress";
  started_at: string;
  completed_at?: string;
  actual_savings?: number;
  actual_improvement?: number;
  error_message?: string;
}

export interface DashboardData {
  agents: Agent[];
  metrics: {
    cost: CostMetrics;
    performance: PerformanceMetrics;
    resource: ResourceMetrics;
    quality: QualityMetrics;
  };
  timeseries?: DashboardTimeseriesPoint[];
  recommendations: Recommendation[];
  recent_executions: Execution[];
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: string;
}

export interface HealthCheck {
  status: "healthy" | "degraded" | "unhealthy";
  timestamp: string;
  components: {
    [key: string]: "healthy" | "degraded" | "unhealthy";
  };
}

export type ProviderStatus = "connected" | "configured" | "not_configured" | "error";

export interface ProviderRequirement {
  field: string;
  label: string;
  required: boolean;
}

export interface CloudProvider {
  provider: string;
  display_name: string;
  type: "generic" | "dedicated";
  category: string;
  enabled: boolean;
  configured: boolean;
  status: ProviderStatus;
  last_status?: string | null;
  last_sync?: string | null;
  credential_count: number;
  requirements: ProviderRequirement[];
}

export interface CloudProvidersResponse {
  customer_id: string;
  generated_at: string;
  providers: CloudProvider[];
  summary: {
    total_supported: number;
    configured: number;
    connected: number;
    generic_supported: number;
    dedicated_supported: number;
  };
}
