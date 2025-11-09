"use client";

import { useEffect, useState } from "react";
import { AgentStatusCard } from "@/components/dashboard/agent-status-card";
import { MetricsChart } from "@/components/dashboard/metrics-chart";
import { RecommendationCard } from "@/components/dashboard/recommendation-card";
import type { Agent, Recommendation, DashboardData } from "@/lib/types";
import {
  asRunPodPlaceholder,
  formatCurrency,
  formatDateTime,
  formatNumber,
  isRunPodDashboardSection,
  formatKey,
} from "@/lib/runpod";

class ResourceAgentClient {
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
      console.error(`Resource Agent API Error [${endpoint}]:`, error);
      return null;
    }
  }

  async getDashboardData(provider?: string): Promise<DashboardData | null> {
    const params = provider ? `?provider=${provider}` : '';
    return this.request<DashboardData>(`/dashboard${params}`);
  }
}

const resourceAgentClient = new ResourceAgentClient();

export default function ResourceAgentPage() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchResourceData = async () => {
      try {
        setLoading(true);
        const data = await resourceAgentClient.getDashboardData("runpod");
        if (data) {
          setDashboardData(data);
        } else {
          setError("Failed to fetch resource data");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchResourceData();
    const interval = setInterval(fetchResourceData, 30000);
    return () => clearInterval(interval);
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
          <p className="text-red-800">Error loading resource data: {error}</p>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="space-y-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800">No resource data available</p>
        </div>
      </div>
    );
  }

  const resourceAgent = dashboardData.agents?.find(agent => agent.agent_type === "resource");
  const resourceMetrics = dashboardData.metrics?.resource || {
    gpu_utilization: 0,
    cpu_utilization: 0,
    memory_utilization: 0,
    gpu_memory_used: 0,
    gpu_memory_total: 0,
  };
  const timeseriesData = dashboardData.timeseries || [];

  const fallbackResourceAgent: Agent = {
    agent_id: "resource-001",
    agent_name: "Resource Agent",
    agent_type: "resource",
    version: "1.0.0",
    status: "active",
    last_heartbeat: new Date().toISOString(),
    capabilities: ["resource_monitoring", "gpu_optimization"],
    host: "localhost",
    port: 8003,
  };

  const chartData = timeseriesData.map(item => ({
    timestamp: new Date(item.timestamp).toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    }),
    gpu: item.gpu || 0,
    memory: (item.gpu || 0) * 0.9,
    cpu: (item.gpu || 0) * 0.6,
  }));

  const runpodMetrics = dashboardData.metrics?.runpod;
  const runpodData = isRunPodDashboardSection(runpodMetrics) ? runpodMetrics : null;
  const runpodStatus = !runpodData ? asRunPodPlaceholder(runpodMetrics) : null;
  const resourceSummary = runpodData?.resource_summary;
  const pods = runpodData?.pods ?? [];
  const endpointHealth = runpodData?.endpoint_health ?? [];
  const gpuTypes = resourceSummary?.gpu_types ?? [];
  const podsByStatus = resourceSummary?.pods_by_status ?? {};
  const totalRunpodCost = pods.reduce((acc, pod) => acc + (pod.cost_per_hour || 0), 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Resource Agent</h1>
        <p className="text-gray-500 mt-1">
          Monitor and optimize infrastructure resource utilization
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <AgentStatusCard
          agent={resourceAgent || fallbackResourceAgent}
          metric={{
            value: `${resourceMetrics.gpu_utilization.toFixed(1)}%`,
            label: "GPU Utilization",
            trend: "stable",
            trendValue: "0%",
          }}
        />
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <p className="text-sm text-gray-500">Memory Usage</p>
          <p className="text-2xl font-bold text-orange-600">
            {resourceMetrics.memory_utilization.toFixed(1)}%
          </p>
          <p className="text-xs text-gray-400 mt-2">Average</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <p className="text-sm text-gray-500">CPU Usage</p>
          <p className="text-2xl font-bold text-purple-600">
            {resourceMetrics.cpu_utilization.toFixed(1)}%
          </p>
          <p className="text-xs text-gray-400 mt-2">Average</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <MetricsChart
          title="GPU Utilization (Real-time)"
          data={chartData}
          dataKeys={[{ key: "gpu", color: "#10b981", label: "GPU (%)" }]}
          type="area"
        />
        <MetricsChart
          title="Resource Usage"
          data={chartData}
          dataKeys={[
            { key: "memory", color: "#f59e0b", label: "Memory (%)" },
            { key: "cpu", color: "#8b5cf6", label: "CPU (%)" },
          ]}
          type="line"
        />
      </div>

      {runpodData ? (
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">RunPod Resource Inventory</h2>
            <p className="text-gray-500 mt-1">
              Live pod inventory, GPU capacity, and worker availability from the RunPod staging
              tables
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <p className="text-sm text-gray-500">Total Pods</p>
              <p className="mt-2 text-2xl font-semibold text-gray-900">
                {formatNumber(resourceSummary?.total_pods ?? pods.length)}
              </p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <p className="text-sm text-gray-500">Total GPUs</p>
              <p className="mt-2 text-2xl font-semibold text-emerald-600">
                {formatNumber(resourceSummary?.total_gpus ?? 0)}
              </p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <p className="text-sm text-gray-500">Total Memory</p>
              <p className="mt-2 text-2xl font-semibold text-indigo-600">
                {formatNumber(resourceSummary?.total_memory_gb ?? 0, { maximumFractionDigits: 1 })} GB
              </p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <p className="text-sm text-gray-500">Estimated Cost / hr</p>
              <p className="mt-2 text-2xl font-semibold text-rose-600">
                {formatCurrency(totalRunpodCost)}
              </p>
              <p className="mt-2 text-xs text-gray-400">
                Sum of current pod hourly rates
              </p>
            </div>
          </div>

          {Object.keys(podsByStatus).length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900">Pod Status Breakdown</h3>
              <div className="mt-4 flex flex-wrap gap-3 text-sm">
                {Object.entries(podsByStatus).map(([status, count]) => (
                  <span
                    key={status}
                    className="inline-flex items-center rounded-full border border-gray-200 px-3 py-1 text-gray-700"
                  >
                    <span className="font-medium">
                      {formatKey(status)}
                    </span>
                    <span className="ml-2 text-xs text-gray-500">
                      {formatNumber(count)}
                    </span>
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900">Active Pods</h3>
            {pods.length > 0 ? (
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
                    {pods.map((row) => (
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
                          {formatCurrency(row.cost_per_hour)}
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
              <p className="mt-4 text-sm text-gray-500">
                No RunPod pod snapshots have been recorded yet.
              </p>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900">GPU Type Summary</h3>
              {gpuTypes.length > 0 ? (
                <div className="mt-4 overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 text-sm">
                    <thead>
                      <tr className="text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                        <th scope="col" className="px-4 py-2">GPU Type</th>
                        <th scope="col" className="px-4 py-2">Pods</th>
                        <th scope="col" className="px-4 py-2">GPUs</th>
                        <th scope="col" className="px-4 py-2">Cost / hr</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {gpuTypes.map((entry) => (
                        <tr key={entry.gpu_type_id} className="hover:bg-gray-50">
                          <td className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                            {entry.gpu_type_id}
                          </td>
                          <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                            {formatNumber(entry.pods)}
                          </td>
                          <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                            {formatNumber(entry.gpus)}
                          </td>
                          <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                            {formatCurrency(entry.cost_per_hour)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="mt-4 text-sm text-gray-500">
                  GPU type summaries will appear after the first pod snapshots are ingested.
                </p>
              )}
            </div>

            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900">Endpoint Worker Capacity</h3>
              {endpointHealth.length > 0 ? (
                <div className="mt-4 overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 text-sm">
                    <thead>
                      <tr className="text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                        <th scope="col" className="px-4 py-2">Endpoint</th>
                        <th scope="col" className="px-4 py-2">Workers Running</th>
                        <th scope="col" className="px-4 py-2">Workers Idle</th>
                        <th scope="col" className="px-4 py-2">Jobs In Queue</th>
                        <th scope="col" className="px-4 py-2">Observed</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {endpointHealth.map((row) => (
                        <tr key={row.endpoint_id} className="hover:bg-gray-50">
                          <td className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                            {row.endpoint_id}
                          </td>
                          <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                            {formatNumber(row.workers_running)}
                          </td>
                          <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                            {formatNumber(row.workers_idle)}
                          </td>
                          <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                            {formatNumber(row.jobs_in_queue)}
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
                  No endpoint worker telemetry is available yet for RunPod.
                </p>
              )}
            </div>
          </div>
        </div>
      ) : runpodStatus ? (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-blue-800">
            RunPod metrics status: {runpodStatus.status}.
            {runpodStatus.note ? ` ${runpodStatus.note}` : ""}
          </p>
        </div>
      ) : runpodMetrics === undefined ? null : (
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
          <p className="text-slate-700">
            RunPod resource metrics will appear once pod snapshots are ingested.
          </p>
        </div>
      )}

      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Resource Optimization Recommendations
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
            <p className="text-gray-500">No resource optimization recommendations available at this time.</p>
          </div>
        )}
      </div>
    </div>
  );
}
