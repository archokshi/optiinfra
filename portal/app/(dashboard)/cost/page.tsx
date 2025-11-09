"use client";

import { useEffect, useState } from "react";
import { AgentStatusCard } from "@/components/dashboard/agent-status-card";
import { MetricsChart } from "@/components/dashboard/metrics-chart";
import { RecommendationCard } from "@/components/dashboard/recommendation-card";
import type { Agent, Recommendation, DashboardData, RunPodDashboardSection } from "@/lib/types";
import {
  asRunPodPlaceholder,
  formatCurrency,
  formatDateTime,
  formatDetailValue,
  formatKey,
  formatNumber,
  isRunPodDashboardSection,
} from "@/lib/runpod";

// Create a Cost Agent API client
class CostAgentClient {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T | null> {
    try {
      const response = await fetch(`/api${endpoint}`, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...options?.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Cost Agent API Error [${endpoint}]:`, error);
      return null;
    }
  }

  async getDashboardData(provider?: string): Promise<DashboardData | null> {
    const params = provider ? `?provider=${provider}` : '';
    return this.request<DashboardData>(`/dashboard${params}`);
  }
}

const costAgentClient = new CostAgentClient();

export default function CostAgentPage() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchCostData = async () => {
      try {
        setLoading(true);
        const data = await costAgentClient.getDashboardData("runpod");
        if (data) {
          setDashboardData(data);
        } else {
          setError("Failed to fetch cost data");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchCostData();
  }, []);

  const handleApprove = (id: string) => {
    console.log("Approve recommendation:", id);
  };

  const handleReject = (id: string) => {
    console.log("Reject recommendation:", id);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-32 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading cost data: {error}</p>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="space-y-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800">No cost data available</p>
        </div>
      </div>
    );
  }

  // Find the cost agent from the agents list
  const costAgent = dashboardData.agents?.find((agent) => agent.agent_type === "cost");
  const costMetrics = dashboardData.metrics?.cost || {
    total_cost: 0,
    daily_cost: 0,
    monthly_cost: 0,
    cost_trend: 0,
    savings_potential: 0,
    currency: "USD",
  };
  const timeseriesData = dashboardData.timeseries || [];
  const currency = costMetrics.currency || "USD";
  const costTrendValue = Number.isFinite(costMetrics.cost_trend)
    ? `${formatNumber(costMetrics.cost_trend, { maximumFractionDigits: 1 })}%`
    : "0%";
  const costTrendDirection =
    costMetrics.cost_trend > 0 ? "up" : costMetrics.cost_trend < 0 ? "down" : "stable";

  // Fallback cost agent if not found in the data
  const fallbackCostAgent: Agent = {
    agent_id: "cost-001",
    agent_name: "Cost Agent",
    agent_type: "cost",
    version: "1.0.0",
    status: "active",
    last_heartbeat: new Date().toISOString(),
    capabilities: ["cost_tracking", "optimization"],
    host: "localhost",
    port: 8001,
  };

  // Transform timeseries data for the chart
  const chartData = timeseriesData.map((item) => ({
    timestamp: new Date(item.timestamp).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    }),
    cost: item.cost || 0,
    savings: (item.cost || 0) * 0.1, // Show 10% as potential savings
  }));

  const runpodMetrics = dashboardData.metrics?.runpod;
  const runpodData = isRunPodDashboardSection(runpodMetrics) ? runpodMetrics : null;
  const runpodStatus = !runpodData ? asRunPodPlaceholder(runpodMetrics) : null;
  const latestBilling = runpodData?.billing?.[0];
  const spendBreakdownEntries = latestBilling
    ? Object.entries(latestBilling.spend_breakdown ?? {})
    : [];
  const endpointHealthRows = runpodData?.endpoint_health ?? [];
  const podRows = runpodData?.pods ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Cost Agent</h1>
        <p className="text-gray-500 mt-1">
          Monitor and optimize LLM infrastructure costs
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <AgentStatusCard
          agent={costAgent || fallbackCostAgent}
          metric={{
            value: formatCurrency(costMetrics.total_cost, currency),
            label: "Monthly Cost",
            trend: costTrendDirection,
            trendValue: costTrendValue,
          }}
        />
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <p className="text-sm text-gray-500">Potential Savings</p>
          <p className="text-2xl font-bold text-green-600">
            {formatCurrency(costMetrics.savings_potential, currency)}
          </p>
          <p className="text-xs text-gray-400 mt-2">Available optimizations</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <p className="text-sm text-gray-500">Daily Cost</p>
          <p className="text-2xl font-bold text-blue-600">
            {formatCurrency(costMetrics.daily_cost, currency)}
          </p>
          <p className="text-xs text-gray-400 mt-2">Last 24 hours</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <MetricsChart
          title="Cost Trends (Real-time)"
          data={chartData}
          dataKeys={[{ key: "cost", color: "#ef4444", label: "Cost ($)" }]}
          type="area"
        />
        <MetricsChart
          title="Potential Savings"
          data={chartData}
          dataKeys={[{ key: "savings", color: "#22c55e", label: "Savings ($)" }]}
          type="bar"
        />
      </div>

      {runpodData ? (
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">RunPod Insights</h2>
            <p className="text-gray-500 mt-1">
              Live telemetry collected from RunPod staging tables
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <p className="text-sm text-gray-500">Current Spend / hr</p>
              <p className="mt-2 text-2xl font-semibold text-gray-900">
                {formatCurrency(latestBilling?.avg_spend_per_hr, currency)}
              </p>
              <p className="mt-2 text-xs text-gray-400">
                Snapshot {formatDateTime(latestBilling?.snapshot_date, { dateStyle: "medium" })}
              </p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <p className="text-sm text-gray-500">Lifetime Spend</p>
              <p className="mt-2 text-2xl font-semibold text-gray-900">
                {formatCurrency(latestBilling?.lifetime_spend, currency)}
              </p>
              <p className="mt-2 text-xs text-gray-400">RunPod account cumulative total</p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <p className="text-sm text-gray-500">Available Balance</p>
              <p className="mt-2 text-2xl font-semibold text-emerald-600">
                {formatCurrency(latestBilling?.balance, currency)}
              </p>
              <p className="mt-2 text-xs text-gray-400">Reported by RunPod billing</p>
            </div>
          </div>

          {spendBreakdownEntries.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900">Spend Breakdown</h3>
              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {spendBreakdownEntries.map(([product, raw]) => {
                  const details =
                    raw && typeof raw === "object" ? (raw as Record<string, unknown>) : { total: raw };
                  return (
                    <div key={product} className="rounded border border-gray-200 p-4">
                      <p className="text-sm font-semibold text-gray-700">{formatKey(product)}</p>
                      <dl className="mt-2 space-y-1 text-sm text-gray-500">
                        {Object.entries(details).map(([key, value]) => (
                          <div key={key} className="flex justify-between gap-3">
                            <dt className="truncate">{formatKey(key)}</dt>
                            <dd className="font-medium text-gray-700">
                              {formatDetailValue(value)}
                            </dd>
                          </div>
                        ))}
                      </dl>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900">Billing History</h3>
            {runpodData.billing.length > 0 ? (
              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead>
                    <tr className="text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      <th scope="col" className="px-4 py-2">Snapshot Date</th>
                      <th scope="col" className="px-4 py-2">Average Spend / hr</th>
                      <th scope="col" className="px-4 py-2">Lifetime Spend</th>
                      <th scope="col" className="px-4 py-2">Balance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {runpodData.billing.map((row, index) => (
                      <tr key={`${row.snapshot_date}-${index}`} className="hover:bg-gray-50">
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatDateTime(row.snapshot_date, { dateStyle: "medium" })}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          <span>{formatCurrency(row.avg_spend_per_hr, currency)}</span>
                          <span className="ml-1 text-xs text-gray-400">/hr</span>
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatCurrency(row.lifetime_spend, currency)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatCurrency(row.balance, currency)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="mt-4 text-sm text-gray-500">
                No billing snapshots have been ingested for this customer.
              </p>
            )}
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900">Endpoint Health</h3>
            {endpointHealthRows.length > 0 ? (
              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead>
                    <tr className="text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      <th scope="col" className="px-4 py-2">Endpoint</th>
                      <th scope="col" className="px-4 py-2">Completed</th>
                      <th scope="col" className="px-4 py-2">Failed</th>
                      <th scope="col" className="px-4 py-2">In Progress</th>
                      <th scope="col" className="px-4 py-2">In Queue</th>
                      <th scope="col" className="px-4 py-2">Workers Running</th>
                      <th scope="col" className="px-4 py-2">Workers Idle</th>
                      <th scope="col" className="px-4 py-2">Workers Throttled</th>
                      <th scope="col" className="px-4 py-2">Observed</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {endpointHealthRows.map((row) => (
                      <tr key={row.endpoint_id} className="hover:bg-gray-50">
                        <td className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                          {row.endpoint_id}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatNumber(row.jobs_completed)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatNumber(row.jobs_failed)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatNumber(row.jobs_in_progress)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatNumber(row.jobs_in_queue)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatNumber(row.workers_running)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatNumber(row.workers_idle)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatNumber(row.workers_throttled)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatDateTime(row.observed_ts)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="mt-4 text-sm text-gray-500">
                No endpoint health checks have been recorded for RunPod yet.
              </p>
            )}
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900">Active Pods</h3>
            {podRows.length > 0 ? (
              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead>
                    <tr className="text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      <th scope="col" className="px-4 py-2">Pod</th>
                      <th scope="col" className="px-4 py-2">Status</th>
                      <th scope="col" className="px-4 py-2">GPU Type</th>
                      <th scope="col" className="px-4 py-2">GPUs</th>
                      <th scope="col" className="px-4 py-2">vCPUs</th>
                      <th scope="col" className="px-4 py-2">Memory (GB)</th>
                      <th scope="col" className="px-4 py-2">Cost / hr</th>
                      <th scope="col" className="px-4 py-2">Snapshot</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {podRows.map((row) => (
                      <tr key={row.pod_id} className="hover:bg-gray-50">
                        <td className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                          {row.pod_id}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700 capitalize">
                          {row.status || "unknown"}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {row.gpu_type_id || "—"}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatNumber(row.gpu_count, { maximumFractionDigits: 0 })}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatNumber(row.vcpu_count, { maximumFractionDigits: 0 })}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatNumber(row.memory_gb, { maximumFractionDigits: 1 })}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          <span>{formatCurrency(row.cost_per_hour, currency)}</span>
                          <span className="ml-1 text-xs text-gray-400">/hr</span>
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatDateTime(row.snapshot_ts)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="mt-4 text-sm text-gray-500">No active pods reported by RunPod.</p>
            )}
          </div>
        </div>
      ) : runpodStatus ? (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-blue-800">
            RunPod metrics status: {formatKey(runpodStatus.status)}.
            {runpodStatus.note ? ` ${runpodStatus.note}` : ""}
          </p>
        </div>
      ) : runpodMetrics === undefined ? null : (
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
          <p className="text-slate-700">
            RunPod metrics will appear once the data collector ingests the first snapshot.
          </p>
        </div>
      )}

      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Cost Optimization Recommendations
        </h2>
        {dashboardData.recommendations.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {dashboardData.recommendations.map((rec) => (
              <RecommendationCard
                key={rec.id}
                recommendation={rec}
                onApprove={handleApprove}
                onReject={handleReject}
              />
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <p className="text-gray-500">No cost optimization recommendations available at this time.</p>
          </div>
        )}
      </div>
    </div>
  );
}
