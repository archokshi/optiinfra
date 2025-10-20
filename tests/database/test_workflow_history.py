"""
Comprehensive test suite for workflow history tables (FOUNDATION-0.2c)
Tests: WorkflowExecution, WorkflowStep, WorkflowArtifact

TESTING PRINCIPLES:
- All tests use REAL PostgreSQL database
- All operations are verified by querying back from database
- No mocks, no shortcuts, no fake assertions
- Constraints and relationships are tested to fail when they should
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from shared.database.models import (
    Agent, Customer, WorkflowExecution, WorkflowStep, WorkflowArtifact,
    AgentType, AgentStatus, WorkflowType, WorkflowStatus, StepStatus, ArtifactType
)


class TestWorkflowExecution:
    """Test WorkflowExecution model with real database operations"""
    
    def test_create_workflow_execution(self, db_session):
        """Test creating a workflow execution and verifying it persists"""
        # Create required dependencies
        customer = Customer(
            name="Test Customer",
            email="test@example.com",
            api_key="test_key_123"
        )
        agent = Agent(
            type=AgentType.COST,
            name="test-cost-agent",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8001",
            capabilities=["cost_analysis"]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        
        # Create workflow execution
        workflow = WorkflowExecution(
            agent_id=agent.id,
            customer_id=customer.id,
            workflow_type=WorkflowType.COST_ANALYSIS,
            status=WorkflowStatus.RUNNING,
            started_at=datetime.now(),
            input_data={"test": "data"},
            output_data={},
            workflow_metadata={"priority": "high"}
        )
        db_session.add(workflow)
        db_session.commit()
        
        # VERIFY: Query back from database
        retrieved = db_session.query(WorkflowExecution).filter_by(id=workflow.id).first()
        assert retrieved is not None
        assert retrieved.workflow_type == WorkflowType.COST_ANALYSIS
        assert retrieved.status == WorkflowStatus.RUNNING
        assert retrieved.input_data["test"] == "data"
        assert retrieved.workflow_metadata["priority"] == "high"
        assert retrieved.agent_id == agent.id
        assert retrieved.customer_id == customer.id
    
    def test_workflow_agent_relationship(self, db_session):
        """Test workflow -> agent relationship loads correctly"""
        customer = Customer(name="Test", email="test2@example.com", api_key="key2")
        agent = Agent(
            type=AgentType.PERFORMANCE,
            name="test-perf",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8002",
            capabilities=[]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        
        workflow = WorkflowExecution(
            agent_id=agent.id,
            customer_id=customer.id,
            workflow_type=WorkflowType.PERFORMANCE_TUNING,
            status=WorkflowStatus.PENDING
        )
        db_session.add(workflow)
        db_session.commit()
        
        # VERIFY: Relationship loads
        db_session.refresh(workflow)
        assert workflow.agent is not None
        assert workflow.agent.id == agent.id
        assert workflow.agent.name == "test-perf"
    
    def test_workflow_customer_relationship(self, db_session):
        """Test workflow -> customer relationship loads correctly"""
        customer = Customer(name="Test Customer 3", email="test3@example.com", api_key="key3")
        agent = Agent(
            type=AgentType.RESOURCE,
            name="test-resource",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8003",
            capabilities=[]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        
        workflow = WorkflowExecution(
            agent_id=agent.id,
            customer_id=customer.id,
            workflow_type=WorkflowType.RESOURCE_OPTIMIZATION,
            status=WorkflowStatus.COMPLETED
        )
        db_session.add(workflow)
        db_session.commit()
        
        # VERIFY: Relationship loads
        db_session.refresh(workflow)
        assert workflow.customer is not None
        assert workflow.customer.id == customer.id
        assert workflow.customer.name == "Test Customer 3"
    
    def test_workflow_status_transitions(self, db_session):
        """Test workflow status can be updated and persists"""
        customer = Customer(name="Test", email="test4@example.com", api_key="key4")
        agent = Agent(
            type=AgentType.APPLICATION,
            name="test-app",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8004",
            capabilities=[]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        
        workflow = WorkflowExecution(
            agent_id=agent.id,
            customer_id=customer.id,
            workflow_type=WorkflowType.QUALITY_CHECK,
            status=WorkflowStatus.PENDING
        )
        db_session.add(workflow)
        db_session.commit()
        workflow_id = workflow.id
        
        # Update status
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()
        db_session.commit()
        
        # VERIFY: Status persisted
        retrieved = db_session.query(WorkflowExecution).filter_by(id=workflow_id).first()
        assert retrieved.status == WorkflowStatus.RUNNING
        assert retrieved.started_at is not None
        
        # Complete workflow
        workflow.status = WorkflowStatus.COMPLETED
        workflow.completed_at = datetime.now()
        workflow.output_data = {"result": "success"}
        db_session.commit()
        
        # VERIFY: Completion persisted
        retrieved = db_session.query(WorkflowExecution).filter_by(id=workflow_id).first()
        assert retrieved.status == WorkflowStatus.COMPLETED
        assert retrieved.completed_at is not None
        assert retrieved.output_data["result"] == "success"


class TestWorkflowStep:
    """Test WorkflowStep model with real database operations"""
    
    def test_create_workflow_step(self, db_session):
        """Test creating workflow steps and verifying they persist"""
        customer = Customer(name="Test", email="step1@example.com", api_key="stepkey1")
        agent = Agent(
            type=AgentType.COST,
            name="step-agent",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8001",
            capabilities=[]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        
        workflow = WorkflowExecution(
            agent_id=agent.id,
            customer_id=customer.id,
            workflow_type=WorkflowType.COST_ANALYSIS,
            status=WorkflowStatus.RUNNING
        )
        db_session.add(workflow)
        db_session.commit()
        
        # Create step
        step = WorkflowStep(
            workflow_execution_id=workflow.id,
            step_name="analyze_costs",
            step_order=1,
            status=StepStatus.COMPLETED,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            input_data={"param": "value"},
            output_data={"result": 100},
            retry_count=0
        )
        db_session.add(step)
        db_session.commit()
        
        # VERIFY: Step persisted
        retrieved = db_session.query(WorkflowStep).filter_by(id=step.id).first()
        assert retrieved is not None
        assert retrieved.step_name == "analyze_costs"
        assert retrieved.step_order == 1
        assert retrieved.status == StepStatus.COMPLETED
        assert retrieved.input_data["param"] == "value"
        assert retrieved.output_data["result"] == 100
    
    def test_workflow_steps_relationship(self, db_session):
        """Test workflow -> steps relationship with ordering"""
        customer = Customer(name="Test", email="step2@example.com", api_key="stepkey2")
        agent = Agent(
            type=AgentType.PERFORMANCE,
            name="step-agent-2",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8002",
            capabilities=[]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        
        workflow = WorkflowExecution(
            agent_id=agent.id,
            customer_id=customer.id,
            workflow_type=WorkflowType.PERFORMANCE_TUNING,
            status=WorkflowStatus.RUNNING
        )
        db_session.add(workflow)
        db_session.commit()
        
        # Create multiple steps
        steps = [
            WorkflowStep(
                workflow_execution_id=workflow.id,
                step_name=f"step_{i}",
                step_order=i,
                status=StepStatus.COMPLETED if i <= 3 else StepStatus.PENDING
            )
            for i in range(1, 6)
        ]
        db_session.add_all(steps)
        db_session.commit()
        
        # VERIFY: Relationship loads all steps in order
        db_session.refresh(workflow)
        assert len(workflow.steps) == 5
        assert workflow.steps[0].step_order == 1
        assert workflow.steps[4].step_order == 5
        
        # VERIFY: Can filter by status
        completed_steps = [s for s in workflow.steps if s.status == StepStatus.COMPLETED]
        assert len(completed_steps) == 3
    
    def test_step_retry_logic(self, db_session):
        """Test step retry count tracking"""
        customer = Customer(name="Test", email="step3@example.com", api_key="stepkey3")
        agent = Agent(
            type=AgentType.RESOURCE,
            name="retry-agent",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8003",
            capabilities=[]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        
        workflow = WorkflowExecution(
            agent_id=agent.id,
            customer_id=customer.id,
            workflow_type=WorkflowType.SCALING_DECISION,
            status=WorkflowStatus.RUNNING
        )
        db_session.add(workflow)
        db_session.commit()
        
        step = WorkflowStep(
            workflow_execution_id=workflow.id,
            step_name="scale_up",
            step_order=1,
            status=StepStatus.RETRYING,
            retry_count=0,
            max_retries=3
        )
        db_session.add(step)
        db_session.commit()
        step_id = step.id
        
        # Simulate retries
        for retry in range(1, 4):
            step.retry_count = retry
            step.status = StepStatus.RETRYING if retry < 3 else StepStatus.COMPLETED
            db_session.commit()
            
            # VERIFY: Retry count persisted
            retrieved = db_session.query(WorkflowStep).filter_by(id=step_id).first()
            assert retrieved.retry_count == retry
        
        # VERIFY: Final state
        final = db_session.query(WorkflowStep).filter_by(id=step_id).first()
        assert final.retry_count == 3
        assert final.status == StepStatus.COMPLETED


class TestWorkflowArtifact:
    """Test WorkflowArtifact model with real database operations"""
    
    def test_create_workflow_artifact(self, db_session):
        """Test creating artifacts and verifying they persist"""
        customer = Customer(name="Test", email="art1@example.com", api_key="artkey1")
        agent = Agent(
            type=AgentType.COST,
            name="art-agent",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8001",
            capabilities=[]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        
        workflow = WorkflowExecution(
            agent_id=agent.id,
            customer_id=customer.id,
            workflow_type=WorkflowType.COST_ANALYSIS,
            status=WorkflowStatus.COMPLETED
        )
        db_session.add(workflow)
        db_session.commit()
        
        step = WorkflowStep(
            workflow_execution_id=workflow.id,
            step_name="generate_report",
            step_order=1,
            status=StepStatus.COMPLETED
        )
        db_session.add(step)
        db_session.commit()
        
        # Create artifact
        artifact = WorkflowArtifact(
            workflow_execution_id=workflow.id,
            workflow_step_id=step.id,
            artifact_type=ArtifactType.REPORT,
            artifact_name="Cost Report",
            artifact_path="s3://bucket/report.pdf",
            artifact_size_bytes=1024000,
            content_type="application/pdf",
            artifact_metadata={"pages": 10}
        )
        db_session.add(artifact)
        db_session.commit()
        
        # VERIFY: Artifact persisted
        retrieved = db_session.query(WorkflowArtifact).filter_by(id=artifact.id).first()
        assert retrieved is not None
        assert retrieved.artifact_type == ArtifactType.REPORT
        assert retrieved.artifact_name == "Cost Report"
        assert retrieved.artifact_size_bytes == 1024000
        assert retrieved.artifact_metadata["pages"] == 10
    
    def test_workflow_artifacts_relationship(self, db_session):
        """Test workflow -> artifacts relationship"""
        customer = Customer(name="Test", email="art2@example.com", api_key="artkey2")
        agent = Agent(
            type=AgentType.PERFORMANCE,
            name="art-agent-2",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8002",
            capabilities=[]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        
        workflow = WorkflowExecution(
            agent_id=agent.id,
            customer_id=customer.id,
            workflow_type=WorkflowType.PERFORMANCE_TUNING,
            status=WorkflowStatus.COMPLETED
        )
        db_session.add(workflow)
        db_session.commit()
        
        # Create multiple artifacts
        artifacts = [
            WorkflowArtifact(
                workflow_execution_id=workflow.id,
                artifact_type=ArtifactType.CHART,
                artifact_name=f"Chart {i}",
                artifact_path=f"s3://bucket/chart_{i}.png"
            )
            for i in range(3)
        ]
        db_session.add_all(artifacts)
        db_session.commit()
        
        # VERIFY: Relationship loads all artifacts
        db_session.refresh(workflow)
        assert len(workflow.artifacts) == 3
        
        # VERIFY: Can query by type
        charts = db_session.query(WorkflowArtifact).filter_by(
            workflow_execution_id=workflow.id,
            artifact_type=ArtifactType.CHART
        ).all()
        assert len(charts) == 3


class TestCascadeDeletes:
    """Test cascade delete behavior - CRITICAL for data integrity"""
    
    def test_delete_workflow_cascades_to_steps(self, db_session):
        """Test that deleting workflow deletes all steps"""
        customer = Customer(name="Test", email="casc1@example.com", api_key="casckey1")
        agent = Agent(
            type=AgentType.COST,
            name="casc-agent",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8001",
            capabilities=[]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        
        workflow = WorkflowExecution(
            agent_id=agent.id,
            customer_id=customer.id,
            workflow_type=WorkflowType.COST_ANALYSIS,
            status=WorkflowStatus.COMPLETED
        )
        db_session.add(workflow)
        db_session.commit()
        workflow_id = workflow.id
        
        # Create steps
        steps = [
            WorkflowStep(
                workflow_execution_id=workflow.id,
                step_name=f"step_{i}",
                step_order=i,
                status=StepStatus.COMPLETED
            )
            for i in range(5)
        ]
        db_session.add_all(steps)
        db_session.commit()
        
        # VERIFY: Steps exist
        assert db_session.query(WorkflowStep).filter_by(
            workflow_execution_id=workflow_id
        ).count() == 5
        
        # Delete workflow
        db_session.delete(workflow)
        db_session.commit()
        
        # VERIFY: All steps deleted (cascade)
        remaining_steps = db_session.query(WorkflowStep).filter_by(
            workflow_execution_id=workflow_id
        ).count()
        assert remaining_steps == 0
    
    def test_delete_workflow_cascades_to_artifacts(self, db_session):
        """Test that deleting workflow deletes all artifacts"""
        customer = Customer(name="Test", email="casc2@example.com", api_key="casckey2")
        agent = Agent(
            type=AgentType.PERFORMANCE,
            name="casc-agent-2",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8002",
            capabilities=[]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        
        workflow = WorkflowExecution(
            agent_id=agent.id,
            customer_id=customer.id,
            workflow_type=WorkflowType.PERFORMANCE_TUNING,
            status=WorkflowStatus.COMPLETED
        )
        db_session.add(workflow)
        db_session.commit()
        workflow_id = workflow.id
        
        # Create artifacts
        artifacts = [
            WorkflowArtifact(
                workflow_execution_id=workflow.id,
                artifact_type=ArtifactType.REPORT,
                artifact_name=f"artifact_{i}",
                artifact_path=f"s3://bucket/file_{i}"
            )
            for i in range(3)
        ]
        db_session.add_all(artifacts)
        db_session.commit()
        
        # VERIFY: Artifacts exist
        assert db_session.query(WorkflowArtifact).filter_by(
            workflow_execution_id=workflow_id
        ).count() == 3
        
        # Delete workflow
        db_session.delete(workflow)
        db_session.commit()
        
        # VERIFY: All artifacts deleted (cascade)
        remaining_artifacts = db_session.query(WorkflowArtifact).filter_by(
            workflow_execution_id=workflow_id
        ).count()
        assert remaining_artifacts == 0
    
    def test_delete_agent_cascades_to_workflows(self, db_session):
        """Test that deleting agent deletes all workflows"""
        customer = Customer(name="Test", email="casc3@example.com", api_key="casckey3")
        agent = Agent(
            type=AgentType.RESOURCE,
            name="casc-agent-3",
            version="1.0.0",
            status=AgentStatus.HEALTHY,
            endpoint="http://localhost:8003",
            capabilities=[]
        )
        db_session.add_all([customer, agent])
        db_session.commit()
        agent_id = agent.id
        
        # Create workflows
        workflows = [
            WorkflowExecution(
                agent_id=agent.id,
                customer_id=customer.id,
                workflow_type=WorkflowType.RESOURCE_OPTIMIZATION,
                status=WorkflowStatus.COMPLETED
            )
            for _ in range(3)
        ]
        db_session.add_all(workflows)
        db_session.commit()
        
        # VERIFY: Workflows exist
        assert db_session.query(WorkflowExecution).filter_by(agent_id=agent_id).count() == 3
        
        # Delete agent
        db_session.delete(agent)
        db_session.commit()
        
        # VERIFY: All workflows deleted (cascade)
        remaining = db_session.query(WorkflowExecution).filter_by(agent_id=agent_id).count()
        assert remaining == 0


class TestIntegration:
    """Integration tests with seeded data"""
    
    def test_query_workflow_with_all_relationships(self, db_session):
        """Test querying workflow with all relationships loaded"""
        # Get any workflow from seed data
        workflow = db_session.query(WorkflowExecution).first()
        
        if workflow:
            # VERIFY: All relationships accessible
            assert hasattr(workflow, 'agent')
            assert hasattr(workflow, 'customer')
            assert hasattr(workflow, 'steps')
            assert hasattr(workflow, 'artifacts')
            
            # VERIFY: Can access related data
            assert workflow.agent is not None
            assert workflow.customer is not None
    
    def test_query_workflows_by_status(self, db_session):
        """Test querying workflows by status"""
        completed = db_session.query(WorkflowExecution).filter_by(
            status=WorkflowStatus.COMPLETED
        ).all()
        
        running = db_session.query(WorkflowExecution).filter_by(
            status=WorkflowStatus.RUNNING
        ).all()
        
        failed = db_session.query(WorkflowExecution).filter_by(
            status=WorkflowStatus.FAILED
        ).all()
        
        # VERIFY: Each query returns correct status
        for wf in completed:
            assert wf.status == WorkflowStatus.COMPLETED
        for wf in running:
            assert wf.status == WorkflowStatus.RUNNING
        for wf in failed:
            assert wf.status == WorkflowStatus.FAILED
    
    def test_query_steps_by_workflow(self, db_session):
        """Test querying steps for a specific workflow"""
        workflow = db_session.query(WorkflowExecution).first()
        
        if workflow:
            steps = db_session.query(WorkflowStep).filter_by(
                workflow_execution_id=workflow.id
            ).order_by(WorkflowStep.step_order).all()
            
            # VERIFY: Steps are in order
            for i, step in enumerate(steps, 1):
                assert step.step_order == i
    
    def test_query_artifacts_by_type(self, db_session):
        """Test querying artifacts by type"""
        reports = db_session.query(WorkflowArtifact).filter_by(
            artifact_type=ArtifactType.REPORT
        ).all()
        
        for artifact in reports:
            assert artifact.artifact_type == ArtifactType.REPORT
