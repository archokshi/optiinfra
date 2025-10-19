"""
Tests for core database schema.
"""
import pytest
import uuid
from datetime import datetime

from shared.database.models.core import (
    Customer, CustomerPlan, CustomerStatus,
    Agent, AgentType, AgentStatus,
    Event, EventSeverity,
    Recommendation, RecommendationPriority, RecommendationStatus,
    Approval, ApprovalStatus,
    Optimization, OptimizationStatus,
)


class TestCustomerModel:
    """Tests for Customer model"""
    
    def test_create_customer(self, db_session):
        """Test creating a customer"""
        customer = Customer(
            name="Test Corp",
            email="test@example.com",
            api_key="test_key_123",
            plan=CustomerPlan.STARTUP,
            status=CustomerStatus.ACTIVE,
        )
        
        db_session.add(customer)
        db_session.commit()
        
        assert customer.id is not None
        assert customer.name == "Test Corp"
        assert customer.email == "test@example.com"
        assert customer.plan == CustomerPlan.STARTUP
        assert customer.status == CustomerStatus.ACTIVE
        assert customer.created_at is not None
        assert customer.updated_at is not None
    
    def test_customer_unique_email(self, db_session):
        """Test that customer emails must be unique"""
        customer1 = Customer(
            name="Corp 1",
            email="same@example.com",
            api_key="key1",
        )
        customer2 = Customer(
            name="Corp 2",
            email="same@example.com",
            api_key="key2",
        )
        
        db_session.add(customer1)
        db_session.commit()
        
        db_session.add(customer2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
    
    def test_customer_metadata(self, db_session):
        """Test customer metadata JSONB field"""
        customer = Customer(
            name="Meta Corp",
            email="meta@example.com",
            api_key="meta_key",
            customer_metadata={"industry": "tech", "size": "100-500"},
        )
        
        db_session.add(customer)
        db_session.commit()
        
        assert customer.customer_metadata["industry"] == "tech"
        assert customer.customer_metadata["size"] == "100-500"


class TestAgentModel:
    """Tests for Agent model"""
    
    def test_create_agent(self, db_session):
        """Test creating an agent"""
        agent = Agent(
            type=AgentType.COST,
            name="cost-agent-test",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8001",
            capabilities=["spot_migration", "right_sizing"],
        )
        
        db_session.add(agent)
        db_session.commit()
        
        assert agent.id is not None
        assert agent.type == AgentType.COST
        assert agent.name == "cost-agent-test"
        assert agent.status == AgentStatus.HEALTHY
        assert "spot_migration" in agent.capabilities
    
    def test_agent_heartbeat(self, db_session):
        """Test agent heartbeat timestamp"""
        agent = Agent(
            type=AgentType.ORCHESTRATOR,
            name="orchestrator-test",
            last_heartbeat=datetime.utcnow(),
        )
        
        db_session.add(agent)
        db_session.commit()
        
        assert agent.last_heartbeat is not None
        assert isinstance(agent.last_heartbeat, datetime)


class TestEventModel:
    """Tests for Event model"""
    
    def test_create_event(self, db_session):
        """Test creating an event"""
        # Create customer and agent first
        customer = Customer(name="Test", email="test@e.com", api_key="key")
        agent = Agent(type=AgentType.COST, name="agent")
        
        db_session.add_all([customer, agent])
        db_session.commit()
        
        # Create event
        event = Event(
            customer_id=customer.id,
            agent_id=agent.id,
            event_type="test_event",
            severity=EventSeverity.INFO,
            data={"test": "data"},
        )
        
        db_session.add(event)
        db_session.commit()
        
        assert event.id is not None
        assert event.customer_id == customer.id
        assert event.agent_id == agent.id
        assert event.event_type == "test_event"
        assert event.data["test"] == "data"
    
    def test_event_cascade_delete(self, db_session):
        """Test that events are deleted when customer is deleted"""
        customer = Customer(name="Test", email="test@e.com", api_key="key")
        db_session.add(customer)
        db_session.commit()
        
        event = Event(
            customer_id=customer.id,
            event_type="test",
            severity=EventSeverity.INFO,
            data={},
        )
        db_session.add(event)
        db_session.commit()
        
        event_id = event.id
        
        # Delete customer
        db_session.delete(customer)
        db_session.commit()
        
        # Event should be deleted
        assert db_session.query(Event).filter_by(id=event_id).first() is None


class TestRecommendationModel:
    """Tests for Recommendation model"""
    
    def test_create_recommendation(self, db_session):
        """Test creating a recommendation"""
        customer = Customer(name="Test", email="test@e.com", api_key="key")
        agent = Agent(type=AgentType.COST, name="agent")
        
        db_session.add_all([customer, agent])
        db_session.commit()
        
        rec = Recommendation(
            customer_id=customer.id,
            agent_id=agent.id,
            type="spot_migration",
            title="Test Recommendation",
            description="Test description",
            estimated_savings=1000.00,
            confidence_score=0.9,
            priority=RecommendationPriority.HIGH,
            status=RecommendationStatus.PENDING,
        )
        
        db_session.add(rec)
        db_session.commit()
        
        assert rec.id is not None
        assert rec.type == "spot_migration"
        assert float(rec.estimated_savings) == 1000.00
        assert rec.confidence_score == 0.9


class TestApprovalModel:
    """Tests for Approval model"""
    
    def test_create_approval(self, db_session):
        """Test creating an approval"""
        customer = Customer(name="Test", email="test@e.com", api_key="key")
        agent = Agent(type=AgentType.COST, name="agent")
        db_session.add_all([customer, agent])
        db_session.commit()
        
        rec = Recommendation(
            customer_id=customer.id,
            agent_id=agent.id,
            type="test",
            title="Test",
        )
        db_session.add(rec)
        db_session.commit()
        
        approval = Approval(
            recommendation_id=rec.id,
            approved_by="admin@example.com",
            status=ApprovalStatus.APPROVED,
            comment="Looks good!",
        )
        
        db_session.add(approval)
        db_session.commit()
        
        assert approval.id is not None
        assert approval.recommendation_id == rec.id
        assert approval.status == ApprovalStatus.APPROVED


class TestOptimizationModel:
    """Tests for Optimization model"""
    
    def test_create_optimization(self, db_session):
        """Test creating an optimization"""
        customer = Customer(name="Test", email="test@e.com", api_key="key")
        agent = Agent(type=AgentType.COST, name="agent")
        db_session.add_all([customer, agent])
        db_session.commit()
        
        rec = Recommendation(
            customer_id=customer.id,
            agent_id=agent.id,
            type="test",
            title="Test",
        )
        db_session.add(rec)
        db_session.commit()
        
        opt = Optimization(
            recommendation_id=rec.id,
            customer_id=customer.id,
            agent_id=agent.id,
            status=OptimizationStatus.EXECUTING,
            progress=50,
            result={"phase": "10%"},
        )
        
        db_session.add(opt)
        db_session.commit()
        
        assert opt.id is not None
        assert opt.progress == 50
        assert opt.result["phase"] == "10%"


class TestRelationships:
    """Tests for model relationships"""
    
    def test_customer_recommendations_relationship(self, db_session):
        """Test customer -> recommendations relationship"""
        customer = Customer(name="Test", email="test@e.com", api_key="key")
        agent = Agent(type=AgentType.COST, name="agent")
        db_session.add_all([customer, agent])
        db_session.commit()
        
        rec1 = Recommendation(
            customer_id=customer.id,
            agent_id=agent.id,
            type="test1",
            title="Test 1",
        )
        rec2 = Recommendation(
            customer_id=customer.id,
            agent_id=agent.id,
            type="test2",
            title="Test 2",
        )
        
        db_session.add_all([rec1, rec2])
        db_session.commit()
        
        # Test relationship
        assert len(customer.recommendations) == 2
        assert rec1 in customer.recommendations
        assert rec2 in customer.recommendations


class TestDatabaseIntegration:
    """Integration tests for database operations"""
    
    def test_seed_data(self, db_session):
        """Test that seed data can be inserted"""
        from shared.database.seeds.core_seed import seed_core_data
        
        result = seed_core_data(db_session)
        
        assert len(result["customers"]) == 3
        assert len(result["agents"]) == 5
        assert len(result["events"]) == 3
        assert len(result["recommendations"]) == 3
        
        # Verify data was actually inserted
        assert db_session.query(Customer).count() == 3
        assert db_session.query(Agent).count() == 5
    
    def test_query_with_filters(self, db_session):
        """Test querying with filters"""
        from shared.database.seeds.core_seed import seed_core_data
        
        seed_core_data(db_session)
        
        # Query active customers
        active_customers = db_session.query(Customer).filter_by(
            status=CustomerStatus.ACTIVE
        ).all()
        assert len(active_customers) > 0
        
        # Query cost agents
        cost_agents = db_session.query(Agent).filter_by(
            type=AgentType.COST
        ).all()
        assert len(cost_agents) > 0
