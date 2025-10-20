"""
Seed data for workflow history tables (FOUNDATION-0.2c)
Populates: workflow_executions, workflow_steps, workflow_artifacts
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from shared.database.models import (
    Agent, Customer, WorkflowExecution, WorkflowStep, WorkflowArtifact,
    WorkflowType, WorkflowStatus, StepStatus, ArtifactType, AgentType
)
from shared.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def seed_workflow_history_tables(db: Session):
    """Seed workflow history tables with realistic test data"""
    
    print("🌱 Seeding workflow history tables...")
    
    # Get existing test data
    cost_agent = db.query(Agent).filter_by(type=AgentType.COST).first()
    perf_agent = db.query(Agent).filter_by(type=AgentType.PERFORMANCE).first()
    resource_agent = db.query(Agent).filter_by(type=AgentType.RESOURCE).first()
    app_agent = db.query(Agent).filter_by(type=AgentType.APPLICATION).first()
    
    customers = db.query(Customer).all()
    customer1 = customers[0] if len(customers) > 0 else None
    customer2 = customers[1] if len(customers) > 1 else None
    
    if not all([cost_agent, perf_agent, resource_agent, app_agent, customer1, customer2]):
        raise ValueError("❌ Required agents/customers not found! Run previous seed scripts first.")
    
    now = datetime.now()
    
    # ==========================================
    # SCENARIO 1: Completed Cost Analysis
    # ==========================================
    print("  💰 Creating completed cost analysis workflow...")
    
    workflow1 = WorkflowExecution(
        agent_id=cost_agent.id,
        customer_id=customer1.id,
        workflow_type=WorkflowType.COST_ANALYSIS,
        status=WorkflowStatus.COMPLETED,
        started_at=now - timedelta(hours=2),
        completed_at=now - timedelta(hours=1, minutes=45),
        input_data={
            "analysis_period": "last_30_days",
            "include_projections": True,
            "focus_areas": ["gpu", "storage", "network"]
        },
        output_data={
            "total_cost": 120000,
            "potential_savings": 60000,
            "savings_percentage": 50,
            "recommendations_generated": 8,
            "confidence_score": 0.92
        },
        workflow_metadata={
            "triggered_by": "scheduled",
            "priority": "normal",
            "analyst_notes": "High confidence savings identified"
        }
    )
    db.add(workflow1)
    db.flush()
    
    # Steps for workflow1
    steps1 = [
        WorkflowStep(
            workflow_execution_id=workflow1.id,
            step_name="collect_metrics",
            step_order=1,
            status=StepStatus.COMPLETED,
            started_at=now - timedelta(hours=2),
            completed_at=now - timedelta(hours=1, minutes=58),
            input_data={"sources": ["prometheus", "cloudwatch", "billing_api"]},
            output_data={"metrics_collected": 1247, "data_points": 89650},
            retry_count=0
        ),
        WorkflowStep(
            workflow_execution_id=workflow1.id,
            step_name="analyze_gpu_usage",
            step_order=2,
            status=StepStatus.COMPLETED,
            started_at=now - timedelta(hours=1, minutes=58),
            completed_at=now - timedelta(hours=1, minutes=55),
            input_data={"gpu_count": 12, "analysis_depth": "detailed"},
            output_data={
                "avg_utilization": 35.2,
                "idle_gpus": 4,
                "potential_savings": 35000
            },
            retry_count=0
        ),
        WorkflowStep(
            workflow_execution_id=workflow1.id,
            step_name="analyze_storage",
            step_order=3,
            status=StepStatus.COMPLETED,
            started_at=now - timedelta(hours=1, minutes=55),
            completed_at=now - timedelta(hours=1, minutes=52),
            input_data={"storage_types": ["s3", "ebs"]},
            output_data={
                "total_storage_tb": 45.2,
                "cold_data_percentage": 62,
                "potential_savings": 15000
            },
            retry_count=0
        ),
        WorkflowStep(
            workflow_execution_id=workflow1.id,
            step_name="generate_recommendations",
            step_order=4,
            status=StepStatus.COMPLETED,
            started_at=now - timedelta(hours=1, minutes=52),
            completed_at=now - timedelta(hours=1, minutes=48),
            input_data={"min_confidence": 0.8},
            output_data={
                "recommendations_count": 8,
                "high_priority": 3,
                "medium_priority": 5
            },
            retry_count=0
        ),
        WorkflowStep(
            workflow_execution_id=workflow1.id,
            step_name="generate_report",
            step_order=5,
            status=StepStatus.COMPLETED,
            started_at=now - timedelta(hours=1, minutes=48),
            completed_at=now - timedelta(hours=1, minutes=45),
            input_data={"format": "pdf", "include_charts": True},
            output_data={"report_path": "s3://reports/cost_analysis_20251019.pdf"},
            retry_count=0
        ),
    ]
    db.add_all(steps1)
    db.flush()
    
    # Artifacts for workflow1
    artifacts1 = [
        WorkflowArtifact(
            workflow_execution_id=workflow1.id,
            workflow_step_id=steps1[4].id,
            artifact_type=ArtifactType.REPORT,
            artifact_name="Cost Analysis Report - Customer 1",
            artifact_path="s3://optiinfra-reports/customer1/cost_analysis_20251019.pdf",
            artifact_size_bytes=2458624,
            content_type="application/pdf",
            artifact_metadata={
                "pages": 24,
                "charts": 12,
                "tables": 8
            }
        ),
        WorkflowArtifact(
            workflow_execution_id=workflow1.id,
            workflow_step_id=steps1[3].id,
            artifact_type=ArtifactType.RECOMMENDATION,
            artifact_name="Recommendations JSON",
            artifact_path="s3://optiinfra-data/customer1/recommendations_20251019.json",
            artifact_size_bytes=45821,
            content_type="application/json",
            artifact_metadata={"recommendations_count": 8}
        ),
        WorkflowArtifact(
            workflow_execution_id=workflow1.id,
            workflow_step_id=steps1[1].id,
            artifact_type=ArtifactType.CHART,
            artifact_name="GPU Utilization Chart",
            artifact_path="s3://optiinfra-charts/customer1/gpu_util_20251019.png",
            artifact_size_bytes=156789,
            content_type="image/png",
            artifact_metadata={"chart_type": "timeseries", "duration_days": 30}
        ),
    ]
    db.add_all(artifacts1)
    
    # ==========================================
    # SCENARIO 2: Running Performance Tuning
    # ==========================================
    print("  ⚡ Creating running performance tuning workflow...")
    
    workflow2 = WorkflowExecution(
        agent_id=perf_agent.id,
        customer_id=customer1.id,
        workflow_type=WorkflowType.PERFORMANCE_TUNING,
        status=WorkflowStatus.RUNNING,
        started_at=now - timedelta(minutes=15),
        completed_at=None,
        input_data={
            "target_latency_p95": 300,
            "current_latency_p95": 800,
            "optimization_budget_hours": 2
        },
        output_data={},
        workflow_metadata={
            "triggered_by": "user",
            "priority": "high"
        }
    )
    db.add(workflow2)
    db.flush()
    
    # Steps for workflow2 (partially complete)
    steps2 = [
        WorkflowStep(
            workflow_execution_id=workflow2.id,
            step_name="baseline_measurement",
            step_order=1,
            status=StepStatus.COMPLETED,
            started_at=now - timedelta(minutes=15),
            completed_at=now - timedelta(minutes=13),
            input_data={"sample_size": 1000},
            output_data={
                "p50_latency": 450,
                "p95_latency": 800,
                "p99_latency": 1200
            },
            retry_count=0
        ),
        WorkflowStep(
            workflow_execution_id=workflow2.id,
            step_name="analyze_kv_cache",
            step_order=2,
            status=StepStatus.COMPLETED,
            started_at=now - timedelta(minutes=13),
            completed_at=now - timedelta(minutes=10),
            input_data={"current_cache_size_gb": 32},
            output_data={
                "cache_hit_rate": 0.67,
                "recommended_size_gb": 48,
                "expected_improvement": "25%"
            },
            retry_count=0
        ),
        WorkflowStep(
            workflow_execution_id=workflow2.id,
            step_name="test_configurations",
            step_order=3,
            status=StepStatus.RUNNING,
            started_at=now - timedelta(minutes=10),
            completed_at=None,
            input_data={"configurations_to_test": 5},
            output_data={"configurations_tested": 2},
            retry_count=0
        ),
        WorkflowStep(
            workflow_execution_id=workflow2.id,
            step_name="apply_optimizations",
            step_order=4,
            status=StepStatus.PENDING,
            started_at=None,
            completed_at=None,
            input_data={},
            output_data={},
            retry_count=0
        ),
    ]
    db.add_all(steps2)
    db.flush()
    
    # Artifacts for workflow2
    artifacts2 = [
        WorkflowArtifact(
            workflow_execution_id=workflow2.id,
            workflow_step_id=steps2[0].id,
            artifact_type=ArtifactType.METRICS,
            artifact_name="Baseline Metrics",
            artifact_path="s3://optiinfra-data/customer1/baseline_metrics_20251019.json",
            artifact_size_bytes=23456,
            content_type="application/json",
            artifact_metadata={"measurement_duration_seconds": 120}
        ),
    ]
    db.add_all(artifacts2)
    
    # ==========================================
    # SCENARIO 3: Failed Quality Check
    # ==========================================
    print("  ❌ Creating failed quality check workflow...")
    
    workflow3 = WorkflowExecution(
        agent_id=app_agent.id,
        customer_id=customer2.id,
        workflow_type=WorkflowType.QUALITY_CHECK,
        status=WorkflowStatus.FAILED,
        started_at=now - timedelta(hours=3),
        completed_at=now - timedelta(hours=2, minutes=55),
        input_data={
            "check_type": "regression_test",
            "baseline_version": "v1.2.0",
            "test_version": "v1.3.0"
        },
        output_data={},
        error_details={
            "error_type": "QualityThresholdBreach",
            "error_message": "Quality score dropped below threshold: 0.78 < 0.85",
            "failed_at_step": "quality_validation",
            "can_retry": False
        },
        workflow_metadata={
            "triggered_by": "deployment_pipeline",
            "priority": "high"
        }
    )
    db.add(workflow3)
    db.flush()
    
    # Steps for workflow3
    steps3 = [
        WorkflowStep(
            workflow_execution_id=workflow3.id,
            step_name="collect_samples",
            step_order=1,
            status=StepStatus.COMPLETED,
            started_at=now - timedelta(hours=3),
            completed_at=now - timedelta(hours=2, minutes=58),
            input_data={"sample_count": 100},
            output_data={"samples_collected": 100},
            retry_count=0
        ),
        WorkflowStep(
            workflow_execution_id=workflow3.id,
            step_name="run_quality_checks",
            step_order=2,
            status=StepStatus.COMPLETED,
            started_at=now - timedelta(hours=2, minutes=58),
            completed_at=now - timedelta(hours=2, minutes=56),
            input_data={"metrics": ["coherence", "relevance", "factuality"]},
            output_data={
                "coherence_score": 0.82,
                "relevance_score": 0.79,
                "factuality_score": 0.73,
                "overall_score": 0.78
            },
            retry_count=0
        ),
        WorkflowStep(
            workflow_execution_id=workflow3.id,
            step_name="quality_validation",
            step_order=3,
            status=StepStatus.FAILED,
            started_at=now - timedelta(hours=2, minutes=56),
            completed_at=now - timedelta(hours=2, minutes=55),
            input_data={"threshold": 0.85},
            output_data={},
            error_details={
                "error": "Quality score 0.78 below threshold 0.85",
                "recommendation": "Roll back to v1.2.0"
            },
            retry_count=0
        ),
    ]
    db.add_all(steps3)
    db.flush()
    
    # Artifacts for workflow3
    artifacts3 = [
        WorkflowArtifact(
            workflow_execution_id=workflow3.id,
            workflow_step_id=steps3[1].id,
            artifact_type=ArtifactType.DIAGNOSTIC,
            artifact_name="Quality Check Results",
            artifact_path="s3://optiinfra-data/customer2/quality_results_20251019.json",
            artifact_size_bytes=67890,
            content_type="application/json",
            artifact_metadata={"failed_metrics": ["factuality"]}
        ),
        WorkflowArtifact(
            workflow_execution_id=workflow3.id,
            workflow_step_id=steps3[2].id,
            artifact_type=ArtifactType.ALERT,
            artifact_name="Quality Alert",
            artifact_path="s3://optiinfra-alerts/customer2/quality_alert_20251019.json",
            artifact_size_bytes=1234,
            content_type="application/json",
            artifact_metadata={
                "severity": "high",
                "action_required": "rollback"
            }
        ),
    ]
    db.add_all(artifacts3)
    
    db.commit()
    
    print("\n✅ Workflow history tables seeded successfully!")
    print(f"   📊 Workflow Executions: 3")
    print(f"   📝 Workflow Steps: {len(steps1) + len(steps2) + len(steps3)}")
    print(f"   📦 Workflow Artifacts: {len(artifacts1) + len(artifacts2) + len(artifacts3)}")
    
    return {
        "workflows": [workflow1, workflow2, workflow3],
        "steps": steps1 + steps2 + steps3,
        "artifacts": artifacts1 + artifacts2 + artifacts3
    }

def main():
    """Main entry point"""
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        seed_workflow_history_tables(session)
    except Exception as e:
        print(f"❌ Error seeding workflow history tables: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()
