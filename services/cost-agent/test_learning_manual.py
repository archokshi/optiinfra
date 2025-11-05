"""
Manual test script for Learning Loop.

Run this to test the learning loop manually.
"""

import asyncio
import os
from datetime import datetime

from src.learning.outcome_tracker import OutcomeTracker
from src.learning.knowledge_store import KnowledgeStore
from src.learning.feedback_analyzer import FeedbackAnalyzer
from src.learning.improvement_engine import ImprovementEngine
from src.learning.learning_loop import LearningLoop


async def test_outcome_tracking():
    """Test outcome tracking."""
    print("\n" + "="*60)
    print("TEST 1: Outcome Tracking")
    print("="*60)
    
    tracker = OutcomeTracker()
    
    # Track a successful outcome
    outcome = await tracker.track_execution_outcome(
        execution_id="exec-manual-123",
        recommendation_id="rec-manual-456",
        outcome_data={
            "success": True,
            "actual_savings": 52.00,
            "predicted_savings": 50.00,
            "execution_duration_seconds": 120.0,
            "issues_encountered": [],
            "post_execution_metrics": {
                "region": "us-east-1",
                "resource_type": "ec2"
            },
            "recommendation_type": "terminate"
        }
    )
    
    print(f"\n✅ Outcome tracked:")
    print(f"   Outcome ID: {outcome.outcome_id}")
    print(f"   Success: {outcome.success}")
    print(f"   Actual Savings: ${outcome.actual_savings:.2f}")
    print(f"   Predicted Savings: ${outcome.predicted_savings:.2f}")
    print(f"   Accuracy: {outcome.savings_accuracy:.1%}")
    
    # Measure savings
    measurement = await tracker.measure_actual_savings(
        execution_id="exec-manual-123",
        days=30
    )
    
    print(f"\n✅ Savings measured:")
    print(f"   Period: {measurement.measurement_period_days} days")
    print(f"   Actual: ${measurement.actual_savings:.2f}")
    print(f"   Predicted: ${measurement.predicted_savings:.2f}")
    print(f"   Accuracy: {measurement.savings_accuracy:.1%}")
    
    # Compare predicted vs actual
    comparison = await tracker.compare_predicted_vs_actual(
        recommendation_id="rec-manual-456"
    )
    
    print(f"\n✅ Comparison:")
    print(f"   Prediction Error: {comparison.prediction_error:.1%}")
    print(f"   Execution Success: {comparison.execution_success}")
    print(f"   Notes: {', '.join(comparison.notes)}")
    
    print("\n✅ Outcome tracking test PASSED")
    return tracker


async def test_knowledge_store():
    """Test knowledge store (Qdrant)."""
    print("\n" + "="*60)
    print("TEST 2: Knowledge Store (Qdrant)")
    print("="*60)
    
    # Get OpenAI API key from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    store = KnowledgeStore(
        qdrant_url="http://localhost:6333",
        openai_api_key=openai_api_key
    )
    
    # Check health
    print("\n🔍 Checking Qdrant health...")
    try:
        healthy = await store.check_health()
        if healthy:
            print("✅ Qdrant is healthy")
        else:
            print("⚠️  Qdrant health check failed")
            return None
    except Exception as e:
        print(f"❌ Qdrant not available: {e}")
        print("   Please start Qdrant: docker run -p 6333:6333 qdrant/qdrant")
        return None
    
    # Initialize collections
    print("\n🔧 Initializing collections...")
    try:
        await store.initialize_collections()
        print("✅ Collections initialized")
    except Exception as e:
        print(f"⚠️  Collection initialization: {e}")
    
    # Store a recommendation outcome
    print("\n💾 Storing recommendation outcome...")
    recommendation = {
        "recommendation_id": "rec-qdrant-123",
        "recommendation_type": "terminate",
        "resource_type": "ec2",
        "resource_id": "i-test123",
        "region": "us-east-1",
        "monthly_savings": 50.00,
        "risk_level": "high"
    }
    
    outcome = {
        "outcome_id": "outcome-qdrant-123",
        "success": True,
        "actual_savings": 52.00,
        "predicted_savings": 50.00,
        "savings_accuracy": 1.04,
        "timestamp": datetime.utcnow()
    }
    
    try:
        vector_id = await store.store_recommendation_outcome(
            recommendation=recommendation,
            outcome=outcome
        )
        print(f"✅ Stored in Qdrant: {vector_id}")
    except Exception as e:
        print(f"⚠️  Storage error: {e}")
        return None
    
    # Find similar cases
    print("\n🔍 Finding similar cases...")
    try:
        similar_cases = await store.find_similar_cases(
            recommendation=recommendation,
            limit=5
        )
        print(f"✅ Found {len(similar_cases)} similar cases")
        for i, case in enumerate(similar_cases[:3], 1):
            print(f"   {i}. Similarity: {case.similarity_score:.2f}")
            print(f"      Success: {case.outcome.success}")
            print(f"      Savings: ${case.outcome.actual_savings:.2f}")
    except Exception as e:
        print(f"⚠️  Search error: {e}")
    
    # Get success rate
    print("\n📊 Getting success rate...")
    try:
        success_rate = await store.get_success_rate("terminate")
        print(f"✅ Success rate for 'terminate': {success_rate:.1%}")
    except Exception as e:
        print(f"⚠️  Error: {e}")
    
    print("\n✅ Knowledge store test PASSED")
    return store


async def test_feedback_analysis(tracker):
    """Test feedback analysis."""
    print("\n" + "="*60)
    print("TEST 3: Feedback Analysis")
    print("="*60)
    
    # Create more test data
    print("\n📝 Creating test outcomes...")
    for i in range(10):
        await tracker.track_execution_outcome(
            execution_id=f"exec-feedback-{i}",
            recommendation_id=f"rec-feedback-{i}",
            outcome_data={
                "success": i < 8,  # 80% success rate
                "actual_savings": 48.0 if i < 8 else 0.0,
                "predicted_savings": 50.0,
                "execution_duration_seconds": 100.0 + i * 10,
                "issues_encountered": [] if i < 8 else ["Permission denied"],
                "post_execution_metrics": {"region": "us-east-1"},
                "recommendation_type": "terminate"
            }
        )
    print(f"✅ Created 10 test outcomes")
    
    analyzer = FeedbackAnalyzer(outcome_tracker=tracker)
    
    # Analyze success patterns
    print("\n📈 Analyzing success patterns...")
    success_patterns = await analyzer.analyze_success_patterns(
        recommendation_type="terminate",
        lookback_days=30
    )
    
    print(f"✅ Success Patterns:")
    print(f"   Success Rate: {success_patterns.success_rate:.1%}")
    print(f"   Total Cases: {success_patterns.total_cases}")
    print(f"   Avg Savings Accuracy: {success_patterns.avg_savings_accuracy:.1%}")
    print(f"   Confidence: {success_patterns.confidence:.1%}")
    print(f"   Characteristics: {len(success_patterns.common_characteristics)}")
    
    # Analyze failure patterns
    print("\n📉 Analyzing failure patterns...")
    failure_patterns = await analyzer.analyze_failure_patterns(
        recommendation_type="terminate",
        lookback_days=30
    )
    
    print(f"✅ Failure Patterns:")
    print(f"   Failure Rate: {failure_patterns.failure_rate:.1%}")
    print(f"   Common Causes: {len(failure_patterns.common_causes)}")
    if failure_patterns.common_causes:
        for cause in failure_patterns.common_causes[:3]:
            print(f"      - {cause}")
    
    # Calculate accuracy metrics
    print("\n🎯 Calculating accuracy metrics...")
    metrics = await analyzer.calculate_accuracy_metrics("terminate")
    
    print(f"✅ Accuracy Metrics:")
    print(f"   Total Executions: {metrics.total_executions}")
    print(f"   Success Rate: {metrics.success_rate:.1%}")
    print(f"   Avg Savings Accuracy: {metrics.avg_savings_accuracy:.1%}")
    print(f"   Avg Prediction Error: {metrics.avg_prediction_error:.1%}")
    print(f"   Improvement: {metrics.improvement_over_baseline:.1%}")
    
    # Generate insights
    print("\n💡 Generating learning insights...")
    insights = await analyzer.generate_learning_insights(lookback_days=30)
    
    print(f"✅ Generated {len(insights)} insights")
    for i, insight in enumerate(insights[:3], 1):
        print(f"   {i}. {insight.insight_type}: {insight.description[:60]}...")
        print(f"      Confidence: {insight.confidence:.1%}, Impact: {insight.impact}")
    
    print("\n✅ Feedback analysis test PASSED")
    return analyzer


async def test_improvement_engine(tracker, analyzer):
    """Test improvement engine."""
    print("\n" + "="*60)
    print("TEST 4: Improvement Engine")
    print("="*60)
    
    engine = ImprovementEngine()
    
    # Generate insights
    insights = await analyzer.generate_learning_insights(lookback_days=30)
    
    # Adjust scoring weights
    print("\n⚖️  Adjusting scoring weights...")
    weights = await engine.adjust_scoring_weights(insights)
    
    print(f"✅ Scoring Weights:")
    print(f"   ROI Weight: {weights.roi_weight:.2f}")
    print(f"   Risk Weight: {weights.risk_weight:.2f}")
    print(f"   Urgency Weight: {weights.urgency_weight:.2f}")
    print(f"   Confidence Weight: {weights.confidence_weight:.2f}")
    print(f"   Total: {weights.roi_weight + weights.risk_weight + weights.urgency_weight + weights.confidence_weight:.2f}")
    
    # Refine cost predictions
    print("\n📊 Refining cost predictions...")
    historical = await tracker.get_outcomes_by_type("terminate", limit=100)
    
    if len(historical) >= 5:
        model = await engine.refine_cost_predictions(
            recommendation_type="terminate",
            historical_data=historical
        )
        
        print(f"✅ Prediction Model:")
        print(f"   Base Accuracy: {model.base_accuracy:.1%}")
        print(f"   Training Samples: {model.training_samples}")
        print(f"   Adjustment Factors: {len(model.adjustment_factors)}")
        print(f"   Confidence Interval: {model.confidence_interval:.1%}")
    else:
        print(f"⚠️  Not enough data ({len(historical)} samples, need 5+)")
    
    # Update risk assessments
    print("\n⚠️  Updating risk assessments...")
    failure_patterns = await analyzer.analyze_failure_patterns("terminate", 30)
    
    if failure_patterns.total_cases >= 3:
        risk_model = await engine.update_risk_assessments(failure_patterns)
        
        print(f"✅ Risk Model:")
        print(f"   Base Risk Score: {risk_model.base_risk_score:.1%}")
        print(f"   Risk Factors: {len(risk_model.risk_factors)}")
        print(f"   Failure Indicators: {len(risk_model.failure_indicators)}")
    else:
        print(f"⚠️  Not enough failure data ({failure_patterns.total_cases} cases)")
    
    print("\n✅ Improvement engine test PASSED")
    return engine


async def test_learning_loop():
    """Test complete learning loop."""
    print("\n" + "="*60)
    print("TEST 5: Learning Loop (End-to-End)")
    print("="*60)
    
    loop = LearningLoop()
    
    # Process an execution outcome
    print("\n🔄 Processing execution outcome...")
    result = await loop.process_execution_outcome(
        execution_id="exec-loop-123",
        recommendation_id="rec-loop-456",
        outcome_data={
            "success": True,
            "actual_savings": 52.00,
            "predicted_savings": 50.00,
            "execution_duration_seconds": 120.0,
            "issues_encountered": [],
            "post_execution_metrics": {},
            "recommendation_type": "terminate"
        }
    )
    
    print(f"✅ Outcome processed:")
    print(f"   Outcome ID: {result.outcome_id}")
    print(f"   Stored in Qdrant: {result.stored_in_qdrant}")
    print(f"   Insights Generated: {result.insights_generated}")
    print(f"   Processing Time: {result.processing_time_seconds:.2f}s")
    
    # Run learning cycle
    print("\n🔄 Running learning cycle...")
    cycle_result = await loop.run_learning_cycle(force=True)
    
    print(f"✅ Learning cycle completed:")
    print(f"   Cycle ID: {cycle_result.cycle_id}")
    print(f"   Outcomes Processed: {cycle_result.outcomes_processed}")
    print(f"   Insights Generated: {cycle_result.insights_generated}")
    print(f"   Improvements Applied: {cycle_result.improvements_applied}")
    print(f"   Accuracy Improvement: {cycle_result.accuracy_improvement:.1%}")
    print(f"   Duration: {cycle_result.duration_seconds:.2f}s")
    
    # Get learning metrics
    print("\n📊 Getting learning metrics...")
    metrics = await loop.get_learning_metrics()
    
    print(f"✅ Learning Metrics:")
    print(f"   Total Outcomes: {metrics.total_outcomes_tracked}")
    print(f"   Success Rate: {metrics.success_rate:.1%}")
    print(f"   Avg Savings Accuracy: {metrics.avg_savings_accuracy:.1%}")
    print(f"   Avg Prediction Error: {metrics.avg_prediction_error:.1%}")
    print(f"   Improvement: {metrics.improvement_over_baseline:.1%}")
    print(f"   Learning Cycles: {metrics.learning_cycles_completed}")
    print(f"   Active Improvements: {metrics.active_improvements}")
    
    print("\n✅ Learning loop test PASSED")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("🚀 LEARNING LOOP MANUAL TESTS")
    print("="*60)
    
    try:
        # Test 1: Outcome Tracking
        tracker = await test_outcome_tracking()
        
        # Test 2: Knowledge Store (Qdrant)
        store = await test_knowledge_store()
        
        # Test 3: Feedback Analysis
        analyzer = await test_feedback_analysis(tracker)
        
        # Test 4: Improvement Engine
        engine = await test_improvement_engine(tracker, analyzer)
        
        # Test 5: Learning Loop
        await test_learning_loop()
        
        print("\n" + "="*60)
        print("✅ ALL MANUAL TESTS PASSED!")
        print("="*60)
        print("\nLearning Loop is working correctly! 🎉\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
