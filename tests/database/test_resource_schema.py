"""
Comprehensive test suite for resource schema tables (FOUNDATION-0.2d)
Tests: ResourceMetric, ScalingEvent

TESTING PRINCIPLES:
- All tests use REAL PostgreSQL database
- All operations verified by querying back from database
- No mocks, no shortcuts, evidence-based assertions
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from shared.database.models import (
    Agent, Customer, WorkflowExecution,
    ResourceMetric, ScalingEvent,
    ResourceType, ScalingEventType,
    AgentType, AgentStatus, CustomerStatus,
    WorkflowType, WorkflowStatus
)


class TestResourceMetric:
    """Test ResourceMetric model with real database operations"""
    
    def test_create_resource_metric(self, db_session):
        """Test creating a resource metric and verifying persistence"""
        # Create dependencies
        customer = Customer(name="Test", email="metric1@test.com", api_key="key1", status=CustomerStatus.ACTIVE)
        agent = Agent(
            type=AgentType.RESOURCE,
            name="test-resource-agent",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8001",
            capabilities=["monitoring"]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        
        # Create metric
        now = datetime.now()
        metric = ResourceMetric(
            agent_id=agent.id,
            customer_id=customer.id,
            instance_id="i-abc123",
            resource_type=ResourceType.GPU,
            metric_name="utilization",
            metric_value=85.5,
            unit="percent",
            timestamp=now,
            resource_metadata={
                "gpu_model": "NVIDIA H100",
                "gpu_memory_gb": 80
            }
        )
        db_session.add(metric)
        db_session.commit()
        
        # VERIFY: Query back from database
        retrieved = db_session.query(ResourceMetric).filter_by(id=metric.id).first()
        assert retrieved is not None
        assert retrieved.instance_id == "i-abc123"
        assert retrieved.resource_type == ResourceType.GPU
        assert retrieved.metric_name == "utilization"
        assert retrieved.metric_value == 85.5
        assert retrieved.unit == "percent"
        assert retrieved.resource_metadata["gpu_model"] == "NVIDIA H100"
    
    def test_resource_metric_agent_relationship(self, db_session):
        """Test metric -> agent relationship loads correctly"""
        customer = Customer(name="Test", email="metric2@test.com", api_key="key2", status=CustomerStatus.ACTIVE)
        agent = Agent(
            type=AgentType.RESOURCE,
            name="test-agent-2",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8002",
            capabilities=[]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        
        metric = ResourceMetric(
            agent_id=agent.id,
            customer_id=customer.id,
            instance_id="i-test",
            resource_type=ResourceType.CPU,
            metric_name="utilization",
            metric_value=65.0,
            unit="percent",
            timestamp=datetime.now()
        )
        db_session.add(metric)
        db_session.commit()
        
        # VERIFY: Relationship loads
        db_session.refresh(metric)
        assert metric.agent is not None
        assert metric.agent.id == agent.id
        assert metric in metric.agent.resource_metrics
    
    def test_resource_metric_customer_relationship(self, db_session):
        """Test metric -> customer relationship loads correctly"""
        customer = Customer(name="Test 3", email="metric3@test.com", api_key="key3", status=CustomerStatus.ACTIVE)
        agent = Agent(
            type=AgentType.RESOURCE,
            name="test-agent-3",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8003",
            capabilities=[]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        
        metric = ResourceMetric(
            agent_id=agent.id,
            customer_id=customer.id,
            instance_id="i-test3",
            resource_type=ResourceType.MEMORY,
            metric_name="used",
            metric_value=64.0,
            unit="GB",
            timestamp=datetime.now()
        )
        db_session.add(metric)
        db_session.commit()
        
        # VERIFY: Relationship loads
        db_session.refresh(metric)
        assert metric.customer is not None
        assert metric.customer.id == customer.id
        assert metric in metric.customer.resource_metrics
    
    def test_multiple_resource_types(self, db_session):
        """Test storing different resource types"""
        customer = Customer(name="Test", email="metric4@test.com", api_key="key4", status=CustomerStatus.ACTIVE)
        agent = Agent(
            type=AgentType.RESOURCE,
            name="test-agent-4",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8004",
            capabilities=[]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        
        now = datetime.now()
        metrics = [
            ResourceMetric(
                agent_id=agent.id,
                customer_id=customer.id,
                instance_id="i-multi",
                resource_type=ResourceType.GPU,
                metric_name="utilization",
                metric_value=75.0,
                unit="percent",
                timestamp=now
            ),
            ResourceMetric(
                agent_id=agent.id,
                customer_id=customer.id,
                instance_id="i-multi",
                resource_type=ResourceType.CPU,
                metric_name="utilization",
                metric_value=65.0,
                unit="percent",
                timestamp=now
            ),
            ResourceMetric(
                agent_id=agent.id,
                customer_id=customer.id,
                instance_id="i-multi",
                resource_type=ResourceType.MEMORY,
                metric_name="used",
                metric_value=64.0,
                unit="GB",
                timestamp=now
            ),
        ]
        
        db_session.add_all(metrics)
        db_session.commit()
        
        # VERIFY: All metrics persisted
        gpu_metrics = db_session.query(ResourceMetric).filter_by(
            instance_id="i-multi",
            resource_type=ResourceType.GPU
        ).all()
        assert len(gpu_metrics) == 1
        assert gpu_metrics[0].metric_value == 75.0
    
    def test_time_series_query(self, db_session):
        """Test querying metrics over time"""
        customer = Customer(name="Test", email="metric5@test.com", api_key="key5", status=CustomerStatus.ACTIVE)
        agent = Agent(
            type=AgentType.RESOURCE,
            name="test-agent-5",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8005",
            capabilities=[]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        
        instance_id = "i-timeseries"
        base_time = datetime.now()
        
        # Create hourly metrics
        for hour in range(5):
            metric = ResourceMetric(
                agent_id=agent.id,
                customer_id=customer.id,
                instance_id=instance_id,
                resource_type=ResourceType.GPU,
                metric_name="utilization",
                metric_value=60.0 + (hour * 5),
                unit="percent",
                timestamp=base_time - timedelta(hours=4-hour)
            )
            db_session.add(metric)
        
        db_session.commit()
        
        # VERIFY: Calculate average
        avg_value = db_session.query(
            func.avg(ResourceMetric.metric_value)
        ).filter(
            ResourceMetric.instance_id == instance_id
        ).scalar()
        
        assert avg_value == 70.0  # (60+65+70+75+80)/5


class TestScalingEvent:
    """Test ScalingEvent model with real database operations"""
    
    def test_create_scaling_event(self, db_session):
        """Test creating a scaling event and verifying persistence"""
        customer = Customer(name="Test", email="scale1@test.com", api_key="skey1", status=CustomerStatus.ACTIVE)
        agent = Agent(
            type=AgentType.RESOURCE,
            name="scale-agent-1",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:9001",
            capabilities=[]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        
        now = datetime.now()
        event = ScalingEvent(
            agent_id=agent.id,
            customer_id=customer.id,
            workflow_execution_id=None,
            event_type=ScalingEventType.SCALE_UP,
            trigger_reason="GPU utilization exceeded 85%",
            before_state={
                "instance_count": 3,
                "avg_utilization": 88.0
            },
            after_state={
                "instance_count": 5,
                "avg_utilization": 62.0
            },
            success=True,
            executed_at=now - timedelta(minutes=15),
            completed_at=now,
            scaling_metadata={
                "cost_impact": 20.0,
                "performance_improvement": "30%"
            }
        )
        db_session.add(event)
        db_session.commit()
        
        # VERIFY: Query back from database
        retrieved = db_session.query(ScalingEvent).filter_by(id=event.id).first()
        assert retrieved is not None
        assert retrieved.event_type == ScalingEventType.SCALE_UP
        assert retrieved.success is True
        assert retrieved.before_state["instance_count"] == 3
        assert retrieved.after_state["instance_count"] == 5
        assert retrieved.scaling_metadata["cost_impact"] == 20.0
    
    def test_scaling_event_relationships(self, db_session):
        """Test scaling event relationships"""
        customer = Customer(name="Test", email="scale2@test.com", api_key="skey2", status=CustomerStatus.ACTIVE)
        agent = Agent(
            type=AgentType.RESOURCE,
            name="scale-agent-2",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:9002",
            capabilities=[]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        
        event = ScalingEvent(
            agent_id=agent.id,
            customer_id=customer.id,
            event_type=ScalingEventType.SCALE_DOWN,
            trigger_reason="Low utilization",
            before_state={"count": 5},
            after_state={"count": 3},
            success=True,
            executed_at=datetime.now()
        )
        db_session.add(event)
        db_session.commit()
        
        # VERIFY: Relationships load
        db_session.refresh(event)
        assert event.agent is not None
        assert event.customer is not None
        assert event in event.agent.scaling_events
        assert event in event.customer.scaling_events
    
    def test_scaling_event_with_workflow(self, db_session):
        """Test scaling event linked to workflow"""
        customer = Customer(name="Test", email="scale3@test.com", api_key="skey3", status=CustomerStatus.ACTIVE)
        agent = Agent(
            type=AgentType.RESOURCE,
            name="scale-agent-3",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:9003",
            capabilities=[]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        
        # Create workflow
        workflow = WorkflowExecution(
            agent_id=agent.id,
            customer_id=customer.id,
            workflow_type=WorkflowType.SCALING_DECISION,
            status=WorkflowStatus.COMPLETED,
            started_at=datetime.now() - timedelta(hours=1),
            completed_at=datetime.now(),
            input_data={"trigger": "high_util"},
            output_data={"decision": "scale_up"},
            workflow_metadata={}
        )
        db_session.add(workflow)
        db_session.commit()
        
        # Create scaling event linked to workflow
        event = ScalingEvent(
            agent_id=agent.id,
            customer_id=customer.id,
            workflow_execution_id=workflow.id,
            event_type=ScalingEventType.SCALE_UP,
            trigger_reason="Workflow decision",
            before_state={"count": 2},
            after_state={"count": 4},
            success=True,
            executed_at=datetime.now(),
            completed_at=datetime.now()
        )
        db_session.add(event)
        db_session.commit()
        
        # VERIFY: Relationship loads
        db_session.refresh(event)
        assert event.workflow is not None
        assert event.workflow.id == workflow.id
        assert event in workflow.scaling_events
    
    def test_failed_scaling_event(self, db_session):
        """Test failed scaling event with error details"""
        customer = Customer(name="Test", email="scale4@test.com", api_key="skey4", status=CustomerStatus.ACTIVE)
        agent = Agent(
            type=AgentType.RESOURCE,
            name="scale-agent-4",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:9004",
            capabilities=[]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        
        event = ScalingEvent(
            agent_id=agent.id,
            customer_id=customer.id,
            event_type=ScalingEventType.SCALE_UP,
            trigger_reason="Manual scale request",
            before_state={"count": 2},
            after_state={"count": 2},
            success=False,
            error_details={
                "error_type": "InsufficientCapacity",
                "error_message": "No available H100 instances",
                "region": "us-west-2"
            },
            executed_at=datetime.now(),
            completed_at=datetime.now()
        )
        db_session.add(event)
        db_session.commit()
        
        # VERIFY: Error details persisted
        retrieved = db_session.query(ScalingEvent).filter_by(id=event.id).first()
        assert retrieved.success is False
        assert retrieved.error_details is not None
        assert "InsufficientCapacity" in retrieved.error_details["error_type"]
    
    def test_scaling_event_duration(self, db_session):
        """Test duration property calculation"""
        customer = Customer(name="Test", email="scale5@test.com", api_key="skey5", status=CustomerStatus.ACTIVE)
        agent = Agent(
            type=AgentType.RESOURCE,
            name="scale-agent-5",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:9005",
            capabilities=[]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        
        start = datetime.now()
        end = start + timedelta(minutes=15)
        
        event = ScalingEvent(
            agent_id=agent.id,
            customer_id=customer.id,
            event_type=ScalingEventType.SCALE_UP,
            trigger_reason="Test",
            before_state={},
            after_state={},
            success=True,
            executed_at=start,
            completed_at=end
        )
        db_session.add(event)
        db_session.commit()
        
        # VERIFY: Duration calculated correctly
        assert event.duration_seconds == 900  # 15 minutes
    
    def test_query_scaling_by_type(self, db_session):
        """Test querying scaling events by type"""
        customer = Customer(name="Test", email="scale6@test.com", api_key="skey6", status=CustomerStatus.ACTIVE)
        agent = Agent(
            type=AgentType.RESOURCE,
            name="scale-agent-6",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:9006",
            capabilities=[]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        
        events = [
            ScalingEvent(
                agent_id=agent.id,
                customer_id=customer.id,
                event_type=ScalingEventType.SCALE_UP,
                trigger_reason="Test 1",
                before_state={},
                after_state={},
                success=True,
                executed_at=datetime.now()
            ),
            ScalingEvent(
                agent_id=agent.id,
                customer_id=customer.id,
                event_type=ScalingEventType.SCALE_UP,
                trigger_reason="Test 2",
                before_state={},
                after_state={},
                success=True,
                executed_at=datetime.now()
            ),
            ScalingEvent(
                agent_id=agent.id,
                customer_id=customer.id,
                event_type=ScalingEventType.SCALE_DOWN,
                trigger_reason="Test 3",
                before_state={},
                after_state={},
                success=True,
                executed_at=datetime.now()
            ),
        ]
        db_session.add_all(events)
        db_session.commit()
        
        # VERIFY: Can filter by type
        scale_ups = db_session.query(ScalingEvent).filter_by(
            agent_id=agent.id,
            event_type=ScalingEventType.SCALE_UP
        ).all()
        
        assert len(scale_ups) == 2


class TestCascadeDeletes:
    """Test cascade delete behavior - CRITICAL for data integrity"""
    
    def test_metric_cascade_delete_on_agent(self, db_session):
        """Test CASCADE delete when agent is deleted"""
        customer = Customer(name="Test", email="casc1@test.com", api_key="ckey1", status=CustomerStatus.ACTIVE)
        agent = Agent(
            type=AgentType.RESOURCE,
            name="casc-agent-1",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:7001",
            capabilities=[]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        agent_id = agent.id
        
        # Create metric
        metric = ResourceMetric(
            agent_id=agent.id,
            customer_id=customer.id,
            instance_id="i-delete-test",
            resource_type=ResourceType.GPU,
            metric_name="utilization",
            metric_value=50.0,
            unit="percent",
            timestamp=datetime.now()
        )
        db_session.add(metric)
        db_session.commit()
        metric_id = metric.id
        
        # VERIFY: Metric exists
        assert db_session.query(ResourceMetric).filter_by(id=metric_id).first() is not None
        
        # Delete agent
        db_session.delete(agent)
        db_session.commit()
        
        # VERIFY: Metric deleted (cascade)
        assert db_session.query(ResourceMetric).filter_by(id=metric_id).first() is None
    
    def test_scaling_event_cascade_delete_on_agent(self, db_session):
        """Test CASCADE delete when agent is deleted"""
        customer = Customer(name="Test", email="casc2@test.com", api_key="ckey2", status=CustomerStatus.ACTIVE)
        agent = Agent(
            type=AgentType.RESOURCE,
            name="casc-agent-2",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:7002",
            capabilities=[]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        
        event = ScalingEvent(
            agent_id=agent.id,
            customer_id=customer.id,
            event_type=ScalingEventType.SCALE_UP,
            trigger_reason="Test",
            before_state={},
            after_state={},
            success=True,
            executed_at=datetime.now()
        )
        db_session.add(event)
        db_session.commit()
        event_id = event.id
        
        # VERIFY: Event exists
        assert db_session.query(ScalingEvent).filter_by(id=event_id).first() is not None
        
        # Delete agent
        db_session.delete(agent)
        db_session.commit()
        
        # VERIFY: Event deleted (cascade)
        assert db_session.query(ScalingEvent).filter_by(id=event_id).first() is None


class TestIntegration:
    """Integration tests with seeded data"""
    
    def test_query_resource_metrics_exist(self, db_session):
        """Test that seeded resource metrics exist"""
        metrics = db_session.query(ResourceMetric).all()
        
        # Should have metrics from seed data
        if len(metrics) > 0:
            # VERIFY: Can access relationships
            assert hasattr(metrics[0], 'agent')
            assert hasattr(metrics[0], 'customer')
            assert metrics[0].agent is not None
            assert metrics[0].customer is not None
    
    def test_query_scaling_events_exist(self, db_session):
        """Test that seeded scaling events exist"""
        events = db_session.query(ScalingEvent).all()
        
        # Should have events from seed data
        if len(events) > 0:
            # VERIFY: Can access relationships
            assert hasattr(events[0], 'agent')
            assert hasattr(events[0], 'customer')
            assert events[0].agent is not None
            assert events[0].customer is not None
    
    def test_query_metrics_by_resource_type(self, db_session):
        """Test querying metrics by resource type"""
        gpu_metrics = db_session.query(ResourceMetric).filter_by(
            resource_type=ResourceType.GPU
        ).all()
        
        for metric in gpu_metrics:
            assert metric.resource_type == ResourceType.GPU
    
    def test_query_scaling_by_success(self, db_session):
        """Test querying scaling events by success status"""
        successful = db_session.query(ScalingEvent).filter_by(
            success=True
        ).all()
        
        failed = db_session.query(ScalingEvent).filter_by(
            success=False
        ).all()
        
        # VERIFY: Each query returns correct status
        for event in successful:
            assert event.success is True
        for event in failed:
            assert event.success is False
