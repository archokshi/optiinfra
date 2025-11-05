/**
 * OptiInfra Portal - API Client
 */

import type {
  Agent,
  DashboardData,
  Recommendation,
  Execution,
  HealthCheck,
  ApiResponse,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...options?.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return {
        success: true,
        data,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
        timestamp: new Date().toISOString(),
      };
    }
  }

  async getHealth(): Promise<ApiResponse<HealthCheck>> {
    return this.request<HealthCheck>("/api/v1/health");
  }

  async getAgents(): Promise<ApiResponse<Agent[]>> {
    return this.request<Agent[]>("/api/v1/agents");
  }

  async getAgent(agentId: string): Promise<ApiResponse<Agent>> {
    return this.request<Agent>(`/api/v1/agents/${agentId}`);
  }

  async getDashboardData(provider?: string): Promise<ApiResponse<DashboardData>> {
    const params = provider ? `?provider=${provider}` : '';
    return this.request<DashboardData>(`/api/v1/dashboard${params}`);
  }

  async getRecommendations(): Promise<ApiResponse<Recommendation[]>> {
    return this.request<Recommendation[]>("/api/v1/recommendations");
  }

  async approveRecommendation(id: string): Promise<ApiResponse<Recommendation>> {
    return this.request<Recommendation>(`/api/v1/recommendations/${id}/approve`, {
      method: "POST",
    });
  }

  async rejectRecommendation(id: string): Promise<ApiResponse<Recommendation>> {
    return this.request<Recommendation>(`/api/v1/recommendations/${id}/reject`, {
      method: "POST",
    });
  }

  async getExecutions(): Promise<ApiResponse<Execution[]>> {
    return this.request<Execution[]>("/api/v1/executions");
  }

  async getExecution(id: string): Promise<ApiResponse<Execution>> {
    return this.request<Execution>(`/api/v1/executions/${id}`);
  }
}

export const apiClient = new ApiClient();
export { ApiClient };
