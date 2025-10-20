"""
Test suite for agent state tables (FOUNDATION-0.2b)
Tests: AgentConfig, AgentState, AgentCapability, AgentMetric
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from shared.database.models import (
    Agent, AgentConfig, AgentState, AgentCapability, AgentMetric,
    AgentType, AgentStatus, ConfigType, AgentStatusDetail, MetricType
)


class TestAgentConfig:
    """Test AgentConfig model and relationships"""
    
    def test_create_agent_config(self, db_session):
        """Test creating an agent config"""
        # Create test agent
        agent = Agent(
            type=AgentType.COST,
            name="test-cost-agent",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8001",
            capabilities=["cost_analysis"]
        )
        db_session.add(agent)
        db_session.commit()
        
        # Create config
        config = AgentConfig(
            agent_id=agent.id,
            config_key="max_cost_threshold",
            config_value="5000",
            config_type=ConfigType.INTEGER,
            description="Maximum cost threshold"
        )
        db_session.add(config)
        db_session.commit()
        
        assert config.id is not None
        assert config.config_key == "max_cost_threshold"
        assert config.config_value == "5000"
        assert config.config_type == ConfigType.INTEGER
        assert config.created_at is not None
        assert config.updated_at is not None
    
    def test_agent_config_relationship(self, db_session):
        """Test agent -> configs relationship"""
        agent = Agent(
            type=AgentType.COST,
            name="test-agent-rel",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8001",
            capabilities=[]
        )
        db_session.add(agent)
        db_session.commit()
        
        config = AgentConfig(
            agent_id=agent.id,
            config_key="test_key",
            config_value="test_value",
            config_type=ConfigType.STRING
        )
        db_session.add(config)
        db_session.commit()
        
        # Refresh agent to load relationships
        db_session.refresh(agent)
        
        assert len(agent.configs) >= 1
        assert config in agent.configs
    
    def test_agent_config_unique_constraint(self, db_session):
        """Test unique constraint on agent_id + config_key"""
        agent = Agent(
            type=AgentType.COST,
            name="test-unique",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8001",
            capabilities=[]
        )
        db_session.add(agent)
        db_session.commit()
        
        config1 = AgentConfig(
            agent_id=agent.id,
            config_key="duplicate_key",
            config_value="value1",
            config_type=ConfigType.STRING
        )
        db_session.add(config1)
        db_session.commit()
        
        # Try to add duplicate
        config2 = AgentConfig(
            agent_id=agent.id,
            config_key="duplicate_key",
            config_value="value2",
            config_type=ConfigType.STRING
        )
        db_session.add(config2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestAgentState:
    """Test AgentState model and real-time state tracking"""
    
    def test_create_agent_state(self, db_session):
        """Test creating an agent state"""
        agent = Agent(
            type=AgentType.PERFORMANCE,
            name="test-perf-agent",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8002",
            capabilities=[]
        )
        db_session.add(agent)
        db_session.commit()
        
        state = AgentState(
            agent_id=agent.id,
            current_status=AgentStatusDetail.BUSY,
            active_workflows=["workflow_123"],
            locks={"resource1": True},
            last_activity=datetime.utcnow(),
            resource_usage={"cpu": 45.5, "memory": 2048}
        )
        db_session.add(state)
        db_session.commit()
        
        assert state.id is not None
        assert state.current_status == AgentStatusDetail.BUSY
        assert "workflow_123" in state.active_workflows
        assert state.locks["resource1"] is True
        assert state.resource_usage["cpu"] == 45.5
    
    def test_agent_state_one_to_one(self, db_session):
        """Test one-to-one relationship between agent and state"""
        agent = Agent(
            type=AgentType.RESOURCE,
            name="test-resource-agent",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8003",
            capabilities=[]
        )
        db_session.add(agent)
        db_session.commit()
        
        state = AgentState(
            agent_id=agent.id,
            current_status=AgentStatusDetail.IDLE,
            active_workflows=[],
            locks={},
            last_activity=datetime.utcnow()
        )
        db_session.add(state)
        db_session.commit()
        
        # Refresh to load relationship
        db_session.refresh(agent)
        
        assert agent.state is not None
        assert agent.state.agent_id == agent.id
    
    def test_agent_state_jsonb_fields(self, db_session):
        """Test JSONB fields store complex data"""
        agent = Agent(
            type=AgentType.APPLICATION,
            name="test-app-agent",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8004",
            capabilities=[]
        )
        db_session.add(agent)
        db_session.commit()
        
        complex_data = {
            "workflow_id": "wf_001",
            "started_at": datetime.utcnow().isoformat(),
            "metrics": {"requests": 150, "errors": 2}
        }
        
        state = AgentState(
            agent_id=agent.id,
            current_status=AgentStatusDetail.PROCESSING,
            active_workflows=["wf_001", "wf_002"],
            locks={"db": True, "cache": False},
            last_activity=datetime.utcnow(),
            state_metadata=complex_data
        )
        db_session.add(state)
        db_session.commit()
        
        # Retrieve and verify
        retrieved = db_session.query(AgentState).filter_by(id=state.id).first()
        assert retrieved.state_metadata["workflow_id"] == "wf_001"
        assert retrieved.state_metadata["metrics"]["requests"] == 150


class TestAgentCapability:
    """Test AgentCapability model and versioning"""
    
    def test_create_agent_capability(self, db_session):
        """Test creating an agent capability"""
        agent = Agent(
            type=AgentType.COST,
            name="test-cap-agent",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8001",
            capabilities=[]
        )
        db_session.add(agent)
        db_session.commit()
        
        capability = AgentCapability(
            agent_id=agent.id,
            capability_name="advanced_cost_analysis",
            capability_version="2.1.0",
            description="Advanced cost analysis with ML",
            config={
                "model": "cost_predictor_v2",
                "confidence_threshold": 0.85
            },
            enabled=True
        )
        db_session.add(capability)
        db_session.commit()
        
        assert capability.id is not None
        assert capability.capability_name == "advanced_cost_analysis"
        assert capability.capability_version == "2.1.0"
        assert capability.enabled is True
        assert capability.config["model"] == "cost_predictor_v2"
    
    def test_agent_capability_relationship(self, db_session):
        """Test agent -> capability_details relationship"""
        agent = Agent(
            type=AgentType.PERFORMANCE,
            name="test-cap-rel",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8002",
            capabilities=[]
        )
        db_session.add(agent)
        db_session.commit()
        
        cap1 = AgentCapability(
            agent_id=agent.id,
            capability_name="kv_cache_tuning",
            capability_version="1.0.0",
            enabled=True
        )
        cap2 = AgentCapability(
            agent_id=agent.id,
            capability_name="batch_optimization",
            capability_version="1.0.0",
            enabled=True
        )
        db_session.add_all([cap1, cap2])
        db_session.commit()
        
        # Refresh to load relationships
        db_session.refresh(agent)
        
        assert len(agent.capability_details) >= 2
    
    def test_capability_enable_disable(self, db_session):
        """Test enabling/disabling capabilities"""
        agent = Agent(
            type=AgentType.RESOURCE,
            name="test-enable",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8003",
            capabilities=[]
        )
        db_session.add(agent)
        db_session.commit()
        
        capability = AgentCapability(
            agent_id=agent.id,
            capability_name="auto_scaling",
            capability_version="1.0.0",
            enabled=True
        )
        db_session.add(capability)
        db_session.commit()
        
        # Disable
        capability.enabled = False
        db_session.commit()
        
        # Verify
        retrieved = db_session.query(AgentCapability).filter_by(id=capability.id).first()
        assert retrieved.enabled is False


class TestAgentMetric:
    """Test AgentMetric model and time-series data"""
    
    def test_create_agent_metric(self, db_session):
        """Test creating an agent metric"""
        agent = Agent(
            type=AgentType.COST,
            name="test-metric-agent",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8001",
            capabilities=[]
        )
        db_session.add(agent)
        db_session.commit()
        
        now = datetime.utcnow()
        metric = AgentMetric(
            agent_id=agent.id,
            metric_name="cost_savings_usd",
            metric_value=45000.50,
            metric_type=MetricType.GAUGE,
            tags={"period": "monthly", "customer_count": 5},
            recorded_at=now
        )
        db_session.add(metric)
        db_session.commit()
        
        assert metric.id is not None
        assert metric.metric_name == "cost_savings_usd"
        assert metric.metric_value == 45000.50
        assert metric.metric_type == MetricType.GAUGE
        assert metric.tags["period"] == "monthly"
    
    def test_agent_metric_relationship(self, db_session):
        """Test agent -> metrics relationship"""
        agent = Agent(
            type=AgentType.PERFORMANCE,
            name="test-metric-rel",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8002",
            capabilities=[]
        )
        db_session.add(agent)
        db_session.commit()
        
        metric = AgentMetric(
            agent_id=agent.id,
            metric_name="latency_p95",
            metric_value=250.5,
            metric_type=MetricType.GAUGE,
            recorded_at=datetime.utcnow()
        )
        db_session.add(metric)
        db_session.commit()
        
        # Refresh to load relationships
        db_session.refresh(agent)
        
        assert len(agent.metrics) >= 1
        assert metric in agent.metrics
    
    def test_metric_time_series(self, db_session):
        """Test storing time-series metrics"""
        agent = Agent(
            type=AgentType.RESOURCE,
            name="test-timeseries",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8003",
            capabilities=[]
        )
        db_session.add(agent)
        db_session.commit()
        
        base_time = datetime.utcnow()
        
        # Create hourly metrics
        metrics = []
        for hour in range(5):
            metric = AgentMetric(
                agent_id=agent.id,
                metric_name="gpu_utilization",
                metric_value=70.0 + hour * 2,
                metric_type=MetricType.GAUGE,
                tags={"hour": hour},
                recorded_at=base_time + timedelta(hours=hour)
            )
            metrics.append(metric)
        
        db_session.add_all(metrics)
        db_session.commit()
        
        # Query time range
        start_time = base_time
        end_time = base_time + timedelta(hours=5)
        
        retrieved = db_session.query(AgentMetric).filter(
            AgentMetric.agent_id == agent.id,
            AgentMetric.metric_name == "gpu_utilization",
            AgentMetric.recorded_at >= start_time,
            AgentMetric.recorded_at <= end_time
        ).order_by(AgentMetric.recorded_at).all()
        
        assert len(retrieved) == 5
        assert retrieved[0].metric_value == 70.0
        assert retrieved[4].metric_value == 78.0


class TestCascadeDeletes:
    """Test cascade delete behavior"""
    
    def test_agent_delete_cascades_to_state_tables(self, db_session):
        """Test that deleting an agent cascades to all state tables"""
        # Create agent
        agent = Agent(
            type=AgentType.COST,
            name="test-cascade",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8001",
            capabilities=[]
        )
        db_session.add(agent)
        db_session.commit()
        agent_id = agent.id
        
        # Create related records
        config = AgentConfig(
            agent_id=agent_id,
            config_key="test",
            config_value="test",
            config_type=ConfigType.STRING
        )
        state = AgentState(
            agent_id=agent_id,
            current_status=AgentStatusDetail.IDLE,
            active_workflows=[],
            locks={},
            last_activity=datetime.utcnow()
        )
        capability = AgentCapability(
            agent_id=agent_id,
            capability_name="test_cap",
            capability_version="1.0.0",
            enabled=True
        )
        metric = AgentMetric(
            agent_id=agent_id,
            metric_name="test_metric",
            metric_value=100.0,
            metric_type=MetricType.COUNTER,
            recorded_at=datetime.utcnow()
        )
        
        db_session.add_all([config, state, capability, metric])
        db_session.commit()
        
        # Delete agent
        db_session.delete(agent)
        db_session.commit()
        
        # Verify all related records are deleted
        assert db_session.query(AgentConfig).filter_by(agent_id=agent_id).count() == 0
        assert db_session.query(AgentState).filter_by(agent_id=agent_id).count() == 0
        assert db_session.query(AgentCapability).filter_by(agent_id=agent_id).count() == 0
        assert db_session.query(AgentMetric).filter_by(agent_id=agent_id).count() == 0


class TestDatabaseIntegration:
    """Integration tests with seeded data"""
    
    def test_query_agent_with_all_state_data(self, db_session):
        """Test querying agent with all state relationships"""
        # Get any agent from seed data
        agent = db_session.query(Agent).first()
        
        if agent:
            # Should be able to access all relationships
            assert hasattr(agent, 'configs')
            assert hasattr(agent, 'state')
            assert hasattr(agent, 'capability_details')
            assert hasattr(agent, 'metrics')
    
    def test_query_configs_by_type(self, db_session):
        """Test querying configs by type"""
        integer_configs = db_session.query(AgentConfig).filter_by(
            config_type=ConfigType.INTEGER
        ).all()
        
        for config in integer_configs:
            assert config.config_type == ConfigType.INTEGER
    
    def test_query_active_capabilities(self, db_session):
        """Test querying only enabled capabilities"""
        enabled_caps = db_session.query(AgentCapability).filter_by(
            enabled=True
        ).all()
        
        for cap in enabled_caps:
            assert cap.enabled is True
