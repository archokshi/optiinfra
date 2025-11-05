"use client";

import { useEffect, useState } from "react";
import { AgentStatusCard } from "@/components/dashboard/agent-status-card";
import { MetricsChart } from "@/components/dashboard/metrics-chart";
import { RecommendationCard } from "@/components/dashboard/recommendation-card";
import type { Agent, Recommendation, DashboardData } from "@/lib/types";

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
