"""
Create core schema tables

Revision ID: 001_core_schema
Revises: 
Create Date: 2025-10-19 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_core_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create core schema tables"""
    
    # Create ENUM types
    op.execute("""
        CREATE TYPE customerplan AS ENUM ('free', 'startup', 'enterprise');
        CREATE TYPE customerstatus AS ENUM ('active', 'suspended', 'churned');
        CREATE TYPE agenttype AS ENUM ('orchestrator', 'cost', 'performance', 'resource', 'application');
        CREATE TYPE agentstatus AS ENUM ('starting', 'healthy', 'degraded', 'failed', 'stopped');
        CREATE TYPE eventseverity AS ENUM ('info', 'warning', 'error', 'critical');
        CREATE TYPE recommendationpriority AS ENUM ('low', 'medium', 'high', 'critical');
        CREATE TYPE recommendationstatus AS ENUM ('pending', 'approved', 'rejected', 'executing', 'completed', 'failed', 'rolled_back');
        CREATE TYPE approvalstatus AS ENUM ('pending', 'approved', 'rejected');
        CREATE TYPE optimizationstatus AS ENUM ('queued', 'executing', 'completed', 'failed', 'rolled_back');
    """)
    
    # Create customers table
    op.create_table(
        'customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('api_key', sa.String(64), nullable=False, unique=True),
        sa.Column('plan', postgresql.ENUM(name='customerplan', create_type=False), nullable=False, server_default='free'),
        sa.Column('status', postgresql.ENUM(name='customerstatus', create_type=False), nullable=False, server_default='active'),
        sa.Column('metadata', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes for customers
    op.create_index('idx_customer_email', 'customers', ['email'])
    op.create_index('idx_customer_api_key', 'customers', ['api_key'])
    op.create_index('idx_customer_status', 'customers', ['status'])
    
    # Create agents table
    op.create_table(
        'agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('type', postgresql.ENUM(name='agenttype', create_type=False), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('version', sa.String(50), nullable=True),
        sa.Column('status', postgresql.ENUM(name='agentstatus', create_type=False), nullable=False, server_default='starting'),
        sa.Column('endpoint', sa.String(255), nullable=True),
        sa.Column('capabilities', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('metadata', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('last_heartbeat', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes and constraints for agents
    op.create_index('idx_agent_type', 'agents', ['type'])
    op.create_index('idx_agent_status', 'agents', ['status'])
    op.create_index('idx_agent_heartbeat', 'agents', ['last_heartbeat'])
    op.create_unique_constraint('uq_agent_type_name', 'agents', ['type', 'name'])
    
    # Create events table
    op.create_table(
        'events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('severity', postgresql.ENUM(name='eventseverity', create_type=False), nullable=False, server_default='info'),
        sa.Column('data', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='SET NULL'),
    )
    
    # Create indexes for events
    op.create_index('idx_event_customer', 'events', ['customer_id'])
    op.create_index('idx_event_agent', 'events', ['agent_id'])
    op.create_index('idx_event_type', 'events', ['event_type'])
    op.create_index('idx_event_severity', 'events', ['severity'])
    op.create_index('idx_event_created', 'events', ['created_at'])
    op.create_index('idx_event_customer_created', 'events', ['customer_id', 'created_at'])
    
    # Create recommendations table
    op.create_table(
        'recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(100), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('estimated_savings', sa.DECIMAL(10, 2), nullable=True),
        sa.Column('estimated_improvement', sa.DECIMAL(10, 2), nullable=True),
        sa.Column('confidence_score', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('priority', postgresql.ENUM(name='recommendationpriority', create_type=False), nullable=False, server_default='medium'),
        sa.Column('status', postgresql.ENUM(name='recommendationstatus', create_type=False), nullable=False, server_default='pending'),
        sa.Column('data', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.CheckConstraint('confidence_score >= 0.0 AND confidence_score <= 1.0', name='check_confidence_range'),
    )
    
    # Create indexes for recommendations
    op.create_index('idx_rec_customer', 'recommendations', ['customer_id'])
    op.create_index('idx_rec_agent', 'recommendations', ['agent_id'])
    op.create_index('idx_rec_type', 'recommendations', ['type'])
    op.create_index('idx_rec_priority', 'recommendations', ['priority'])
    op.create_index('idx_rec_status', 'recommendations', ['status'])
    op.create_index('idx_rec_created', 'recommendations', ['created_at'])
    op.create_index('idx_rec_customer_status', 'recommendations', ['customer_id', 'status'])
    
    # Create approvals table
    op.create_table(
        'approvals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('approved_by', sa.String(255), nullable=False),
        sa.Column('status', postgresql.ENUM(name='approvalstatus', create_type=False), nullable=False, server_default='pending'),
        sa.Column('comment', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['recommendation_id'], ['recommendations.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for approvals
    op.create_index('idx_approval_rec', 'approvals', ['recommendation_id'])
    op.create_index('idx_approval_status', 'approvals', ['status'])
    
    # Create optimizations table
    op.create_table(
        'optimizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('recommendation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', postgresql.ENUM(name='optimizationstatus', create_type=False), nullable=False, server_default='queued'),
        sa.Column('progress', sa.Integer, nullable=False, server_default='0'),
        sa.Column('result', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('error', sa.Text, nullable=True),
        sa.Column('actual_savings', sa.DECIMAL(10, 2), nullable=True),
        sa.Column('actual_improvement', sa.DECIMAL(10, 2), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rolled_back_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['recommendation_id'], ['recommendations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.CheckConstraint('progress >= 0 AND progress <= 100', name='check_progress_range'),
    )
    
    # Create indexes for optimizations
    op.create_index('idx_opt_rec', 'optimizations', ['recommendation_id'])
    op.create_index('idx_opt_customer', 'optimizations', ['customer_id'])
    op.create_index('idx_opt_agent', 'optimizations', ['agent_id'])
    op.create_index('idx_opt_status', 'optimizations', ['status'])
    op.create_index('idx_opt_customer_status', 'optimizations', ['customer_id', 'status'])


def downgrade():
    """Drop all tables and types"""
    
    # Drop tables in reverse order (respect foreign keys)
    op.drop_table('optimizations')
    op.drop_table('approvals')
    op.drop_table('recommendations')
    op.drop_table('events')
    op.drop_table('agents')
    op.drop_table('customers')
    
    # Drop ENUM types
    op.execute("""
        DROP TYPE IF EXISTS optimizationstatus;
        DROP TYPE IF EXISTS approvalstatus;
        DROP TYPE IF EXISTS recommendationstatus;
        DROP TYPE IF EXISTS recommendationpriority;
        DROP TYPE IF EXISTS eventseverity;
        DROP TYPE IF EXISTS agentstatus;
        DROP TYPE IF EXISTS agenttype;
        DROP TYPE IF EXISTS customerstatus;
        DROP TYPE IF EXISTS customerplan;
    """)
