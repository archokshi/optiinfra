"""
Seed data for core schema.
Creates test customers and agents for development.
"""
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from shared.database.models.core import (
    Customer, CustomerPlan, CustomerStatus,
    Agent, AgentType, AgentStatus,
    Event, EventSeverity,
    Recommendation, RecommendationPriority, RecommendationStatus,
)


def seed_core_data(session: Session) -> dict:
    """
    Seed core database with test data.
    
    Args:
        session: SQLAlchemy session
        
    Returns:
        Dict with created objects for reference
    """
    print("Seeding core database...")
    
    # Create test customers
    customer1 = Customer(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        name="Acme Corp",
        email="admin@acme.com",
        api_key="acme_test_key_123456789",
        plan=CustomerPlan.ENTERPRISE,
        status=CustomerStatus.ACTIVE,
        metadata={"industry": "technology", "size": "500-1000"},
    )
    
    customer2 = Customer(
        id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        name="StartupCo",
        email="founder@startup.co",
        api_key="startup_test_key_987654321",
        plan=CustomerPlan.STARTUP,
        status=CustomerStatus.ACTIVE,
        metadata={"industry": "fintech", "size": "10-50"},
    )
    
    customer3 = Customer(
        id=uuid.UUID("00000000-0000-0000-0000-000000000003"),
        name="Demo Customer",
        email="demo@example.com",
        api_key="demo_test_key_111111111",
        plan=CustomerPlan.FREE,
        status=CustomerStatus.ACTIVE,
        metadata={"industry": "demo", "size": "1-10"},
    )
    
    session.add_all([customer1, customer2, customer3])
    print(f"  ✅ Created {3} test customers")
    
    # Create test agents
    orchestrator = Agent(
        id=uuid.UUID("00000000-0000-0000-0000-000000000101"),
        type=AgentType.ORCHESTRATOR,
        name="orchestrator-main",
        version="0.2.0",
        status=AgentStatus.HEALTHY,
        endpoint="http://localhost:8080",
        capabilities=["routing", "coordination", "approval_workflow"],
        metadata={"environment": "development"},
        last_heartbeat=datetime.utcnow(),
    )
    
    cost_agent = Agent(
        id=uuid.UUID("00000000-0000-0000-0000-000000000102"),
        type=AgentType.COST,
        name="cost-agent-1",
        version="0.3.0",
        status=AgentStatus.HEALTHY,
        endpoint="http://localhost:8001",
        capabilities=["spot_migration", "right_sizing", "reserved_instances"],
        metadata={"environment": "development"},
        last_heartbeat=datetime.utcnow(),
    )
    
    perf_agent = Agent(
        id=uuid.UUID("00000000-0000-0000-0000-000000000103"),
        type=AgentType.PERFORMANCE,
        name="performance-agent-1",
        version="0.1.0",
        status=AgentStatus.HEALTHY,
        endpoint="http://localhost:8002",
        capabilities=["kv_cache_tuning", "quantization", "batch_optimization"],
        metadata={"environment": "development"},
        last_heartbeat=datetime.utcnow(),
    )
    
    resource_agent = Agent(
        id=uuid.UUID("00000000-0000-0000-0000-000000000104"),
        type=AgentType.RESOURCE,
        name="resource-agent-1",
        version="0.1.0",
        status=AgentStatus.HEALTHY,
        endpoint="http://localhost:8003",
        capabilities=["gpu_optimization", "auto_scaling", "resource_consolidation"],
        metadata={"environment": "development"},
        last_heartbeat=datetime.utcnow(),
    )
    
    app_agent = Agent(
        id=uuid.UUID("00000000-0000-0000-0000-000000000105"),
        type=AgentType.APPLICATION,
        name="application-agent-1",
        version="0.1.0",
        status=AgentStatus.HEALTHY,
        endpoint="http://localhost:8004",
        capabilities=["quality_monitoring", "regression_detection", "ab_testing"],
        metadata={"environment": "development"},
        last_heartbeat=datetime.utcnow(),
    )
    
    session.add_all([orchestrator, cost_agent, perf_agent, resource_agent, app_agent])
    print(f"  ✅ Created {5} test agents")
    
    # Create test events
    event1 = Event(
        customer_id=customer1.id,
        agent_id=cost_agent.id,
        event_type="optimization_started",
        severity=EventSeverity.INFO,
        data={"optimization_type": "spot_migration", "instances": 5},
    )
    
    event2 = Event(
        customer_id=customer1.id,
        agent_id=cost_agent.id,
        event_type="optimization_completed",
        severity=EventSeverity.INFO,
        data={"optimization_type": "spot_migration", "savings": 2450.00},
    )
    
    event3 = Event(
        customer_id=customer2.id,
        agent_id=perf_agent.id,
        event_type="performance_degradation",
        severity=EventSeverity.WARNING,
        data={"metric": "latency_p95", "threshold": 800, "current": 950},
    )
    
    session.add_all([event1, event2, event3])
    print(f"  ✅ Created {3} test events")
    
    # Create test recommendations
    rec1 = Recommendation(
        customer_id=customer1.id,
        agent_id=cost_agent.id,
        type="spot_migration",
        title="Migrate 5 EC2 instances to spot",
        description="Migrate stable workloads to spot instances for 40% savings",
        estimated_savings=2450.00,
        confidence_score=0.92,
        priority=RecommendationPriority.HIGH,
        status=RecommendationStatus.COMPLETED,
        data={
            "instances": ["i-001", "i-002", "i-003", "i-004", "i-005"],
            "risk_level": "low",
        },
        created_at=datetime.utcnow() - timedelta(days=7),
        approved_at=datetime.utcnow() - timedelta(days=6),
        executed_at=datetime.utcnow() - timedelta(days=5),
    )
    
    rec2 = Recommendation(
        customer_id=customer1.id,
        agent_id=cost_agent.id,
        type="right_sizing",
        title="Downsize 3 over-provisioned instances",
        description="Reduce instance sizes based on utilization patterns",
        estimated_savings=850.00,
        confidence_score=0.88,
        priority=RecommendationPriority.MEDIUM,
        status=RecommendationStatus.PENDING,
        data={
            "instances": ["i-010", "i-011", "i-012"],
            "current_types": ["m5.2xlarge", "m5.2xlarge", "c5.4xlarge"],
            "recommended_types": ["m5.xlarge", "m5.xlarge", "c5.2xlarge"],
        },
    )
    
    rec3 = Recommendation(
        customer_id=customer2.id,
        agent_id=perf_agent.id,
        type="kv_cache_tuning",
        title="Optimize KV cache configuration",
        description="Tune PagedAttention settings for better memory usage",
        estimated_improvement=1.5,
        confidence_score=0.85,
        priority=RecommendationPriority.MEDIUM,
        status=RecommendationStatus.PENDING,
        data={
            "current_cache_size": 4096,
            "recommended_cache_size": 8192,
            "expected_latency_improvement": "30%",
        },
    )
    
    session.add_all([rec1, rec2, rec3])
    print(f"  ✅ Created {3} test recommendations")
    
    # Commit all changes
    session.commit()
    
    print("✅ Core database seeding complete!")
    
    return {
        "customers": [customer1, customer2, customer3],
        "agents": [orchestrator, cost_agent, perf_agent, resource_agent, app_agent],
        "events": [event1, event2, event3],
        "recommendations": [rec1, rec2, rec3],
    }


def clear_core_data(session: Session):
    """
    Clear all core data from database.
    
    Args:
        session: SQLAlchemy session
    """
    print("Clearing core database...")
    
    # Delete in correct order (respect foreign keys)
    from shared.database.models.core import (
        Optimization, Approval, Recommendation, Event, Agent, Customer
    )
    
    session.query(Optimization).delete()
    session.query(Approval).delete()
    session.query(Recommendation).delete()
    session.query(Event).delete()
    session.query(Agent).delete()
    session.query(Customer).delete()
    
    session.commit()
    print("✅ Core database cleared!")
