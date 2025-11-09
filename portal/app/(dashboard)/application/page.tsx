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
  formatKey,
  isRunPodDashboardSection,
} from "@/lib/runpod";

class ApplicationAgentClient {
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
      console.error(`Application Agent API Error [${endpoint}]:`, error);
      return null;
    }
  }

  async getDashboardData(provider?: string): Promise<DashboardData | null> {
    const params = provider ? `?provider=${provider}` : '';
    return this.request<DashboardData>(`/dashboard${params}`);
  }
}

const applicationAgentClient = new ApplicationAgentClient();

export default function ApplicationAgentPage() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchApplicationData = async () => {
      try {
        setLoading(true);
        const data = await applicationAgentClient.getDashboardData("runpod");
        if (data) {
          setDashboardData(data);
        } else {
          setError("Failed to fetch application data");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchApplicationData();
    const interval = setInterval(fetchApplicationData, 30000);
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
          <p className="text-red-800">Error loading application data: {error}</p>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="space-y-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800">No application data available</p>
        </div>
      </div>
    );
  }

  const applicationAgent = dashboardData.agents?.find(agent => agent.agent_type === "application");
  const qualityMetrics = dashboardData.metrics?.quality || {
    quality_score: 0,
    relevance_score: 0,
    coherence_score: 0,
    hallucination_rate: 0,
    toxicity_score: 0,
  };
  const timeseriesData = dashboardData.timeseries || [];

  const fallbackApplicationAgent: Agent = {
    agent_id: "app-001",
    agent_name: "Application Agent",
    agent_type: "application",
    version: "1.0.0",
    status: "active",
    last_heartbeat: new Date().toISOString(),
    capabilities: ["quality_monitoring", "validation"],
    host: "localhost",
    port: 8004,
  };

  const chartData = timeseriesData.map(item => ({
    timestamp: new Date(item.timestamp).toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    }),
    quality: item.quality || 0,
    accuracy: (item.quality || 0) * 0.95,
    consistency: (item.quality || 0) * 1.02,
  }));

  const runpodMetrics = dashboardData.metrics?.runpod;
  const runpodData = isRunPodDashboardSection(runpodMetrics) ? runpodMetrics : null;
  const runpodStatus = !runpodData ? asRunPodPlaceholder(runpodMetrics) : null;
  const runpodJobStats = runpodData?.job_stats ?? [];
  const runpodJobSeries = runpodData?.job_timeseries ?? [];
  const runpodEndpointHealth = runpodData?.endpoint_health ?? [];
  const runpodApplicationSummary = runpodData?.application_summary;

  const aggregatedSeries = runpodJobSeries.reduce<
    Record<
      string,
      {
        total_jobs: number;
        failed_jobs: number;
      }
    >
  >((acc, point) => {
    const bucket = point.timestamp;
    const entry = acc[bucket] || { total_jobs: 0, failed_jobs: 0 };
    entry.total_jobs += point.total_jobs ?? 0;
    entry.failed_jobs += point.failed_jobs ?? 0;
    acc[bucket] = entry;
    return acc;
  }, {});

  const runpodTimeline = Object.entries(aggregatedSeries)
    .sort((a, b) => new Date(a[0]).getTime() - new Date(b[0]).getTime())
    .map(([timestamp, value]) => ({
      timestamp: new Date(timestamp).toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      }),
      jobs: value.total_jobs,
      failed: value.failed_jobs,
    }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Application Agent</h1>
        <p className="text-gray-500 mt-1">
          Monitor and ensure LLM output quality and consistency
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <AgentStatusCard
          agent={applicationAgent || fallbackApplicationAgent}
          metric={{
            value: `${qualityMetrics.quality_score.toFixed(1)}%`,
            label: "Quality Score",
            trend: "stable",
            trendValue: "0%",
          }}
        />
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <p className="text-sm text-gray-500">Relevance</p>
          <p className="text-2xl font-bold text-blue-600">
            {qualityMetrics.relevance_score.toFixed(1)}%
          </p>
          <p className="text-xs text-gray-400 mt-2">Average</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <p className="text-sm text-gray-500">Coherence</p>
          <p className="text-2xl font-bold text-green-600">
            {qualityMetrics.coherence_score.toFixed(1)}%
          </p>
          <p className="text-xs text-gray-400 mt-2">Average</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <MetricsChart
          title="Quality Score Trends (Real-time)"
          data={chartData}
          dataKeys={[{ key: "quality", color: "#22c55e", label: "Quality (%)" }]}
          type="area"
        />
        <MetricsChart
          title="Quality Metrics"
          data={chartData}
          dataKeys={[
            { key: "accuracy", color: "#3b82f6", label: "Accuracy (%)" },
            { key: "consistency", color: "#10b981", label: "Consistency (%)" },
          ]}
          type="line"
        />
      </div>

      {runpodData ? (
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">RunPod Workflow Activity</h2>
            <p className="text-gray-500 mt-1">
              Job throughput and status distribution for RunPod-backed applications
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
              <p className="mt-2 text-xs text-gray-400">
                Includes errored or aborted executions
              </p>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <p className="text-sm text-gray-500">Active Endpoints</p>
              <p className="mt-2 text-2xl font-semibold text-indigo-600">
                {formatNumber(runpodApplicationSummary?.active_endpoints ?? 0)}
              </p>
              <p className="mt-2 text-xs text-gray-400">
                Reporting job activity in the last 6 hours
              </p>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <MetricsChart
              title="RunPod Job Status Timeline"
              data={runpodTimeline}
              dataKeys={[
                { key: "jobs", color: "#22c55e", label: "Jobs" },
                { key: "failed", color: "#dc2626", label: "Failed" },
              ]}
              type="line"
            />
          </div>

          {runpodApplicationSummary?.status_counts && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900">Status Breakdown</h3>
              <dl className="mt-4 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                {Object.entries(runpodApplicationSummary.status_counts).map(([status, count]) => (
                  <div key={status} className="rounded border border-gray-200 p-4">
                    <dt className="text-gray-500 uppercase tracking-wide">
                      {formatKey(status)}
                    </dt>
                    <dd className="mt-2 text-lg font-semibold text-gray-900">
                      {formatNumber(count)}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          )}

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900">Endpoint Job Metrics</h3>
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
                RunPod job metrics will appear after the first workflows execute.
              </p>
            )}
          </div>

          {runpodEndpointHealth.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900">Endpoint Queue Health</h3>
              <div className="mt-4 overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead>
                    <tr className="text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      <th scope="col" className="px-4 py-2">Endpoint</th>
                      <th scope="col" className="px-4 py-2">Jobs In Queue</th>
                      <th scope="col" className="px-4 py-2">Jobs In Progress</th>
                      <th scope="col" className="px-4 py-2">Jobs Failed</th>
                      <th scope="col" className="px-4 py-2">Observed</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {runpodEndpointHealth.map((row) => (
                      <tr key={row.endpoint_id} className="hover:bg-gray-50">
                        <td className="whitespace-nowrap px-4 py-2 font-medium text-gray-900">
                          {row.endpoint_id}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatNumber(row.jobs_in_queue)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatNumber(row.jobs_in_progress)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatNumber(row.jobs_failed)}
                        </td>
                        <td className="whitespace-nowrap px-4 py-2 text-gray-700">
                          {formatDateTime(row.observed_ts)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
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
            RunPod workflow metrics will appear once job telemetry is ingested.
          </p>
        </div>
      )}

      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Quality Improvement Recommendations
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
            <p className="text-gray-500">No quality improvement recommendations available at this time.</p>
          </div>
        )}
      </div>
    </div>
  );
}
