"""
Create agent state tables

Revision ID: 002_agent_state_tables
Revises: 001_core_schema
Create Date: 2025-10-19 16:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_agent_state_tables'
down_revision = '001_core_schema'
branch_labels = None
depends_on = None


def upgrade():
    """Create agent state tables"""
    
    # Create ENUM types
    op.execute("""
        CREATE TYPE configtype AS ENUM ('string', 'integer', 'float', 'boolean', 'json');
        CREATE TYPE agentstatusdetail AS ENUM ('idle', 'busy', 'processing', 'waiting', 'error');
        CREATE TYPE metrictype AS ENUM ('counter', 'gauge', 'histogram');
    """)
    
    # Create agent_configs table
    op.create_table(
        'agent_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('config_key', sa.String(255), nullable=False),
        sa.Column('config_value', sa.Text, nullable=False),
        sa.Column('config_type', postgresql.ENUM(name='configtype', create_type=False), nullable=False, server_default='string'),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create indexes for agent_configs
    op.create_index('idx_agent_config_agent', 'agent_configs', ['agent_id'])
    op.create_index('idx_agent_config_key', 'agent_configs', ['config_key'])
    op.create_index('idx_agent_config_agent_key', 'agent_configs', ['agent_id', 'config_key'])
    op.create_unique_constraint('uq_agent_config', 'agent_configs', ['agent_id', 'config_key'])
    
    # Create agent_states table
    op.create_table(
        'agent_states',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('current_status', postgresql.ENUM(name='agentstatusdetail', create_type=False), nullable=False, server_default='idle'),
        sa.Column('active_workflows', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('locks', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('resource_usage', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('metadata', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create indexes for agent_states
    op.create_index('idx_agent_state_agent', 'agent_states', ['agent_id'])
    op.create_index('idx_agent_state_status', 'agent_states', ['current_status'])
    op.create_index('idx_agent_state_activity', 'agent_states', ['last_activity'])
    
    # Create agent_capabilities table
    op.create_table(
        'agent_capabilities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('capability_name', sa.String(255), nullable=False),
        sa.Column('capability_version', sa.String(50), nullable=False, server_default='1.0.0'),
        sa.Column('enabled', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('config', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create indexes for agent_capabilities
    op.create_index('idx_agent_cap_agent', 'agent_capabilities', ['agent_id'])
    op.create_index('idx_agent_cap_name', 'agent_capabilities', ['capability_name'])
    op.create_index('idx_agent_cap_enabled', 'agent_capabilities', ['enabled'])
    op.create_index('idx_agent_cap_agent_name', 'agent_capabilities', ['agent_id', 'capability_name'])
    op.create_unique_constraint('uq_agent_capability', 'agent_capabilities', ['agent_id', 'capability_name'])
    
    # Create agent_metrics table
    op.create_table(
        'agent_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('metric_name', sa.String(255), nullable=False),
        sa.Column('metric_value', sa.Float, nullable=False),
        sa.Column('metric_type', postgresql.ENUM(name='metrictype', create_type=False), nullable=False, server_default='gauge'),
        sa.Column('tags', postgresql.JSONB, nullable=True, server_default='{}'),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create indexes for agent_metrics
    op.create_index('idx_agent_metric_agent', 'agent_metrics', ['agent_id'])
    op.create_index('idx_agent_metric_name', 'agent_metrics', ['metric_name'])
    op.create_index('idx_agent_metric_recorded', 'agent_metrics', ['recorded_at'])
    op.create_index('idx_agent_metric_agent_name', 'agent_metrics', ['agent_id', 'metric_name'])
    op.create_index('idx_agent_metric_agent_recorded', 'agent_metrics', ['agent_id', 'recorded_at'])


def downgrade():
    """Drop agent state tables"""
    
    # Drop tables in reverse order
    op.drop_table('agent_metrics')
    op.drop_table('agent_capabilities')
    op.drop_table('agent_states')
    op.drop_table('agent_configs')
    
    # Drop ENUM types
    op.execute("""
        DROP TYPE IF EXISTS metrictype;
        DROP TYPE IF EXISTS agentstatusdetail;
        DROP TYPE IF EXISTS configtype;
    """)
