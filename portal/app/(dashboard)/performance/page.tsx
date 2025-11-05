"use client";

import { useEffect, useState } from "react";
import { AgentStatusCard } from "@/components/dashboard/agent-status-card";
import { MetricsChart } from "@/components/dashboard/metrics-chart";
import { RecommendationCard } from "@/components/dashboard/recommendation-card";
import type { Agent, Recommendation, DashboardData } from "@/lib/types";

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
