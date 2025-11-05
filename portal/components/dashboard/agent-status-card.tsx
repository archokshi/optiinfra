"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Activity,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Gauge,
  Cpu,
  Sparkles,
  type LucideIcon,
} from "lucide-react";
import type { Agent, AgentType } from "@/lib/types";
import { formatRelativeTime } from "@/lib/utils";

interface AgentStatusCardProps {
  agent: Agent;
  metric?: {
    value: string;
    label: string;
    trend?: "up" | "down" | "stable";
    trendValue?: string;
  };
}

const agentIcons: Record<AgentType, LucideIcon> = {
  cost: DollarSign,
  performance: Gauge,
  resource: Cpu,
  application: Sparkles,
};

export function AgentStatusCard({ agent, metric }: AgentStatusCardProps) {
  const Icon = agentIcons[agent.agent_type] ?? Activity;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">
          <div className="flex items-center gap-2">
            <Icon className="h-5 w-5 text-sky-600" aria-hidden="true" />
            {agent.agent_name}
          </div>
        </CardTitle>
        <Activity className="h-4 w-4 text-gray-500" />
      </CardHeader>
      <CardContent>
        <div className="mb-4 flex items-center justify-between">
          <span className="text-xs text-gray-500">Status:</span>
          <Badge
            variant={
              agent.status === "active"
                ? "success"
                : agent.status === "degraded"
                ? "warning"
                : "error"
            }
          >
            {agent.status}
          </Badge>
        </div>

        {metric ? (
          <>
            <div className="text-2xl font-bold">{metric.value}</div>
            <p className="mt-1 text-xs text-gray-500">{metric.label}</p>

            {metric.trend && metric.trendValue && (
              <div className="mt-2 flex items-center gap-1">
                {metric.trend === "up" ? (
                  <TrendingUp className="h-3 w-3 text-green-600" />
                ) : metric.trend === "down" ? (
                  <TrendingDown className="h-3 w-3 text-red-600" />
                ) : null}
                <span
                  className={`text-xs ${
                    metric.trend === "up"
                      ? "text-green-600"
                      : metric.trend === "down"
                      ? "text-red-600"
                      : "text-gray-600"
                  }`}
                >
                  {metric.trendValue}
                </span>
              </div>
            )}
          </>
        ) : (
          <p className="text-sm text-gray-500">Metric data not available.</p>
        )}

        <div className="mt-4 border-t border-gray-100 pt-4">
          <p className="text-xs text-gray-400">
            Last heartbeat: {formatRelativeTime(agent.last_heartbeat)}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
