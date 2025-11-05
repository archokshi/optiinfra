# PHASE5-5.2 PART1: Dashboard Components - Code Implementation Plan

**Phase**: PHASE5-5.2  
**Component**: Portal & Production  
**Objective**: Create all dashboards, charts, and real-time components  
**Estimated Time**: 40+30m = 70 minutes total  
**Priority**: HIGH  
**Dependencies**: PHASE5-5.1 (Next.js Setup)

---

## Overview

This phase creates comprehensive dashboard components for monitoring all 4 agents (Cost, Performance, Resource, Application) with real-time metrics, charts, and interactive visualizations.

---

## Dashboard Components Purpose

### **Primary Features**
1. **Agent Status Cards** - Real-time status for all agents
2. **Metrics Visualization** - Charts for cost, performance, resource, quality
3. **Recommendations Panel** - View and manage optimization recommendations
4. **Execution History** - Track all optimization executions
5. **Real-time Updates** - Live data refresh (polling/WebSocket ready)

### **Key Components**
- Agent status cards with health indicators
- Line/bar charts for metrics
- Recommendation cards with approve/reject
- Execution history table
- Navigation sidebar
- Header with breadcrumbs

---

## Implementation Plan

### Step 1: Install Chart Library (5 minutes)

```bash
cd portal
npm install recharts
npm install lucide-react  # For icons
```

**Dependencies:**
- `recharts` - Chart library for React
- `lucide-react` - Icon library

---

### Step 2: Create UI Components (components/ui/) (15 minutes)

#### Card Component (`components/ui/card.tsx`)

```typescript
import { cn } from "@/lib/utils";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}

export function Card({ className, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-lg border border-gray-200 bg-white shadow-sm",
        className
      )}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }: CardProps) {
  return (
    <div
      className={cn("flex flex-col space-y-1.5 p-6", className)}
      {...props}
    />
  );
}

export function CardTitle({ className, ...props }: CardProps) {
  return (
    <h3
      className={cn("text-2xl font-semibold leading-none tracking-tight", className)}
      {...props}
    />
  );
}

export function CardDescription({ className, ...props }: CardProps) {
  return (
    <p
      className={cn("text-sm text-gray-500", className)}
      {...props}
    />
  );
}

export function CardContent({ className, ...props }: CardProps) {
  return <div className={cn("p-6 pt-0", className)} {...props} />;
}

export function CardFooter({ className, ...props }: CardProps) {
  return (
    <div
      className={cn("flex items-center p-6 pt-0", className)}
      {...props}
    />
  );
}
```

#### Badge Component (`components/ui/badge.tsx`)

```typescript
import { cn } from "@/lib/utils";

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "success" | "warning" | "error" | "info";
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors",
        {
          "bg-gray-100 text-gray-800": variant === "default",
          "bg-green-100 text-green-800": variant === "success",
          "bg-yellow-100 text-yellow-800": variant === "warning",
          "bg-red-100 text-red-800": variant === "error",
          "bg-blue-100 text-blue-800": variant === "info",
        },
        className
      )}
      {...props}
    />
  );
}
```

#### Button Component (`components/ui/button.tsx`)

```typescript
import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline" | "ghost" | "destructive";
  size?: "default" | "sm" | "lg";
}

export function Button({
  className,
  variant = "default",
  size = "default",
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-md font-medium transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
        "disabled:pointer-events-none disabled:opacity-50",
        {
          "bg-primary-600 text-white hover:bg-primary-700": variant === "default",
          "border border-gray-300 bg-white hover:bg-gray-50": variant === "outline",
          "hover:bg-gray-100": variant === "ghost",
          "bg-red-600 text-white hover:bg-red-700": variant === "destructive",
        },
        {
          "h-10 px-4 py-2": size === "default",
          "h-9 px-3 text-sm": size === "sm",
          "h-11 px-8": size === "lg",
        },
        className
      )}
      {...props}
    />
  );
}
```

---

### Step 3: Create Dashboard Components (components/dashboard/) (25 minutes)

#### Agent Status Card (`components/dashboard/agent-status-card.tsx`)

```typescript
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Activity, TrendingUp, TrendingDown } from "lucide-react";
import type { Agent, AgentType } from "@/lib/types";
import { formatRelativeTime, getStatusColor } from "@/lib/utils";

interface AgentStatusCardProps {
  agent: Agent;
  metric?: {
    value: string;
    label: string;
    trend?: "up" | "down" | "stable";
    trendValue?: string;
  };
}

const agentIcons: Record<AgentType, React.ReactNode> = {
  cost: "💰",
  performance: "⚡",
  resource: "🖥️",
  application: "✅",
};

export function AgentStatusCard({ agent, metric }: AgentStatusCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{agentIcons[agent.agent_type]}</span>
            {agent.agent_name}
          </div>
        </CardTitle>
        <Activity className="h-4 w-4 text-gray-500" />
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between mb-4">
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

        {metric && (
          <>
            <div className="text-2xl font-bold">{metric.value}</div>
            <p className="text-xs text-gray-500 mt-1">{metric.label}</p>

            {metric.trend && metric.trendValue && (
              <div className="flex items-center gap-1 mt-2">
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
        )}

        <div className="mt-4 pt-4 border-t border-gray-100">
          <p className="text-xs text-gray-400">
            Last heartbeat: {formatRelativeTime(agent.last_heartbeat)}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
```

#### Metrics Chart Component (`components/dashboard/metrics-chart.tsx`)

```typescript
"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface MetricsChartProps {
  title: string;
  data: any[];
  dataKeys: { key: string; color: string; label: string }[];
  type?: "line" | "area" | "bar";
  height?: number;
}

export function MetricsChart({
  title,
  data,
  dataKeys,
  type = "line",
  height = 300,
}: MetricsChartProps) {
  const ChartComponent =
    type === "area" ? AreaChart : type === "bar" ? BarChart : LineChart;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          <ChartComponent data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="timestamp"
              stroke="#888888"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="#888888"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "white",
                border: "1px solid #e5e7eb",
                borderRadius: "6px",
              }}
            />
            <Legend />

            {dataKeys.map((item) => {
              if (type === "area") {
                return (
                  <Area
                    key={item.key}
                    type="monotone"
                    dataKey={item.key}
                    stroke={item.color}
                    fill={item.color}
                    fillOpacity={0.2}
                    name={item.label}
                  />
                );
              } else if (type === "bar") {
                return (
                  <Bar
                    key={item.key}
                    dataKey={item.key}
                    fill={item.color}
                    name={item.label}
                  />
                );
              } else {
                return (
                  <Line
                    key={item.key}
                    type="monotone"
                    dataKey={item.key}
                    stroke={item.color}
                    strokeWidth={2}
                    name={item.label}
                  />
                );
              }
            })}
          </ChartComponent>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
```

#### Recommendation Card (`components/dashboard/recommendation-card.tsx`)

```typescript
"use client";

import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CheckCircle, XCircle, AlertTriangle } from "lucide-react";
import type { Recommendation } from "@/lib/types";
import { formatCurrency, formatPercentage, formatDateTime } from "@/lib/utils";

interface RecommendationCardProps {
  recommendation: Recommendation;
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
}

const riskIcons = {
  low: <CheckCircle className="h-4 w-4 text-green-600" />,
  medium: <AlertTriangle className="h-4 w-4 text-yellow-600" />,
  high: <XCircle className="h-4 w-4 text-red-600" />,
};

export function RecommendationCard({
  recommendation,
  onApprove,
  onReject,
}: RecommendationCardProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg">{recommendation.title}</CardTitle>
            <p className="text-sm text-gray-500 mt-1">
              {recommendation.description}
            </p>
          </div>
          <Badge
            variant={
              recommendation.status === "pending"
                ? "info"
                : recommendation.status === "approved"
                ? "success"
                : recommendation.status === "rejected"
                ? "error"
                : "default"
            }
          >
            {recommendation.status}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          {recommendation.estimated_savings && (
            <div>
              <p className="text-xs text-gray-500">Estimated Savings</p>
              <p className="text-lg font-semibold text-green-600">
                {formatCurrency(recommendation.estimated_savings)}
              </p>
            </div>
          )}

          {recommendation.estimated_improvement && (
            <div>
              <p className="text-xs text-gray-500">Estimated Improvement</p>
              <p className="text-lg font-semibold text-blue-600">
                {formatPercentage(recommendation.estimated_improvement)}
              </p>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 mt-4">
          {riskIcons[recommendation.risk_level]}
          <span className="text-sm text-gray-600">
            {recommendation.risk_level.charAt(0).toUpperCase() +
              recommendation.risk_level.slice(1)}{" "}
            Risk
          </span>
        </div>

        <p className="text-xs text-gray-400 mt-4">
          Created: {formatDateTime(recommendation.created_at)}
        </p>
      </CardContent>

      {recommendation.status === "pending" && onApprove && onReject && (
        <CardFooter className="flex gap-2">
          <Button
            size="sm"
            onClick={() => onApprove(recommendation.id)}
            className="flex-1"
          >
            Approve
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => onReject(recommendation.id)}
            className="flex-1"
          >
            Reject
          </Button>
        </CardFooter>
      )}
    </Card>
  );
}
```

---

### Step 4: Create Layout Components (components/layout/) (10 minutes)

#### Sidebar Navigation (`components/layout/sidebar.tsx`)

```typescript
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  DollarSign,
  Zap,
  Cpu,
  CheckCircle,
  Settings,
} from "lucide-react";

const navigation = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { name: "Cost Agent", href: "/dashboard/cost", icon: DollarSign },
  { name: "Performance Agent", href: "/dashboard/performance", icon: Zap },
  { name: "Resource Agent", href: "/dashboard/resource", icon: Cpu },
  { name: "Application Agent", href: "/dashboard/application", icon: CheckCircle },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex h-full w-64 flex-col bg-white border-r border-gray-200">
      <div className="flex h-16 items-center px-6 border-b border-gray-200">
        <h1 className="text-2xl font-bold">
          Opti<span className="text-primary-600">Infra</span>
        </h1>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary-50 text-primary-600"
                  : "text-gray-700 hover:bg-gray-50"
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-gray-200 p-4">
        <p className="text-xs text-gray-500">Version 1.0.0</p>
      </div>
    </div>
  );
}
```

#### Header Component (`components/layout/header.tsx`)

```typescript
"use client";

import { Bell, User } from "lucide-react";

export function Header() {
  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Dashboard</h2>
        <p className="text-sm text-gray-500">Monitor your LLM infrastructure</p>
      </div>

      <div className="flex items-center gap-4">
        <button className="relative rounded-full p-2 hover:bg-gray-100">
          <Bell className="h-5 w-5 text-gray-600" />
          <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-red-500" />
        </button>

        <button className="flex items-center gap-2 rounded-full p-2 hover:bg-gray-100">
          <User className="h-5 w-5 text-gray-600" />
        </button>
      </div>
    </header>
  );
}
```

---

### Step 5: Update Dashboard Layout (15 minutes)

#### Dashboard Layout (`app/(dashboard)/layout.tsx`)

```typescript
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
```

#### Updated Dashboard Page (`app/(dashboard)/page.tsx`)

```typescript
"use client";

import { useEffect, useState } from "react";
import { AgentStatusCard } from "@/components/dashboard/agent-status-card";
import { MetricsChart } from "@/components/dashboard/metrics-chart";
import { RecommendationCard } from "@/components/dashboard/recommendation-card";
import type { Agent, Recommendation } from "@/lib/types";
import { apiClient } from "@/lib/api";

// Mock data for demonstration
const mockAgents: Agent[] = [
  {
    agent_id: "cost-001",
    agent_name: "Cost Agent",
    agent_type: "cost",
    version: "1.0.0",
    status: "active",
    last_heartbeat: new Date(Date.now() - 30000).toISOString(),
    capabilities: ["cost_tracking", "optimization"],
    host: "localhost",
    port: 8001,
  },
  {
    agent_id: "perf-001",
    agent_name: "Performance Agent",
    agent_type: "performance",
    version: "1.0.0",
    status: "active",
    last_heartbeat: new Date(Date.now() - 45000).toISOString(),
    capabilities: ["performance_monitoring"],
    host: "localhost",
    port: 8002,
  },
  {
    agent_id: "resource-001",
    agent_name: "Resource Agent",
    agent_type: "resource",
    version: "1.0.0",
    status: "active",
    last_heartbeat: new Date(Date.now() - 20000).toISOString(),
    capabilities: ["resource_monitoring"],
    host: "localhost",
    port: 8003,
  },
  {
    agent_id: "app-001",
    agent_name: "Application Agent",
    agent_type: "application",
    version: "1.0.0",
    status: "active",
    last_heartbeat: new Date(Date.now() - 15000).toISOString(),
    capabilities: ["quality_monitoring"],
    host: "localhost",
    port: 8004,
  },
];

const mockMetricsData = [
  { timestamp: "00:00", cost: 1200, latency: 95, gpu: 75, quality: 92 },
  { timestamp: "04:00", cost: 1150, latency: 88, gpu: 78, quality: 94 },
  { timestamp: "08:00", cost: 1300, latency: 92, gpu: 82, quality: 91 },
  { timestamp: "12:00", cost: 1250, latency: 85, gpu: 79, quality: 93 },
  { timestamp: "16:00", cost: 1100, latency: 82, gpu: 76, quality: 95 },
  { timestamp: "20:00", cost: 1050, latency: 80, gpu: 74, quality: 94 },
];

const mockRecommendations: Recommendation[] = [
  {
    id: "rec-001",
    agent_type: "cost",
    type: "spot_migration",
    title: "Migrate to Spot Instances",
    description: "Migrate 3 on-demand instances to spot instances for cost savings",
    estimated_savings: 450,
    risk_level: "low",
    status: "pending",
    created_at: new Date(Date.now() - 3600000).toISOString(),
    updated_at: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: "rec-002",
    agent_type: "performance",
    type: "kv_cache_optimization",
    title: "Optimize KV Cache",
    description: "Adjust KV cache size to improve latency",
    estimated_improvement: 15,
    risk_level: "medium",
    status: "pending",
    created_at: new Date(Date.now() - 7200000).toISOString(),
    updated_at: new Date(Date.now() - 7200000).toISOString(),
  },
];

export default function DashboardPage() {
  const [agents, setAgents] = useState<Agent[]>(mockAgents);
  const [recommendations, setRecommendations] = useState<Recommendation[]>(mockRecommendations);

  const handleApprove = (id: string) => {
    console.log("Approve recommendation:", id);
    // TODO: Call API
  };

  const handleReject = (id: string) => {
    console.log("Reject recommendation:", id);
    // TODO: Call API
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Overview</h1>
        <p className="text-gray-500 mt-1">
          Monitor all agents and their performance metrics
        </p>
      </div>

      {/* Agent Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <AgentStatusCard
          agent={agents[0]}
          metric={{
            value: "$12,450",
            label: "Monthly Cost",
            trend: "down",
            trendValue: "-8.2%",
          }}
        />
        <AgentStatusCard
          agent={agents[1]}
          metric={{
            value: "85ms",
            label: "P95 Latency",
            trend: "down",
            trendValue: "-12%",
          }}
        />
        <AgentStatusCard
          agent={agents[2]}
          metric={{
            value: "78%",
            label: "GPU Utilization",
            trend: "up",
            trendValue: "+5%",
          }}
        />
        <AgentStatusCard
          agent={agents[3]}
          metric={{
            value: "94%",
            label: "Quality Score",
            trend: "up",
            trendValue: "+2%",
          }}
        />
      </div>

      {/* Metrics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <MetricsChart
          title="Cost Trends"
          data={mockMetricsData}
          dataKeys={[{ key: "cost", color: "#0ea5e9", label: "Cost ($)" }]}
          type="area"
        />
        <MetricsChart
          title="Performance Metrics"
          data={mockMetricsData}
          dataKeys={[
            { key: "latency", color: "#8b5cf6", label: "Latency (ms)" },
            { key: "gpu", color: "#10b981", label: "GPU (%)" },
          ]}
          type="line"
        />
      </div>

      {/* Recommendations */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Pending Recommendations
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {recommendations.map((rec) => (
            <RecommendationCard
              key={rec.id}
              recommendation={rec}
              onApprove={handleApprove}
              onReject={handleReject}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
```

---

## Expected Outcomes

After completing this phase:

1. ✅ **UI Components Library**
   - Card, Badge, Button components
   - Reusable and styled

2. ✅ **Dashboard Components**
   - Agent status cards with metrics
   - Charts for visualization
   - Recommendation cards

3. ✅ **Layout Components**
   - Sidebar navigation
   - Header with notifications
   - Dashboard layout

4. ✅ **Interactive Dashboard**
   - Real-time agent monitoring
   - Metrics visualization
   - Recommendation management

5. ✅ **Charts Integration**
   - Recharts library
   - Line, area, bar charts
   - Responsive design

---

## Success Criteria

- [ ] All UI components created
- [ ] Dashboard components functional
- [ ] Charts displaying correctly
- [ ] Navigation working
- [ ] Mock data displaying
- [ ] Responsive design
- [ ] No TypeScript errors
- [ ] No console errors

---

## Next Steps

After PHASE5-5.2 is complete:

**PHASE5-5.3: Portal Tests**
- Playwright E2E tests
- Component tests
- Integration tests

---

**Dashboard components ready for interactive monitoring!** 📊
