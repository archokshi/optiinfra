"use client";

import { useEffect, useMemo, useState } from "react";
import { AgentStatusCard } from "@/components/dashboard/agent-status-card";
import { MetricsChart } from "@/components/dashboard/metrics-chart";
import { RecommendationCard } from "@/components/dashboard/recommendation-card";
import type {
  Agent,
  AgentType,
  DashboardData,
  DashboardTimeseriesPoint,
  Recommendation,
} from "@/lib/types";
import { apiClient } from "@/lib/api";
import { formatCurrency, formatPercentage } from "@/lib/utils";

type AgentCardMetric = {
  value: string;
  label: string;
  trend?: "up" | "down" | "stable";
  trendValue?: string;
};

const fallbackTimeseries: { timestamp: string; [key: string]: string | number }[] = [
  { timestamp: "00:00", cost: 1200, latency: 95, gpu: 75, quality: 92 },
  { timestamp: "04:00", cost: 1150, latency: 88, gpu: 78, quality: 94 },
  { timestamp: "08:00", cost: 1300, latency: 92, gpu: 82, quality: 91 },
  { timestamp: "12:00", cost: 1250, latency: 85, gpu: 79, quality: 93 },
  { timestamp: "16:00", cost: 1100, latency: 82, gpu: 76, quality: 95 },
  { timestamp: "20:00", cost: 1050, latency: 80, gpu: 74, quality: 94 },
];

const fallbackAgents: Agent[] = [
  {
    agent_id: "cost-001",
    agent_name: "Cost Agent",
    agent_type: "cost",
    version: "1.0.0",
    status: "active",
    last_heartbeat: new Date(Date.now() - 30000).toISOString(),
    capabilities: ["cost_tracking", "optimization"],
    host: "localhost",
    port: 8001,
  },
  {
    agent_id: "perf-001",
    agent_name: "Performance Agent",
    agent_type: "performance",
    version: "1.0.0",
    status: "active",
    last_heartbeat: new Date(Date.now() - 45000).toISOString(),
    capabilities: ["performance_monitoring"],
    host: "localhost",
    port: 8002,
  },
  {
    agent_id: "resource-001",
    agent_name: "Resource Agent",
    agent_type: "resource",
    version: "1.0.0",
    status: "active",
    last_heartbeat: new Date(Date.now() - 20000).toISOString(),
    capabilities: ["resource_monitoring"],
    host: "localhost",
    port: 8003,
  },
  {
    agent_id: "app-001",
    agent_name: "Application Agent",
    agent_type: "application",
    version: "1.0.0",
    status: "active",
    last_heartbeat: new Date(Date.now() - 15000).toISOString(),
    capabilities: ["quality_monitoring"],
    host: "localhost",
    port: 8004,
  },
];

const fallbackRecommendations: Recommendation[] = [
  {
    id: "rec-001",
    agent_type: "cost",
    type: "spot_migration",
    title: "Migrate to Spot Instances",
    description: "Migrate 3 on-demand instances to spot instances for cost savings",
    estimated_savings: 450,
    risk_level: "low",
    status: "pending",
    created_at: new Date(Date.now() - 3600000).toISOString(),
    updated_at: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: "rec-002",
    agent_type: "performance",
    type: "kv_cache_optimization",
    title: "Optimize KV Cache",
    description: "Adjust KV cache size to improve latency",
    estimated_improvement: 15,
    risk_level: "medium",
    status: "pending",
    created_at: new Date(Date.now() - 7200000).toISOString(),
    updated_at: new Date(Date.now() - 7200000).toISOString(),
  },
];

const fallbackDashboard: DashboardData = {
  agents: fallbackAgents,
  metrics: {
    cost: {
      total_cost: 12450,
      daily_cost: 410,
      monthly_cost: 12450,
      cost_trend: -8.2,
      savings_potential: 920,
      currency: "USD",
    },
    performance: {
      latency_p50: 65,
      latency_p95: 85,
      latency_p99: 110,
      throughput: 1200,
      requests_per_second: 450,
      error_rate: 0.4,
    },
    resource: {
      gpu_utilization: 78,
      cpu_utilization: 55,
      memory_utilization: 63,
      gpu_memory_used: 22,
      gpu_memory_total: 32,
    },
    quality: {
      quality_score: 94,
      relevance_score: 92,
      coherence_score: 90,
      hallucination_rate: 1.2,
      toxicity_score: 0.4,
    },
  },
  timeseries: fallbackTimeseries,
  recommendations: fallbackRecommendations,
  recent_executions: [],
};

function formatLatency(value?: number | null): string | undefined {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return undefined;
  }
  return `${Math.round(value)} ms`;
}

function formatUtilization(value?: number | null): string | undefined {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return undefined;
  }
  return formatPercentage(value, 0);
}

function formatQualityScore(value?: number | null): string | undefined {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return undefined;
  }
  const normalized = value <= 1 ? value * 100 : value;
  return formatPercentage(normalized, normalized >= 99 ? 0 : 1);
}

function formatTrend(value?: number | null): string | undefined {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return undefined;
  }
  const fixed = Math.abs(value) >= 10 ? value.toFixed(0) : value.toFixed(1);
  const sign = value > 0 ? "+" : value < 0 ? "" : "";
  return `${sign}${fixed}%`;
}

function getTrendDirection(value?: number | null): "up" | "down" | "stable" | undefined {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return undefined;
  }
  if (Math.abs(value) < 0.1) {
    return "stable";
  }
  return value > 0 ? "up" : "down";
}

function sanitizeTimeseries(data?: DashboardTimeseriesPoint[]): DashboardTimeseriesPoint[] {
  if (!data || data.length === 0) {
    return [];
  }

  return data.map((point) => {
    const entry: DashboardTimeseriesPoint = {
      timestamp: point.timestamp,
    };

    Object.entries(point).forEach(([key, value]) => {
      if (key === "timestamp" || value === undefined || value === null) {
        return;
      }

      if (typeof value === "number") {
        entry[key] = value;
        return;
      }

      if (typeof value === "string") {
        const parsed = Number(value);
        if (!Number.isNaN(parsed)) {
          entry[key] = parsed;
        }
      }
    });

    return entry;
  });
}

export default function DashboardPage() {
  const [dashboardData, setDashboardData] = useState<DashboardData>(fallbackDashboard);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const loadDashboard = async () => {
      setLoading(true);
      try {
        const response = await apiClient.getDashboardData('runpod');
        if (cancelled) {
          return;
        }

        if (response.success && response.data) {
          const sanitizedSeries = sanitizeTimeseries(response.data.timeseries);

          setDashboardData((prev) => {
            const metrics =
              response.data?.metrics ?? prev.metrics ?? fallbackDashboard.metrics;
            const agents =
              response.data?.agents ?? prev.agents ?? fallbackDashboard.agents;
            const recommendations =
              response.data?.recommendations ??
              prev.recommendations ??
              [];
            const recentExecutions =
              response.data?.recent_executions ??
              prev.recent_executions ??
              [];
            const timeseries =
              sanitizedSeries.length > 0
                ? sanitizedSeries
                : prev.timeseries && prev.timeseries.length > 0
                ? prev.timeseries
                : fallbackTimeseries;

            return {
              agents,
              metrics,
              timeseries,
              recommendations,
              recent_executions: recentExecutions,
            };
          });
          setError(null);
        } else if (response.error) {
          setError(response.error);
        } else {
          setError("Unable to load dashboard data.");
        }
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
        if (!cancelled) {
          setError("Showing cached sample data while the dashboard refreshes.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadDashboard();
    const interval = setInterval(loadDashboard, 60000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const agentsByType = useMemo(() => {
    const map = new Map<AgentType, Agent>();
    dashboardData.agents.forEach((agent) => {
      map.set(agent.agent_type, agent);
    });
    return map;
  }, [dashboardData.agents]);

  const cardMetrics = useMemo<Partial<Record<AgentType, AgentCardMetric | undefined>>>(() => {
    const metrics = dashboardData.metrics;
    const result: Partial<Record<AgentType, AgentCardMetric | undefined>> = {};

    if (metrics?.cost) {
      const monthlyCost = metrics.cost.monthly_cost ?? metrics.cost.total_cost;
      const value = monthlyCost !== undefined ? formatCurrency(monthlyCost, metrics.cost.currency) : undefined;
      const trendValue = formatTrend(metrics.cost.cost_trend);
      result.cost =
        value !== undefined
          ? {
              value,
              label: "Monthly Cost",
              ...(trendValue
                ? {
                    trend: getTrendDirection(metrics.cost.cost_trend),
                    trendValue,
                  }
                : {}),
            }
          : undefined;
    }

    if (metrics?.performance) {
      const latency = formatLatency(metrics.performance.latency_p95);
      result.performance = latency
        ? {
            value: latency,
            label: "P95 Latency",
          }
        : undefined;
    }

    if (metrics?.resource) {
      const gpu = formatUtilization(metrics.resource.gpu_utilization);
      result.resource = gpu
        ? {
            value: gpu,
            label: "GPU Utilization",
          }
        : undefined;
    }

    if (metrics?.quality) {
      const quality = formatQualityScore(metrics.quality.quality_score);
      result.application = quality
        ? {
            value: quality,
            label: "Quality Score",
          }
        : undefined;
    }

    return result;
  }, [dashboardData.metrics]);

  let chartData: { timestamp: string; [key: string]: string | number }[];
  
  if (dashboardData.timeseries && dashboardData.timeseries.length > 0) {
    chartData = dashboardData.timeseries.map(item => ({
      timestamp: item.timestamp,
      cost: item.cost || 0,
      latency: item.latency || 0,
      gpu: item.gpu || 0,
      quality: item.quality || 0,
    }));
  } else {
    chartData = fallbackTimeseries;
  }

  const handleApprove = async (id: string) => {
    try {
      const response = await apiClient.approveRecommendation(id);
      if (!response.success) {
        throw new Error(response.error || "Approval failed.");
      }

      const approved = response.data;

      setDashboardData((prev) => ({
        ...prev,
        recommendations: prev.recommendations.map((rec) =>
          rec.id === id
            ? approved ?? {
                ...rec,
                status: "approved",
                updated_at: new Date().toISOString(),
              }
            : rec
        ),
      }));
      setError(null);
    } catch (err) {
      console.error("Failed to approve recommendation:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Failed to approve recommendation."
      );
    }
  };

  const handleReject = async (id: string) => {
    try {
      const response = await apiClient.rejectRecommendation(id);
      if (!response.success) {
        throw new Error(response.error || "Rejection failed.");
      }

      const rejected = response.data;

      setDashboardData((prev) => ({
        ...prev,
        recommendations: prev.recommendations.map((rec) =>
          rec.id === id
            ? rejected ?? {
                ...rec,
                status: "rejected",
                updated_at: new Date().toISOString(),
              }
            : rec
        ),
      }));
      setError(null);
    } catch (err) {
      console.error("Failed to reject recommendation:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Failed to reject recommendation."
      );
    }
  };

  const orderedAgentTypes: AgentType[] = [
    "cost",
    "performance",
    "resource",
    "application",
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Overview</h1>
        <p className="mt-1 text-gray-500">
          Monitor all agents and their performance metrics.
        </p>
        {loading && (
          <p className="mt-2 text-sm text-gray-500">
            Loading the latest dashboard data...
          </p>
        )}
        {error && (
          <p className="mt-2 text-sm text-yellow-700">
            {error}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        {orderedAgentTypes.map((type) => {
          const agent = agentsByType.get(type);
          if (!agent) {
            return null;
          }

          return (
            <AgentStatusCard
              key={agent.agent_id}
              agent={agent}
              metric={cardMetrics[type]}
            />
          );
        })}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <MetricsChart
          title="Cost Trends"
          data={chartData}
          dataKeys={[{ key: "cost", color: "#0ea5e9", label: "Cost ($)" }]}
          type="area"
        />
        <MetricsChart
          title="Performance Metrics"
          data={chartData}
          dataKeys={[
            { key: "latency", color: "#8b5cf6", label: "Latency (ms)" },
            { key: "gpu", color: "#10b981", label: "GPU (%)" },
          ]}
          type="line"
        />
      </div>

      <div>
        <h2 className="mb-4 text-2xl font-bold text-gray-900">
          Pending Recommendations
        </h2>
        {dashboardData.recommendations.length === 0 ? (
          <p className="text-sm text-gray-500">
            No pending recommendations at the moment.
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {dashboardData.recommendations.map((rec) => (
              <RecommendationCard
                key={rec.id}
                recommendation={rec}
                onApprove={handleApprove}
                onReject={handleReject}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
