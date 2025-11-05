"use client";

import { useEffect, useState } from "react";
import { AgentStatusCard } from "@/components/dashboard/agent-status-card";
import { MetricsChart } from "@/components/dashboard/metrics-chart";
import { RecommendationCard } from "@/components/dashboard/recommendation-card";
import type { Agent, Recommendation, DashboardData } from "@/lib/types";

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
  const costAgent = dashboardData.agents?.find(agent => agent.agent_type === "cost");
  const costMetrics = dashboardData.metrics?.cost || {
    total_cost: 0,
    daily_cost: 0,
    monthly_cost: 0,
    cost_trend: 0,
    savings_potential: 0,
    currency: "USD",
  };
  const timeseriesData = dashboardData.timeseries || [];

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
  const chartData = timeseriesData.map(item => ({
    timestamp: new Date(item.timestamp).toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    }),
    cost: item.cost || 0,
    savings: (item.cost || 0) * 0.1, // Show 10% as potential savings
  }));

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
            value: `$${costMetrics.total_cost.toFixed(2)}`,
            label: "Monthly Cost",
            trend: "stable",
            trendValue: costMetrics.cost_trend ? `${costMetrics.cost_trend.toFixed(1)}%` : "0%",
          }}
        />
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <p className="text-sm text-gray-500">Potential Savings</p>
          <p className="text-2xl font-bold text-green-600">
            ${costMetrics.savings_potential.toFixed(2)}
          </p>
          <p className="text-xs text-gray-400 mt-2">Available optimizations</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <p className="text-sm text-gray-500">Daily Cost</p>
          <p className="text-2xl font-bold text-blue-600">
            ${costMetrics.daily_cost.toFixed(2)}
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
