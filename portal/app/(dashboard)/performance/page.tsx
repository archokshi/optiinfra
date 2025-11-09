"use client";

import { useEffect, useState } from "react";
import { AgentStatusCard } from "@/components/dashboard/agent-status-card";
import { MetricsChart } from "@/components/dashboard/metrics-chart";
import { RecommendationCard } from "@/components/dashboard/recommendation-card";
import type { Agent, Recommendation, DashboardData } from "@/lib/types";
import {
  asRunPodPlaceholder,
  formatDateTime,
  formatNumber,
  isRunPodDashboardSection,
} from "@/lib/runpod";

class PerformanceAgentClient {
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
      console.error(`Performance Agent API Error [${endpoint}]:`, error);
      return null;
    }
  }

  async getDashboardData(provider?: string): Promise<DashboardData | null> {
    const params = provider ? `?provider=${provider}` : '';
    return this.request<DashboardData>(`/dashboard${params}`);
  }
}

const performanceAgentClient = new PerformanceAgentClient();

export default function PerformanceAgentPage() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPerformanceData = async () => {
      try {
        setLoading(true);
        const data = await performanceAgentClient.getDashboardData("runpod");
        if (data) {
          setDashboardData(data);
        } else {
          setError("Failed to fetch performance data");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchPerformanceData();
    const interval = setInterval(fetchPerformanceData, 30000);
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
          <p className="text-red-800">Error loading performance data: {error}</p>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="space-y-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800">No performance data available</p>
        </div>
      </div>
    );
  }

  const performanceAgent = dashboardData.agents?.find(agent => agent.agent_type === "performance");
  const performanceMetrics = dashboardData.metrics?.performance || {
    latency_p50: 0,
    latency_p95: 0,
    latency_p99: 0,
    throughput: 0,
    requests_per_second: 0,
    error_rate: 0,
  };
  const timeseriesData = dashboardData.timeseries || [];

  const fallbackPerformanceAgent: Agent = {
    agent_id: "perf-001",
    agent_name: "Performance Agent",
    agent_type: "performance",
    version: "1.0.0",
    status: "active",
    last_heartbeat: new Date().toISOString(),
    capabilities: ["performance_monitoring", "latency_optimization"],
    host: "localhost",
    port: 8002,
  };

  const chartData = timeseriesData.map(item => ({
    timestamp: new Date(item.timestamp).toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    }),
    latency: item.latency || 0,
    throughput: (item.latency || 0) > 0 ? 1000 / (item.latency || 1) : 0,
  }));

  const runpodMetrics = dashboardData.metrics?.runpod;
  const runpodData = isRunPodDashboardSection(runpodMetrics) ? runpodMetrics : null;
  const runpodStatus = !runpodData ? asRunPodPlaceholder(runpodMetrics) : null;
  const runpodJobStats = runpodData?.job_stats ?? [];
  const runpodJobSeries = runpodData?.job_timeseries ?? [];
  const runpodApplicationSummary = runpodData?.application_summary;

  const aggregatedSeries = runpodJobSeries.reduce<
    Record<
      string,
      {
        total_jobs: number;
        failed_jobs: number;
        throughputTotal: number;
        observations: number;
      }
    >
  >((acc, point) => {
    const bucket = point.timestamp;
    const entry = acc[bucket] || {
      total_jobs: 0,
      failed_jobs: 0,
      throughputTotal: 0,
      observations: 0,
    };
    entry.total_jobs += point.total_jobs ?? 0;
    entry.failed_jobs += point.failed_jobs ?? 0;
    if (point.avg_throughput !== undefined && !Number.isNaN(point.avg_throughput)) {
      entry.throughputTotal += point.avg_throughput;
      entry.observations += 1;
    }
    acc[bucket] = entry;
    return acc;
  }, {});

  const runpodChartData = Object.entries(aggregatedSeries)
    .sort((a, b) => new Date(a[0]).getTime() - new Date(b[0]).getTime())
    .map(([timestamp, value]) => ({
      timestamp: new Date(timestamp).toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      }),
      jobs: value.total_jobs,
      failed: value.failed_jobs,
      throughput:
        value.observations > 0 ? value.throughputTotal / value.observations : 0,
    }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Performance Agent</h1>
        <p className="text-gray-500 mt-1">
          Monitor and optimize LLM inference performance
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <AgentStatusCard
          agent={performanceAgent || fallbackPerformanceAgent}
          metric={{
            value: `${performanceMetrics.latency_p95.toFixed(1)}ms`,
            label: "P95 Latency",
            trend: "stable",
            trendValue: "0%",
          }}
        />
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <p className="text-sm text-gray-500">Throughput</p>
          <p className="text-2xl font-bold text-blue-600">
            {performanceMetrics.throughput.toFixed(1)} req/s
          </p>
          <p className="text-xs text-gray-400 mt-2">Average</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <p className="text-sm text-gray-500">P50 Latency</p>
          <p className="text-2xl font-bold text-green-600">
            {performanceMetrics.latency_p50.toFixed(1)}ms
          </p>
          <p className="text-xs text-gray-400 mt-2">Median</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <MetricsChart
          title="Latency Trends (Real-time)"
          data={chartData}
          dataKeys={[{ key: "latency", color: "#8b5cf6", label: "Latency (ms)" }]}
          type="line"
        />
        <MetricsChart
          title="Throughput"
          data={chartData}
          dataKeys={[{ key: "throughput", color: "#3b82f6", label: "Requests/s" }]}
          type="area"
        />
      </div>

      {runpodData ? (
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">RunPod Serverless Performance</h2>
            <p className="text-gray-500 mt-1">
              Real-time execution metrics captured from RunPod job telemetry
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <p className="text-sm text-gray-500">Jobs Processed (6h)</p>
              <p className="mt-2 text-2xl font-semibold text-gray-900">
                {formatNumber(runpodApplicationSummary?.total_jobs ?? 0)}
              </p>
              <p className="mt-2 text-xs text-gray-400">
                Last update {formatDateTime(runpodApplicationSummary?.last_updated)}
              </p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <p className="text-sm text-gray-500">Failed Jobs</p>
              <p className="mt-2 text-2xl font-semibold text-rose-600">
                {formatNumber(runpodApplicationSummary?.failed_jobs ?? 0)}
              </p>
              <p className="mt-2 text-xs text-gray-400">Detected within the lookback window</p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <p className="text-sm text-gray-500">Active Endpoints</p>
              <p className="mt-2 text-2xl font-semibold text-indigo-600">
                {formatNumber(runpodApplicationSummary?.active_endpoints ?? 0)}
              </p>
              <p className="mt-2 text-xs text-gray-400">
                Reporting job telemetry in the last 6 hours
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <MetricsChart
              title="RunPod Job Throughput"
              data={runpodChartData}
              dataKeys={[{ key: "throughput", color: "#2563eb", label: "Throughput (avg req/s)" }]}
              type="area"
            />
            <MetricsChart
              title="RunPod Job Volume vs Failures"
              data={runpodChartData}
              dataKeys={[
                { key: "jobs", color: "#16a34a", label: "Jobs" },
                { key: "failed", color: "#dc2626", label: "Failed" },
              ]}
              type="line"
            />
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900">Endpoint Execution Metrics</h3>
            {runpodJobStats.length > 0 ? (
              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead>
                    <tr className="text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      <th scope="col" className="px-4 py-2">Endpoint</th>
                      <th scope="col" className="px-4 py-2">Jobs</th>
                      <th scope="col" className="px-4 py-2">Failed</th>
                      <th scope="col" className="px-4 py-2">Avg Exec (ms)</th>
                      <th scope="col" className="px-4 py-2">P95 Exec (ms)</th>
                      <th scope="col" className="px-4 py-2">Avg Throughput</th>
                      <th scope="col" className="px-4 py-2">Tokens Out</th>
                      <th scope="col" className="px-4 py-2">Last Observed</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {runpodJobStats.map((row) => (
                      <tr key={row.endpoint_id} className="hover:bg-gray-50">
                        <td className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                          {row.endpoint_id}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatNumber(row.total_jobs)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatNumber(row.failed_jobs)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatNumber(row.avg_execution_ms, { maximumFractionDigits: 1 })}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatNumber(row.p95_execution_ms, { maximumFractionDigits: 1 })}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatNumber(row.avg_throughput, { maximumFractionDigits: 2 })}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatNumber(row.total_output_tokens)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatDateTime(row.last_observed)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="mt-4 text-sm text-gray-500">
                No RunPod jobs have been processed within the recent lookback window.
              </p>
            )}
          </div>

          {runpodApplicationSummary?.status_counts && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900">Job Status Breakdown</h3>
              <dl className="mt-4 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                {Object.entries(runpodApplicationSummary.status_counts).map(([status, count]) => (
                  <div key={status} className="rounded border border-gray-200 p-4">
                    <dt className="text-gray-500 uppercase tracking-wide">
                      {status.replace(/_/g, " ")}
                    </dt>
                    <dd className="mt-2 text-lg font-semibold text-gray-900">
                      {formatNumber(count)}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          )}
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
            RunPod performance metrics will appear once the collector ingests the first job
            snapshots.
          </p>
        </div>
      )}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Performance Optimization Recommendations
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
            <p className="text-gray-500">No performance optimization recommendations available at this time.</p>
          </div>
        )}
      </div>
    </div>
  );
}
