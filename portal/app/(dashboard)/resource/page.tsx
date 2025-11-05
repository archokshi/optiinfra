"use client";

import { useEffect, useState } from "react";
import { AgentStatusCard } from "@/components/dashboard/agent-status-card";
import { MetricsChart } from "@/components/dashboard/metrics-chart";
import { RecommendationCard } from "@/components/dashboard/recommendation-card";
import type { Agent, Recommendation, DashboardData } from "@/lib/types";

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
