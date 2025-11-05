# PHASE5-5.1 PART1: Next.js Setup - Code Implementation Plan

**Phase**: PHASE5-5.1  
**Component**: Portal & Production  
**Objective**: Set up Next.js 14 App Router with TailwindCSS and TypeScript  
**Estimated Time**: 25+20m = 45 minutes total  
**Priority**: HIGH  
**Dependencies**: None (foundation phase)

---

## Overview

This phase creates the foundational Next.js 14 application for the OptiInfra customer portal. The portal provides a unified dashboard for monitoring all agents (Cost, Performance, Resource, Application), viewing recommendations, and managing approvals.

---

## Portal Purpose

### **Primary Responsibilities**
1. **Unified Dashboard** - Overview of all agents and their status
2. **Agent Monitoring** - Real-time metrics from all 4 agents
3. **Recommendations** - View and approve/reject optimization recommendations
4. **Execution History** - Track all optimizations and their outcomes
5. **Real-time Updates** - WebSocket integration for live data

### **Key Features**
- Modern Next.js 14 App Router
- TypeScript for type safety
- TailwindCSS for styling
- Responsive design
- Dark mode support
- Real-time data updates

---

## Implementation Plan

### Step 1: Initialize Next.js Project (5 minutes)

```bash
# Navigate to project root
cd C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra

# Create Next.js app with TypeScript and TailwindCSS
npx create-next-app@latest portal --typescript --tailwind --app --no-src-dir --import-alias "@/*"

# Navigate to portal directory
cd portal
```

**Configuration during setup:**
- ✅ TypeScript: Yes
- ✅ ESLint: Yes
- ✅ Tailwind CSS: Yes
- ✅ App Router: Yes
- ✅ Import alias: Yes (@/*)
- ❌ src/ directory: No
- ❌ Turbopack: No (use default Webpack)

---

### Step 2: Project Structure (3 minutes)

```bash
portal/
├── app/
│   ├── (dashboard)/          # Dashboard layout group
│   │   ├── layout.tsx        # Dashboard layout
│   │   ├── page.tsx          # Overview page
│   │   ├── cost/             # Cost agent dashboard
│   │   │   └── page.tsx
│   │   ├── performance/      # Performance agent dashboard
│   │   │   └── page.tsx
│   │   ├── resource/         # Resource agent dashboard
│   │   │   └── page.tsx
│   │   └── application/      # Application agent dashboard
│   │       └── page.tsx
│   ├── api/                  # API routes
│   │   └── health/
│   │       └── route.ts
│   ├── layout.tsx            # Root layout
│   ├── page.tsx              # Landing page
│   └── globals.css           # Global styles
├── components/
│   ├── ui/                   # Reusable UI components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   └── badge.tsx
│   ├── layout/               # Layout components
│   │   ├── header.tsx
│   │   ├── sidebar.tsx
│   │   └── footer.tsx
│   └── dashboard/            # Dashboard-specific components
│       ├── agent-card.tsx
│       ├── metrics-chart.tsx
│       └── status-indicator.tsx
├── lib/
│   ├── api.ts                # API client
│   ├── types.ts              # TypeScript types
│   └── utils.ts              # Utility functions
├── public/
│   └── logo.svg              # OptiInfra logo
├── .env.local                # Environment variables
├── .env.example              # Environment template
├── next.config.js            # Next.js configuration
├── tailwind.config.ts        # Tailwind configuration
├── tsconfig.json             # TypeScript configuration
├── package.json              # Dependencies
└── README.md                 # Documentation
```

---

### Step 3: Configure Environment Variables (.env.example) (2 minutes)

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_COST_AGENT_URL=http://localhost:8001
NEXT_PUBLIC_PERFORMANCE_AGENT_URL=http://localhost:8002
NEXT_PUBLIC_RESOURCE_AGENT_URL=http://localhost:8003
NEXT_PUBLIC_APPLICATION_AGENT_URL=http://localhost:8004

# WebSocket Configuration
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# Environment
NEXT_PUBLIC_ENVIRONMENT=development

# Feature Flags
NEXT_PUBLIC_ENABLE_DARK_MODE=true
NEXT_PUBLIC_ENABLE_REALTIME=true
```

---

### Step 4: Configure Tailwind (tailwind.config.ts) (3 minutes)

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#f0f9ff",
          100: "#e0f2fe",
          200: "#bae6fd",
          300: "#7dd3fc",
          400: "#38bdf8",
          500: "#0ea5e9",
          600: "#0284c7",
          700: "#0369a1",
          800: "#075985",
          900: "#0c4a6e",
          950: "#082f49",
        },
        success: {
          50: "#f0fdf4",
          500: "#22c55e",
          700: "#15803d",
        },
        warning: {
          50: "#fffbeb",
          500: "#f59e0b",
          700: "#b45309",
        },
        error: {
          50: "#fef2f2",
          500: "#ef4444",
          700: "#b91c1c",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-in-out",
        "slide-in": "slideIn 0.3s ease-out",
        pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideIn: {
          "0%": { transform: "translateY(-10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
```

---

### Step 5: Create TypeScript Types (lib/types.ts) (5 minutes)

```typescript
/**
 * OptiInfra Portal - Type Definitions
 * 
 * Shared TypeScript types for the portal application.
 */

// Agent Types
export type AgentType = "cost" | "performance" | "resource" | "application";

export type AgentStatus = "active" | "inactive" | "degraded" | "error";

export interface Agent {
  agent_id: string;
  agent_name: string;
  agent_type: AgentType;
  version: string;
  status: AgentStatus;
  last_heartbeat: string;
  capabilities: string[];
  host: string;
  port: number;
}

// Metrics Types
export interface Metric {
  name: string;
  value: number;
  unit: string;
  timestamp: string;
  trend?: "up" | "down" | "stable";
}

export interface AgentMetrics {
  agent_id: string;
  agent_type: AgentType;
  metrics: Metric[];
  timestamp: string;
}

// Cost Agent Types
export interface CostMetrics {
  total_cost: number;
  daily_cost: number;
  monthly_cost: number;
  cost_trend: number; // percentage change
  savings_potential: number;
  currency: string;
}

// Performance Agent Types
export interface PerformanceMetrics {
  latency_p50: number;
  latency_p95: number;
  latency_p99: number;
  throughput: number;
  requests_per_second: number;
  error_rate: number;
}

// Resource Agent Types
export interface ResourceMetrics {
  gpu_utilization: number;
  cpu_utilization: number;
  memory_utilization: number;
  gpu_memory_used: number;
  gpu_memory_total: number;
}

// Application Agent Types
export interface QualityMetrics {
  quality_score: number;
  relevance_score: number;
  coherence_score: number;
  hallucination_rate: number;
  toxicity_score: number;
}

// Recommendation Types
export type RecommendationType = 
  | "spot_migration"
  | "reserved_instance"
  | "right_sizing"
  | "kv_cache_optimization"
  | "quantization"
  | "batch_optimization";

export type RecommendationStatus = 
  | "pending"
  | "approved"
  | "rejected"
  | "executing"
  | "completed"
  | "failed";

export interface Recommendation {
  id: string;
  agent_type: AgentType;
  type: RecommendationType;
  title: string;
  description: string;
  estimated_savings?: number;
  estimated_improvement?: number;
  risk_level: "low" | "medium" | "high";
  status: RecommendationStatus;
  created_at: string;
  updated_at: string;
}

// Execution History Types
export interface Execution {
  id: string;
  recommendation_id: string;
  agent_type: AgentType;
  type: RecommendationType;
  status: "success" | "failed" | "in_progress";
  started_at: string;
  completed_at?: string;
  actual_savings?: number;
  actual_improvement?: number;
  error_message?: string;
}

// Dashboard Types
export interface DashboardData {
  agents: Agent[];
  metrics: {
    cost: CostMetrics;
    performance: PerformanceMetrics;
    resource: ResourceMetrics;
    quality: QualityMetrics;
  };
  recommendations: Recommendation[];
  recent_executions: Execution[];
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: string;
}

// Health Check Types
export interface HealthCheck {
  status: "healthy" | "degraded" | "unhealthy";
  timestamp: string;
  components: {
    [key: string]: "healthy" | "degraded" | "unhealthy";
  };
}
```

---

### Step 6: Create API Client (lib/api.ts) (5 minutes)

```typescript
/**
 * OptiInfra Portal - API Client
 * 
 * Centralized API client for communicating with backend services.
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

  // Health Check
  async getHealth(): Promise<ApiResponse<HealthCheck>> {
    return this.request<HealthCheck>("/api/v1/health");
  }

  // Agents
  async getAgents(): Promise<ApiResponse<Agent[]>> {
    return this.request<Agent[]>("/api/v1/agents");
  }

  async getAgent(agentId: string): Promise<ApiResponse<Agent>> {
    return this.request<Agent>(`/api/v1/agents/${agentId}`);
  }

  // Dashboard
  async getDashboardData(): Promise<ApiResponse<DashboardData>> {
    return this.request<DashboardData>("/api/v1/dashboard");
  }

  // Recommendations
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

  // Execution History
  async getExecutions(): Promise<ApiResponse<Execution[]>> {
    return this.request<Execution[]>("/api/v1/executions");
  }

  async getExecution(id: string): Promise<ApiResponse<Execution>> {
    return this.request<Execution>(`/api/v1/executions/${id}`);
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export class for testing
export { ApiClient };
```

---

### Step 7: Create Utility Functions (lib/utils.ts) (3 minutes)

```typescript
/**
 * OptiInfra Portal - Utility Functions
 * 
 * Shared utility functions for the portal application.
 */

import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind CSS classes with proper precedence
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format currency values
 */
export function formatCurrency(value: number, currency: string = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

/**
 * Format percentage values
 */
export function formatPercentage(value: number, decimals: number = 1): string {
  return `${value.toFixed(decimals)}%`;
}

/**
 * Format large numbers with abbreviations (K, M, B)
 */
export function formatNumber(value: number): string {
  if (value >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(1)}B`;
  }
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)}M`;
  }
  if (value >= 1_000) {
    return `${(value / 1_000).toFixed(1)}K`;
  }
  return value.toString();
}

/**
 * Format timestamps to relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(timestamp: string): string {
  const now = new Date();
  const date = new Date(timestamp);
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`;
  
  return date.toLocaleDateString();
}

/**
 * Format timestamps to readable date/time
 */
export function formatDateTime(timestamp: string): string {
  return new Date(timestamp).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Get status color for badges/indicators
 */
export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    active: "text-green-600 bg-green-50",
    healthy: "text-green-600 bg-green-50",
    success: "text-green-600 bg-green-50",
    inactive: "text-gray-600 bg-gray-50",
    degraded: "text-yellow-600 bg-yellow-50",
    warning: "text-yellow-600 bg-yellow-50",
    error: "text-red-600 bg-red-50",
    failed: "text-red-600 bg-red-50",
    unhealthy: "text-red-600 bg-red-50",
    pending: "text-blue-600 bg-blue-50",
    executing: "text-blue-600 bg-blue-50",
    in_progress: "text-blue-600 bg-blue-50",
  };
  
  return colors[status.toLowerCase()] || "text-gray-600 bg-gray-50";
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength)}...`;
}

/**
 * Debounce function for search/input handlers
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}
```

---

### Step 8: Update package.json Dependencies (2 minutes)

```json
{
  "name": "optiinfra-portal",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "next": "14.0.3",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.1.0"
  },
  "devDependencies": {
    "@types/node": "^20.10.0",
    "@types/react": "^18.2.42",
    "@types/react-dom": "^18.2.17",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.55.0",
    "eslint-config-next": "14.0.3",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.3.6",
    "typescript": "^5.3.2"
  }
}
```

---

### Step 9: Create Root Layout (app/layout.tsx) (5 minutes)

```typescript
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "OptiInfra - AI-Powered LLM Infrastructure Optimization",
  description: "Reduce costs by 50%, improve performance 3x, and ensure quality with intelligent multi-agent optimization",
  keywords: ["LLM", "infrastructure", "optimization", "AI", "cost reduction", "performance"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-gray-50 antialiased">
        {children}
      </body>
    </html>
  );
}
```

---

### Step 10: Create Landing Page (app/page.tsx) (5 minutes)

```typescript
import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center space-y-8">
        <h1 className="text-6xl font-bold text-gray-900">
          Opti<span className="text-primary-600">Infra</span>
        </h1>
        
        <p className="text-xl text-gray-600 max-w-2xl">
          AI-Powered LLM Infrastructure Optimization
        </p>
        
        <div className="flex gap-4 justify-center">
          <Link
            href="/dashboard"
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            Go to Dashboard
          </Link>
          
          <Link
            href="/api/health"
            className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            API Health
          </Link>
        </div>
        
        <div className="grid grid-cols-3 gap-8 mt-16 max-w-3xl">
          <div className="text-center">
            <div className="text-4xl font-bold text-primary-600">50%</div>
            <div className="text-sm text-gray-600 mt-2">Cost Reduction</div>
          </div>
          
          <div className="text-center">
            <div className="text-4xl font-bold text-primary-600">3x</div>
            <div className="text-sm text-gray-600 mt-2">Performance Boost</div>
          </div>
          
          <div className="text-center">
            <div className="text-4xl font-bold text-primary-600">4</div>
            <div className="text-sm text-gray-600 mt-2">AI Agents</div>
          </div>
        </div>
      </div>
    </main>
  );
}
```

---

### Step 11: Create Health API Route (app/api/health/route.ts) (3 minutes)

```typescript
import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    status: "healthy",
    timestamp: new Date().toISOString(),
    service: "optiinfra-portal",
    version: "1.0.0",
  });
}
```

---

### Step 12: Update Global Styles (app/globals.css) (2 minutes)

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --font-inter: 'Inter', system-ui, sans-serif;
  }
  
  * {
    @apply border-border;
  }
  
  body {
    @apply bg-background text-foreground;
  }
}

@layer utilities {
  .text-balance {
    text-wrap: balance;
  }
}
```

---

### Step 13: Create README.md (2 minutes)

```markdown
# OptiInfra Portal

Modern Next.js 14 dashboard for monitoring and managing OptiInfra's multi-agent LLM optimization platform.

## Features

- 🎨 Modern UI with Next.js 14 App Router
- 🎯 TypeScript for type safety
- 🎨 TailwindCSS for styling
- 📊 Real-time agent monitoring
- 🔄 WebSocket integration
- 🌙 Dark mode support
- 📱 Responsive design

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
portal/
├── app/              # Next.js App Router pages
├── components/       # React components
├── lib/              # Utilities and API client
└── public/           # Static assets
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## Environment Variables

See `.env.example` for required environment variables.

## Tech Stack

- **Framework**: Next.js 14
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **State**: React Hooks
- **API**: Fetch API

## License

Proprietary - OptiInfra
```

---

## Expected Outcomes

After completing this phase:

1. ✅ **Next.js 14 Application**
   - App Router configured
   - TypeScript enabled
   - TailwindCSS integrated

2. ✅ **Project Structure**
   - Clean folder organization
   - Type definitions
   - API client ready

3. ✅ **Landing Page**
   - Professional homepage
   - Navigation to dashboard
   - Health check endpoint

4. ✅ **Development Environment**
   - Hot reload working
   - TypeScript checking
   - ESLint configured

5. ✅ **Foundation Ready**
   - Ready for dashboard components
   - API integration prepared
   - Styling system in place

---

## Success Criteria

- [ ] Next.js app starts successfully on port 3000
- [ ] Landing page displays correctly
- [ ] TypeScript compilation succeeds
- [ ] TailwindCSS styles applied
- [ ] API health endpoint returns 200 OK
- [ ] No console errors
- [ ] Hot reload working

---

## Next Steps

After PHASE5-5.1 is complete:

**PHASE5-5.2: Dashboard Components**
- Agent status cards
- Metrics charts
- Real-time updates
- Dashboard layout

---

**Next.js foundation ready for dashboard implementation!** 🚀
