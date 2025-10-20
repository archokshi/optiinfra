"""
Seed data for agent state tables (FOUNDATION-0.2b)
Populates: agent_configs, agent_states, agent_capabilities, agent_metrics
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from shared.database.models import (
    Agent, AgentConfig, AgentState, AgentCapability, AgentMetric,
    ConfigType, AgentStatusDetail, MetricType
)
from shared.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def seed_agent_state_tables(session: Session):
    """Seed agent state tables with test data"""
    
    print("🌱 Seeding agent state tables...")
    
    # Get existing test agents from FOUNDATION-0.2a
    agents = session.query(Agent).all()
    if len(agents) < 4:
        raise ValueError("❌ Not enough agents found! Run FOUNDATION-0.2a seed data first.")
    
    cost_agent = agents[1] if len(agents) > 1 else None
    perf_agent = agents[2] if len(agents) > 2 else None
    resource_agent = agents[3] if len(agents) > 3 else None
    app_agent = agents[4] if len(agents) > 4 else None
    
    # ==========================================
    # SEED AGENT CONFIGS
    # ==========================================
    print("  📋 Seeding agent_configs...")
    
    configs = []
    
    if cost_agent:
        configs.extend([
            AgentConfig(
                agent_id=cost_agent.id,
                config_key="cost_threshold_usd",
                config_value="1000",
                config_type=ConfigType.INTEGER,
                description="Minimum monthly cost to trigger optimization"
            ),
            AgentConfig(
                agent_id=cost_agent.id,
                config_key="savings_threshold_percent",
                config_value="15",
                config_type=ConfigType.INTEGER,
                description="Minimum savings percentage to recommend"
            ),
        ])
    
    if perf_agent:
        configs.extend([
            AgentConfig(
                agent_id=perf_agent.id,
                config_key="latency_p95_threshold_ms",
                config_value="500",
                config_type=ConfigType.INTEGER,
                description="P95 latency threshold for alerts"
            ),
            AgentConfig(
                agent_id=perf_agent.id,
                config_key="kv_cache_size_gb",
                config_value="32",
                config_type=ConfigType.INTEGER,
                description="KV cache size in GB"
            ),
        ])
    
    if resource_agent:
        configs.extend([
            AgentConfig(
                agent_id=resource_agent.id,
                config_key="gpu_utilization_target",
                config_value="75",
                config_type=ConfigType.INTEGER,
                description="Target GPU utilization percentage"
            ),
        ])
    
    if app_agent:
        configs.extend([
            AgentConfig(
                agent_id=app_agent.id,
                config_key="quality_score_threshold",
                config_value="0.85",
                config_type=ConfigType.FLOAT,
                description="Minimum quality score (0-1)"
            ),
        ])
    
    session.add_all(configs)
    session.commit()
    print(f"    ✅ Created {len(configs)} agent configs")
    
    # ==========================================
    # SEED AGENT STATES
    # ==========================================
    print("  🔄 Seeding agent_states...")
    
    now = datetime.utcnow()
    states = []
    
    if cost_agent:
        states.append(AgentState(
            agent_id=cost_agent.id,
            current_status=AgentStatusDetail.BUSY,
            active_workflows=["cost_analysis_001"],
            locks={"gpu_cluster_1": True},
            last_activity=now,
            resource_usage={"cpu": 45.2, "memory": 2048}
        ))
    
    if perf_agent:
        states.append(AgentState(
            agent_id=perf_agent.id,
            current_status=AgentStatusDetail.IDLE,
            active_workflows=[],
            locks={},
            last_activity=now,
            resource_usage={"cpu": 12.5, "memory": 512}
        ))
    
    if resource_agent:
        states.append(AgentState(
            agent_id=resource_agent.id,
            current_status=AgentStatusDetail.PROCESSING,
            active_workflows=["gpu_scaling_002"],
            locks={"k8s_cluster": True},
            last_activity=now,
            resource_usage={"cpu": 38.7, "memory": 1024}
        ))
    
    if app_agent:
        states.append(AgentState(
            agent_id=app_agent.id,
            current_status=AgentStatusDetail.IDLE,
            active_workflows=[],
            locks={},
            last_activity=now - timedelta(minutes=5),
            resource_usage={"cpu": 8.3, "memory": 256}
        ))
    
    session.add_all(states)
    session.commit()
    print(f"    ✅ Created {len(states)} agent states")
    
    # ==========================================
    # SEED AGENT CAPABILITIES
    # ==========================================
    print("  💪 Seeding agent_capabilities...")
    
    capabilities = []
    
    if cost_agent:
        capabilities.extend([
            AgentCapability(
                agent_id=cost_agent.id,
                capability_name="gpu_cost_analysis",
                capability_version="1.2.0",
                description="Analyze GPU cluster costs and identify savings",
                config={"supported_providers": ["aws", "gcp", "azure"]},
                enabled=True
            ),
            AgentCapability(
                agent_id=cost_agent.id,
                capability_name="storage_optimization",
                capability_version="1.0.0",
                description="Optimize storage tiering and costs",
                config={"storage_types": ["s3", "ebs", "gcs"]},
                enabled=True
            ),
        ])
    
    if perf_agent:
        capabilities.extend([
            AgentCapability(
                agent_id=perf_agent.id,
                capability_name="kv_cache_tuning",
                capability_version="2.1.0",
                description="Optimize KV cache settings for vLLM/TGI",
                config={"supported_engines": ["vllm", "tgi", "sglang"]},
                enabled=True
            ),
            AgentCapability(
                agent_id=perf_agent.id,
                capability_name="batch_optimization",
                capability_version="1.5.0",
                description="Optimize batch sizes and continuous batching",
                config={"min_batch_size": 4, "max_batch_size": 128},
                enabled=True
            ),
        ])
    
    if resource_agent:
        capabilities.extend([
            AgentCapability(
                agent_id=resource_agent.id,
                capability_name="auto_scaling",
                capability_version="2.0.0",
                description="Auto-scale GPU clusters based on demand",
                config={"scaling_triggers": ["utilization", "queue_depth"]},
                enabled=True
            ),
        ])
    
    if app_agent:
        capabilities.extend([
            AgentCapability(
                agent_id=app_agent.id,
                capability_name="quality_monitoring",
                capability_version="1.4.0",
                description="Monitor LLM output quality in real-time",
                config={"metrics": ["coherence", "relevance", "factuality"]},
                enabled=True
            ),
        ])
    
    session.add_all(capabilities)
    session.commit()
    print(f"    ✅ Created {len(capabilities)} agent capabilities")
    
    # ==========================================
    # SEED AGENT METRICS
    # ==========================================
    print("  📊 Seeding agent_metrics...")
    
    metrics = []
    
    if cost_agent:
        metrics.extend([
            AgentMetric(
                agent_id=cost_agent.id,
                metric_name="total_savings_identified_usd",
                metric_value=125000.00,
                metric_type=MetricType.GAUGE,
                tags={"period": "last_30_days"},
                recorded_at=now
            ),
            AgentMetric(
                agent_id=cost_agent.id,
                metric_name="average_savings_percent",
                metric_value=42.5,
                metric_type=MetricType.GAUGE,
                tags={"period": "last_30_days"},
                recorded_at=now
            ),
        ])
    
    if perf_agent:
        metrics.extend([
            AgentMetric(
                agent_id=perf_agent.id,
                metric_name="latency_improvement_percent",
                metric_value=65.0,
                metric_type=MetricType.GAUGE,
                tags={"metric_type": "performance"},
                recorded_at=now
            ),
            AgentMetric(
                agent_id=perf_agent.id,
                metric_name="throughput_increase_percent",
                metric_value=180.0,
                metric_type=MetricType.GAUGE,
                tags={"metric_type": "performance"},
                recorded_at=now
            ),
        ])
    
    if resource_agent:
        metrics.extend([
            AgentMetric(
                agent_id=resource_agent.id,
                metric_name="average_gpu_utilization_percent",
                metric_value=78.5,
                metric_type=MetricType.GAUGE,
                tags={"resource": "gpu"},
                recorded_at=now
            ),
        ])
    
    if app_agent:
        metrics.extend([
            AgentMetric(
                agent_id=app_agent.id,
                metric_name="quality_score_average",
                metric_value=0.91,
                metric_type=MetricType.GAUGE,
                tags={"samples": "1500"},
                recorded_at=now
            ),
        ])
    
    session.add_all(metrics)
    session.commit()
    print(f"    ✅ Created {len(metrics)} agent metrics")
    
    print("\n✅ Agent state tables seeded successfully!")
    print(f"   📋 Configs: {len(configs)}")
    print(f"   🔄 States: {len(states)}")
    print(f"   💪 Capabilities: {len(capabilities)}")
    print(f"   📊 Metrics: {len(metrics)}")
    
    return {
        "configs": configs,
        "states": states,
        "capabilities": capabilities,
        "metrics": metrics
    }

def main():
    """Main entry point"""
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        seed_agent_state_tables(session)
    except Exception as e:
        print(f"❌ Error seeding agent state tables: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()
