import type { Agent, Recommendation } from '@/lib/types';

export const mockAgents: Agent[] = [
  {
    agent_id: 'cost-001',
    agent_name: 'Cost Agent',
    agent_type: 'cost',
    version: '1.0.0',
    status: 'active',
    last_heartbeat: new Date().toISOString(),
    capabilities: ['cost_tracking'],
    host: 'localhost',
    port: 8001,
  },
  {
    agent_id: 'perf-001',
    agent_name: 'Performance Agent',
    agent_type: 'performance',
    version: '1.0.0',
    status: 'active',
    last_heartbeat: new Date().toISOString(),
    capabilities: ['performance_monitoring'],
    host: 'localhost',
    port: 8002,
  },
];

export const mockRecommendations: Recommendation[] = [
  {
    id: 'rec-001',
    agent_type: 'cost',
    type: 'spot_migration',
    title: 'Migrate to Spot Instances',
    description: 'Test recommendation',
    estimated_savings: 450,
    risk_level: 'low',
    status: 'pending',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];
