"""
Seed data for resource schema tables (FOUNDATION-0.2d)
Populates: resource_metrics, scaling_events
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from shared.database.models import (
    Agent, Customer, WorkflowExecution,
    ResourceMetric, ScalingEvent,
    ResourceType, ScalingEventType, WorkflowType, WorkflowStatus, AgentType
)
from shared.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def seed_resource_schema_tables(db: Session):
    """Seed resource schema tables with realistic test data"""
    
    print("🌱 Seeding resource schema tables...")
    
    # Get existing test data
    resource_agent = db.query(Agent).filter_by(type=AgentType.RESOURCE).first()
    cost_agent = db.query(Agent).filter_by(type=AgentType.COST).first()
    
    customers = db.query(Customer).all()
    customer1 = customers[0] if len(customers) > 0 else None
    customer2 = customers[1] if len(customers) > 1 else None
    
    if not all([resource_agent, cost_agent, customer1, customer2]):
        raise ValueError("❌ Required agents/customers not found! Run previous seed scripts first.")
    
    now = datetime.now()
    
    # ==========================================
    # SEED RESOURCE METRICS
    # ==========================================
    print("  📊 Seeding resource_metrics...")
    
    # Instance IDs for testing
    instances = [
        "i-0abc123def456",  # GPU instance 1
        "i-0abc123def457",  # GPU instance 2
        "i-0abc123def458",  # GPU instance 3
        "i-0xyz789ghi012",  # CPU instance
    ]
    
    metrics = []
    
    # GPU Metrics - Instance 1 (High utilization)
    for i in range(12):  # 12 hours of data
        timestamp = now - timedelta(hours=11-i)
        
        # GPU utilization trending up
        gpu_util = 45.0 + (i * 3.5)  # 45% -> 83.5%
        metrics.append(
            ResourceMetric(
                agent_id=resource_agent.id,
                customer_id=customer1.id,
                instance_id=instances[0],
                resource_type=ResourceType.GPU,
                metric_name="utilization",
                metric_value=gpu_util,
                unit="percent",
                timestamp=timestamp,
                resource_metadata={
                    "gpu_model": "NVIDIA H100",
                    "gpu_memory_total_gb": 80,
                    "gpu_memory_used_gb": round(80 * (gpu_util / 100), 2)
                }
            )
        )
        
        # GPU temperature
        temp = 65.0 + (i * 2.0)  # Rising temperature
        metrics.append(
            ResourceMetric(
                agent_id=resource_agent.id,
                customer_id=customer1.id,
                instance_id=instances[0],
                resource_type=ResourceType.GPU,
                metric_name="temperature",
                metric_value=temp,
                unit="celsius",
                timestamp=timestamp,
                resource_metadata={"gpu_model": "NVIDIA H100"}
            )
        )
    
    # GPU Metrics - Instance 2 (Medium utilization)
    for i in range(12):
        timestamp = now - timedelta(hours=11-i)
        gpu_util = 55.0 + (i * 1.5)  # 55% -> 71.5%
        
        metrics.append(
            ResourceMetric(
                agent_id=resource_agent.id,
                customer_id=customer1.id,
                instance_id=instances[1],
                resource_type=ResourceType.GPU,
                metric_name="utilization",
                metric_value=gpu_util,
                unit="percent",
                timestamp=timestamp,
                resource_metadata={
                    "gpu_model": "NVIDIA A100",
                    "gpu_memory_total_gb": 40,
                    "gpu_memory_used_gb": round(40 * (gpu_util / 100), 2)
                }
            )
        )
    
    # GPU Metrics - Instance 3 (Low utilization - candidate for consolidation)
    for i in range(12):
        timestamp = now - timedelta(hours=11-i)
        gpu_util = 20.0 + (i * 0.5)  # 20% -> 25.5%
        
        metrics.append(
            ResourceMetric(
                agent_id=resource_agent.id,
                customer_id=customer1.id,
                instance_id=instances[2],
                resource_type=ResourceType.GPU,
                metric_name="utilization",
                metric_value=gpu_util,
                unit="percent",
                timestamp=timestamp,
                resource_metadata={
                    "gpu_model": "NVIDIA A100",
                    "gpu_memory_total_gb": 40,
                    "gpu_memory_used_gb": round(40 * (gpu_util / 100), 2)
                }
            )
        )
    
    # CPU Metrics - Instance 4
    for i in range(12):
        timestamp = now - timedelta(hours=11-i)
        cpu_util = 65.0 + (i * 2.0)  # 65% -> 87%
        
        metrics.append(
            ResourceMetric(
                agent_id=resource_agent.id,
                customer_id=customer1.id,
                instance_id=instances[3],
                resource_type=ResourceType.CPU,
                metric_name="utilization",
                metric_value=cpu_util,
                unit="percent",
                timestamp=timestamp,
                resource_metadata={
                    "cpu_cores": 32,
                    "instance_type": "c6i.8xlarge"
                }
            )
        )
    
    # Memory Metrics - Instance 4
    for i in range(12):
        timestamp = now - timedelta(hours=11-i)
        memory_used_gb = 50.0 + (i * 3.0)  # 50GB -> 83GB
        
        metrics.append(
            ResourceMetric(
                agent_id=resource_agent.id,
                customer_id=customer1.id,
                instance_id=instances[3],
                resource_type=ResourceType.MEMORY,
                metric_name="used",
                metric_value=memory_used_gb,
                unit="GB",
                timestamp=timestamp,
                resource_metadata={
                    "memory_total_gb": 128,
                    "utilization_percent": round((memory_used_gb / 128) * 100, 2)
                }
            )
        )
    
    # Disk I/O Metrics - Instance 1
    for i in range(6):  # 6 hours of data
        timestamp = now - timedelta(hours=5-i)
        
        metrics.append(
            ResourceMetric(
                agent_id=resource_agent.id,
                customer_id=customer1.id,
                instance_id=instances[0],
                resource_type=ResourceType.DISK,
                metric_name="read_iops",
                metric_value=1500.0 + (i * 200),
                unit="iops",
                timestamp=timestamp,
                resource_metadata={"disk_type": "nvme"}
            )
        )
        
        metrics.append(
            ResourceMetric(
                agent_id=resource_agent.id,
                customer_id=customer1.id,
                instance_id=instances[0],
                resource_type=ResourceType.DISK,
                metric_name="write_iops",
                metric_value=800.0 + (i * 100),
                unit="iops",
                timestamp=timestamp,
                resource_metadata={"disk_type": "nvme"}
            )
        )
    
    # Network Metrics - Instance 1
    for i in range(6):
        timestamp = now - timedelta(hours=5-i)
        
        metrics.append(
            ResourceMetric(
                agent_id=resource_agent.id,
                customer_id=customer1.id,
                instance_id=instances[0],
                resource_type=ResourceType.NETWORK,
                metric_name="bandwidth_in",
                metric_value=2500.0 + (i * 300),
                unit="Mbps",
                timestamp=timestamp,
                resource_metadata={"network_interface": "eth0"}
            )
        )
        
        metrics.append(
            ResourceMetric(
                agent_id=resource_agent.id,
                customer_id=customer1.id,
                instance_id=instances[0],
                resource_type=ResourceType.NETWORK,
                metric_name="bandwidth_out",
                metric_value=1800.0 + (i * 200),
                unit="Mbps",
                timestamp=timestamp,
                resource_metadata={"network_interface": "eth0"}
            )
        )
    
    # Add metrics for customer2
    for i in range(6):
        timestamp = now - timedelta(hours=5-i)
        gpu_util = 70.0 + (i * 2.0)
        
        metrics.append(
            ResourceMetric(
                agent_id=resource_agent.id,
                customer_id=customer2.id,
                instance_id="i-techstart001",
                resource_type=ResourceType.GPU,
                metric_name="utilization",
                metric_value=gpu_util,
                unit="percent",
                timestamp=timestamp,
                resource_metadata={
                    "gpu_model": "NVIDIA A100",
                    "gpu_memory_total_gb": 40
                }
            )
        )
    
    db.add_all(metrics)
    db.commit()
    print(f"    ✅ Created {len(metrics)} resource metrics")
    
    # ==========================================
    # SEED SCALING EVENTS
    # ==========================================
    print("  🔄 Seeding scaling_events...")
    
    # Create a workflow for one of the scaling events
    scaling_workflow = WorkflowExecution(
        agent_id=resource_agent.id,
        customer_id=customer1.id,
        workflow_type=WorkflowType.SCALING_DECISION,
        status=WorkflowStatus.COMPLETED,
        started_at=now - timedelta(hours=6),
        completed_at=now - timedelta(hours=5, minutes=45),
        input_data={
            "trigger": "high_gpu_utilization",
            "threshold": 85.0,
            "current_avg_util": 88.2
        },
        output_data={
            "decision": "scale_up",
            "instances_added": 2,
            "new_total_instances": 5
        },
        workflow_metadata={
            "triggered_by": "auto_scaler"
        }
    )
    db.add(scaling_workflow)
    db.commit()
    
    events = []
    
    # Event 1: Successful scale-up (linked to workflow)
    events.append(
        ScalingEvent(
            agent_id=resource_agent.id,
            customer_id=customer1.id,
            workflow_execution_id=scaling_workflow.id,
            event_type=ScalingEventType.SCALE_UP,
            trigger_reason="GPU utilization exceeded 85% threshold for 15 minutes",
            before_state={
                "instance_count": 3,
                "instances": [instances[0], instances[1], instances[2]],
                "avg_gpu_utilization": 88.2,
                "total_gpu_count": 3,
                "cost_per_hour": 30.0
            },
            after_state={
                "instance_count": 5,
                "instances": [instances[0], instances[1], instances[2], "i-new001", "i-new002"],
                "avg_gpu_utilization": 62.5,
                "total_gpu_count": 5,
                "cost_per_hour": 50.0
            },
            success=True,
            executed_at=now - timedelta(hours=6),
            completed_at=now - timedelta(hours=5, minutes=45),
            scaling_metadata={
                "scaling_policy": "predictive",
                "predicted_duration_hours": 8,
                "estimated_cost_impact": "+$160",
                "performance_improvement": "Expected 30% latency reduction"
            }
        )
    )
    
    # Event 2: Successful scale-down (consolidation)
    events.append(
        ScalingEvent(
            agent_id=resource_agent.id,
            customer_id=customer1.id,
            workflow_execution_id=None,
            event_type=ScalingEventType.SCALE_DOWN,
            trigger_reason="Low GPU utilization detected: instance i-0abc123def458 at 22% for 2 hours",
            before_state={
                "instance_count": 5,
                "avg_gpu_utilization": 55.0,
                "underutilized_instances": [instances[2]],
                "cost_per_hour": 50.0
            },
            after_state={
                "instance_count": 4,
                "avg_gpu_utilization": 64.0,
                "workloads_migrated": 3,
                "cost_per_hour": 40.0
            },
            success=True,
            executed_at=now - timedelta(hours=4),
            completed_at=now - timedelta(hours=3, minutes=50),
            scaling_metadata={
                "savings_per_hour": 10.0,
                "annual_savings": 87600,
                "migration_duration_minutes": 10
            }
        )
    )
    
    # Event 3: Auto-scale triggered (but cancelled due to cost concerns)
    events.append(
        ScalingEvent(
            agent_id=resource_agent.id,
            customer_id=customer1.id,
            workflow_execution_id=None,
            event_type=ScalingEventType.SCALE_CANCELLED,
            trigger_reason="Auto-scale triggered: GPU utilization at 82%, but within budget constraints",
            before_state={
                "instance_count": 4,
                "avg_gpu_utilization": 82.0,
                "projected_util_in_1h": 85.0
            },
            after_state={
                "instance_count": 4,
                "decision": "cancelled",
                "reason": "Cost budget limit reached for the month"
            },
            success=True,  # Successfully cancelled
            executed_at=now - timedelta(hours=2),
            completed_at=now - timedelta(hours=2, minutes=1),
            scaling_metadata={
                "budget_limit_monthly": 100000,
                "current_spend": 98500,
                "projected_cost_if_scaled": 102000,
                "alternative_action": "Optimize existing instances instead"
            }
        )
    )
    
    # Event 4: Failed scale-up (capacity issue)
    events.append(
        ScalingEvent(
            agent_id=resource_agent.id,
            customer_id=customer1.id,
            workflow_execution_id=None,
            event_type=ScalingEventType.SCALE_UP,
            trigger_reason="Manual scale requested by user",
            before_state={
                "instance_count": 4,
                "target_instance_count": 6
            },
            after_state={
                "instance_count": 4,
                "instances_added": 0
            },
            success=False,
            error_details={
                "error_type": "InsufficientCapacity",
                "error_message": "No available H100 capacity in us-west-2a",
                "attempted_zones": ["us-west-2a", "us-west-2b"],
                "suggestion": "Try different instance type or region"
            },
            executed_at=now - timedelta(hours=1, minutes=30),
            completed_at=now - timedelta(hours=1, minutes=28),
            scaling_metadata={
                "requested_instance_type": "p5.48xlarge",
                "fallback_attempted": False
            }
        )
    )
    
    db.add_all(events)
    db.commit()
    print(f"    ✅ Created {len(events)} scaling events")
    
    print("\n✅ Resource schema tables seeded successfully!")
    print(f"   📊 Metrics: {len(metrics)} (GPU, CPU, Memory, Disk, Network)")
    print(f"   🔄 Events: {len(events)} (scale-up, scale-down, auto-scale, cancelled, failed)")
    
    return {
        "metrics": metrics,
        "events": events,
        "workflow": scaling_workflow
    }

def main():
    """Main entry point"""
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        seed_resource_schema_tables(session)
    except Exception as e:
        print(f"❌ Error seeding resource schema: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()
