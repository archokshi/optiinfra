"""
Seed data for application schema tables (FOUNDATION-0.2e)
Populates: quality_metrics, quality_baselines, quality_regressions
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from shared.database.models import (
    Agent, Customer, WorkflowExecution,
    QualityMetric, QualityBaseline, QualityRegression,
    BaselineType, RegressionType, RegressionSeverity, RegressionAction,
    WorkflowType, WorkflowStatus, AgentType
)
from shared.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import random

def seed_application_schema_tables(db: Session):
    """Seed application schema tables with realistic test data"""
    
    print("🌱 Seeding application schema tables...")
    
    # Get existing test data
    app_agent = db.query(Agent).filter_by(type=AgentType.APPLICATION).first()
    cost_agent = db.query(Agent).filter_by(type=AgentType.COST).first()
    
    customers = db.query(Customer).all()
    customer1 = customers[0] if len(customers) > 0 else None
    customer2 = customers[1] if len(customers) > 1 else None
    
    if not all([app_agent, cost_agent, customer1, customer2]):
        raise ValueError("❌ Required agents/customers not found! Run previous seed scripts first.")
    
    now = datetime.now()
    
    # ==========================================
    # SEED QUALITY METRICS
    # ==========================================
    print("  📊 Seeding quality_metrics...")
    
    models = [
        ("gpt-4", "0314"),
        ("claude-3-opus", "20240229"),
        ("llama-3-70b", "instruct"),
        ("gpt-3.5-turbo", "0125"),
    ]
    
    metrics = []
    
    # Generate quality metrics for different models and time periods
    for model_name, model_version in models:
        for hour in range(24):  # 24 hours of data
            timestamp = now - timedelta(hours=23-hour)
            
            # Generate 2-4 metrics per hour
            num_metrics = random.randint(2, 4)
            for i in range(num_metrics):
                # Base quality scores (vary by model)
                if "gpt-4" in model_name:
                    base_relevance, base_coherence, base_factuality = 0.88, 0.91, 0.86
                elif "claude" in model_name:
                    base_relevance, base_coherence, base_factuality = 0.90, 0.93, 0.89
                elif "llama" in model_name:
                    base_relevance, base_coherence, base_factuality = 0.82, 0.85, 0.80
                else:  # gpt-3.5
                    base_relevance, base_coherence, base_factuality = 0.78, 0.82, 0.75
                
                # Add variance
                relevance = min(1.0, max(0.0, base_relevance + random.uniform(-0.05, 0.05)))
                coherence = min(1.0, max(0.0, base_coherence + random.uniform(-0.05, 0.05)))
                factuality = min(1.0, max(0.0, base_factuality + random.uniform(-0.05, 0.05)))
                
                # Occasionally detect hallucination
                hallucination = random.random() < 0.03  # 3% rate
                if hallucination:
                    factuality = max(0.5, factuality - 0.3)
                
                # Calculate overall score
                overall = (relevance + coherence + factuality) / 3
                
                # Latency varies by model
                if "gpt-4" in model_name:
                    latency = random.uniform(800, 1500)
                elif "claude" in model_name:
                    latency = random.uniform(600, 1200)
                else:
                    latency = random.uniform(400, 900)
                
                metric = QualityMetric(
                    agent_id=app_agent.id,
                    customer_id=customer1.id,
                    request_id=f"req-{model_name}-{hour:02d}-{i:02d}-{timestamp.strftime('%Y%m%d%H%M')}",
                    model_name=model_name,
                    model_version=model_version,
                    prompt_tokens=random.randint(50, 500),
                    completion_tokens=random.randint(100, 800),
                    latency_ms=latency,
                    relevance_score=relevance,
                    coherence_score=coherence,
                    factuality_score=factuality,
                    hallucination_detected=hallucination,
                    toxicity_score=random.uniform(0.0, 0.05),
                    overall_quality_score=overall,
                    timestamp=timestamp + timedelta(minutes=i*15),
                    quality_metadata={
                        "user_id": f"user_{random.randint(1, 10)}",
                        "session_id": f"session_{random.randint(1, 50)}",
                        "endpoint": "/api/chat/completions"
                    }
                )
                metrics.append(metric)
    
    # Add metrics for customer2
    for i in range(10):
        timestamp = now - timedelta(hours=random.randint(0, 12))
        metric = QualityMetric(
            agent_id=app_agent.id,
            customer_id=customer2.id,
            request_id=f"req-techstart-{i:03d}-{timestamp.strftime('%Y%m%d%H%M')}",
            model_name="gpt-4",
            model_version="0314",
            prompt_tokens=random.randint(100, 400),
            completion_tokens=random.randint(200, 600),
            latency_ms=random.uniform(700, 1300),
            relevance_score=random.uniform(0.85, 0.95),
            coherence_score=random.uniform(0.88, 0.95),
            factuality_score=random.uniform(0.83, 0.92),
            hallucination_detected=False,
            toxicity_score=random.uniform(0.0, 0.03),
            overall_quality_score=random.uniform(0.85, 0.93),
            timestamp=timestamp,
            quality_metadata={"customer": "techstart"}
        )
        metrics.append(metric)
    
    db.add_all(metrics)
    db.commit()
    print(f"    ✅ Created {len(metrics)} quality metrics")
    
    # ==========================================
    # SEED QUALITY BASELINES
    # ==========================================
    print("  📈 Seeding quality_baselines...")
    
    baselines = []
    
    # Initial baselines for each model
    for model_name, model_version in models:
        model_metrics = [m for m in metrics if m.model_name == model_name]
        
        if model_metrics:
            avg_relevance = sum(m.relevance_score for m in model_metrics if m.relevance_score) / len([m for m in model_metrics if m.relevance_score])
            avg_coherence = sum(m.coherence_score for m in model_metrics if m.coherence_score) / len([m for m in model_metrics if m.coherence_score])
            avg_factuality = sum(m.factuality_score for m in model_metrics if m.factuality_score) / len([m for m in model_metrics if m.factuality_score])
            avg_overall = sum(m.overall_quality_score for m in model_metrics) / len(model_metrics)
            latencies = sorted([m.latency_ms for m in model_metrics if m.latency_ms])
            p95_latency = latencies[int(len(latencies) * 0.95)] if latencies else 1000.0
            
            baseline = QualityBaseline(
                agent_id=app_agent.id,
                customer_id=customer1.id,
                model_name=model_name,
                model_version=model_version,
                baseline_type=BaselineType.INITIAL,
                sample_size=len(model_metrics),
                avg_relevance_score=avg_relevance,
                avg_coherence_score=avg_coherence,
                avg_factuality_score=avg_factuality,
                avg_overall_score=avg_overall,
                p95_latency_ms=p95_latency,
                established_at=now - timedelta(days=7),
                valid_until=None,
                baseline_metadata={
                    "confidence_interval": 0.95,
                    "std_dev": 0.05,
                    "collection_period_days": 7
                }
            )
            baselines.append(baseline)
    
    # Updated baseline for GPT-4
    baseline = QualityBaseline(
        agent_id=app_agent.id,
        customer_id=customer1.id,
        model_name="gpt-4",
        model_version="0314",
        baseline_type=BaselineType.UPDATED,
        sample_size=80,
        avg_relevance_score=0.90,
        avg_coherence_score=0.93,
        avg_factuality_score=0.88,
        avg_overall_score=0.90,
        p95_latency_ms=1200.0,
        established_at=now - timedelta(days=2),
        valid_until=None,
        baseline_metadata={
            "improvement_from_initial": "+2.3%",
            "optimizations_applied": ["prompt_tuning", "temperature_adjustment"]
        }
    )
    baselines.append(baseline)
    
    # Rollback baseline
    baseline = QualityBaseline(
        agent_id=app_agent.id,
        customer_id=customer1.id,
        model_name="gpt-4",
        model_version="0314",
        baseline_type=BaselineType.ROLLBACK,
        sample_size=100,
        avg_relevance_score=0.87,
        avg_coherence_score=0.90,
        avg_factuality_score=0.85,
        avg_overall_score=0.87,
        p95_latency_ms=1100.0,
        established_at=now - timedelta(days=14),
        valid_until=None,
        baseline_metadata={
            "reason": "Last known good configuration",
            "saved_for": "emergency_rollback"
        }
    )
    baselines.append(baseline)
    
    # Customer2 baseline
    baseline = QualityBaseline(
        agent_id=app_agent.id,
        customer_id=customer2.id,
        model_name="gpt-4",
        model_version="0314",
        baseline_type=BaselineType.INITIAL,
        sample_size=100,
        avg_relevance_score=0.89,
        avg_coherence_score=0.92,
        avg_factuality_score=0.87,
        avg_overall_score=0.89,
        p95_latency_ms=1150.0,
        established_at=now - timedelta(days=5),
        valid_until=None,
        baseline_metadata={"customer": "techstart"}
    )
    baselines.append(baseline)
    
    db.add_all(baselines)
    db.commit()
    print(f"    ✅ Created {len(baselines)} quality baselines")
    
    # ==========================================
    # SEED QUALITY REGRESSIONS
    # ==========================================
    print("  🚨 Seeding quality_regressions...")
    
    # Get baselines
    gpt4_baseline = db.query(QualityBaseline).filter_by(
        model_name="gpt-4",
        baseline_type=BaselineType.INITIAL
    ).first()
    
    claude_baseline = db.query(QualityBaseline).filter_by(
        model_name="claude-3-opus"
    ).first()
    
    llama_baseline = db.query(QualityBaseline).filter_by(
        model_name="llama-3-70b"
    ).first()
    
    # Create workflow for regression
    regression_workflow = WorkflowExecution(
        agent_id=cost_agent.id,
        customer_id=customer1.id,
        workflow_type=WorkflowType.CONFIGURATION_UPDATE,
        status=WorkflowStatus.COMPLETED,
        started_at=now - timedelta(hours=8),
        completed_at=now - timedelta(hours=7, minutes=55),
        input_data={
            "optimization": "reduce_model_size",
            "target_cost_reduction": "30%"
        },
        output_data={
            "model_changed": "gpt-4 -> gpt-3.5-turbo",
            "cost_reduction": "32%"
        },
        workflow_metadata={}
    )
    db.add(regression_workflow)
    db.commit()
    
    regressions = []
    
    # Regression 1: Quality drop (CRITICAL - with rollback)
    if gpt4_baseline:
        regression = QualityRegression(
            agent_id=app_agent.id,
            customer_id=customer1.id,
            baseline_id=gpt4_baseline.id,
            workflow_execution_id=regression_workflow.id,
            regression_type=RegressionType.QUALITY_DROP,
            severity=RegressionSeverity.CRITICAL,
            detected_at=now - timedelta(hours=6),
            metric_name="overall_quality_score",
            baseline_value=0.88,
            current_value=0.72,
            delta_percent=-18.2,
            sample_size=50,
            action_taken=RegressionAction.ROLLBACK_TRIGGERED,
            resolved_at=now - timedelta(hours=5, minutes=45),
            resolution_notes="Automatic rollback triggered due to >15% quality drop. Reverted to previous model configuration.",
            regression_metadata={
                "rollback_duration_minutes": 15,
                "affected_users": 127,
                "rollback_successful": True,
                "post_rollback_quality": 0.87
            }
        )
        regressions.append(regression)
    
    # Regression 2: Latency increase (HIGH - manual review)
    if claude_baseline:
        regression = QualityRegression(
            agent_id=app_agent.id,
            customer_id=customer1.id,
            baseline_id=claude_baseline.id,
            workflow_execution_id=None,
            regression_type=RegressionType.LATENCY_INCREASE,
            severity=RegressionSeverity.HIGH,
            detected_at=now - timedelta(hours=3),
            metric_name="p95_latency_ms",
            baseline_value=900.0,
            current_value=1450.0,
            delta_percent=61.1,
            sample_size=75,
            action_taken=RegressionAction.MANUAL_REVIEW,
            resolved_at=now - timedelta(hours=1),
            resolution_notes="Investigation revealed network congestion. Added caching layer to mitigate.",
            regression_metadata={
                "investigation_time_hours": 2,
                "root_cause": "network_congestion",
                "mitigation": "caching_layer_added"
            }
        )
        regressions.append(regression)
    
    # Regression 3: Hallucination spike (MEDIUM)
    if llama_baseline:
        regression = QualityRegression(
            agent_id=app_agent.id,
            customer_id=customer1.id,
            baseline_id=llama_baseline.id,
            workflow_execution_id=None,
            regression_type=RegressionType.HALLUCINATION_SPIKE,
            severity=RegressionSeverity.MEDIUM,
            detected_at=now - timedelta(hours=12),
            metric_name="hallucination_rate",
            baseline_value=0.02,
            current_value=0.08,
            delta_percent=300.0,
            sample_size=100,
            action_taken=RegressionAction.ALERT_ONLY,
            resolved_at=now - timedelta(hours=10),
            resolution_notes="Hallucination spike due to edge case inputs. Added input validation.",
            regression_metadata={
                "hallucination_examples": 8,
                "fix_applied": "input_validation",
                "fix_effectiveness": "100%"
            }
        )
        regressions.append(regression)
    
    # Regression 4: Quality drop (LOW - auto-fixed)
    if gpt4_baseline:
        regression = QualityRegression(
            agent_id=app_agent.id,
            customer_id=customer1.id,
            baseline_id=gpt4_baseline.id,
            workflow_execution_id=None,
            regression_type=RegressionType.QUALITY_DROP,
            severity=RegressionSeverity.LOW,
            detected_at=now - timedelta(days=2),
            metric_name="coherence_score",
            baseline_value=0.91,
            current_value=0.86,
            delta_percent=-5.5,
            sample_size=80,
            action_taken=RegressionAction.AUTO_FIXED,
            resolved_at=now - timedelta(days=2, hours=1),
            resolution_notes="Minor coherence drop. Auto-adjusted temperature parameter.",
            regression_metadata={
                "auto_fix": "temperature_adjustment",
                "temperature_before": 0.9,
                "temperature_after": 0.7,
                "fix_time_minutes": 5
            }
        )
        regressions.append(regression)
    
    # Regression 5: Toxicity increase (MEDIUM - unresolved)
    if claude_baseline:
        regression = QualityRegression(
            agent_id=app_agent.id,
            customer_id=customer1.id,
            baseline_id=claude_baseline.id,
            workflow_execution_id=None,
            regression_type=RegressionType.TOXICITY_INCREASE,
            severity=RegressionSeverity.MEDIUM,
            detected_at=now - timedelta(hours=4),
            metric_name="toxicity_score",
            baseline_value=0.02,
            current_value=0.07,
            delta_percent=250.0,
            sample_size=60,
            action_taken=RegressionAction.MANUAL_REVIEW,
            resolved_at=None,  # Still under investigation
            resolution_notes=None,
            regression_metadata={
                "investigation_status": "in_progress",
                "suspected_cause": "adversarial_inputs",
                "mitigation_in_progress": "content_filtering"
            }
        )
        regressions.append(regression)
    
    # Regression 6: Customer2 quality drop
    customer2_baseline = db.query(QualityBaseline).filter_by(
        customer_id=customer2.id
    ).first()
    
    if customer2_baseline:
        regression = QualityRegression(
            agent_id=app_agent.id,
            customer_id=customer2.id,
            baseline_id=customer2_baseline.id,
            workflow_execution_id=None,
            regression_type=RegressionType.QUALITY_DROP,
            severity=RegressionSeverity.HIGH,
            detected_at=now - timedelta(hours=18),
            metric_name="factuality_score",
            baseline_value=0.87,
            current_value=0.74,
            delta_percent=-14.9,
            sample_size=45,
            action_taken=RegressionAction.ROLLBACK_TRIGGERED,
            resolved_at=now - timedelta(hours=17, minutes=50),
            resolution_notes="Factuality drop after configuration change. Rolled back successfully.",
            regression_metadata={
                "customer": "techstart",
                "rollback_successful": True
            }
        )
        regressions.append(regression)
    
    db.add_all(regressions)
    db.commit()
    print(f"    ✅ Created {len(regressions)} quality regressions")
    
    print("\n✅ Application schema tables seeded successfully!")
    print(f"   📊 Metrics: {len(metrics)} (across 4 models, 24 hours)")
    print(f"   📈 Baselines: {len(baselines)} (initial, updated, rollback)")
    print(f"   🚨 Regressions: {len(regressions)} (5 resolved, 1 pending)")
    
    return {
        "metrics": metrics,
        "baselines": baselines,
        "regressions": regressions,
        "workflow": regression_workflow
    }

def main():
    """Main entry point"""
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        seed_application_schema_tables(session)
    except Exception as e:
        print(f"❌ Error seeding application schema: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()
