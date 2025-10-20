"""Create resource schema tables

Revision ID: 004_resource_schema
Revises: 003_workflow_history
Create Date: 2025-01-20 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_resource_schema'
down_revision = '003_workflow_history'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create resource schema tables"""
    
    # Define ENUM types (SQLAlchemy will create them automatically)
    resource_type_enum = postgresql.ENUM(
        'gpu',
        'cpu',
        'memory',
        'disk',
        'network',
        name='resource_type'
    )
    
    scaling_event_type_enum = postgresql.ENUM(
        'scale_up',
        'scale_down',
        'auto_scale_triggered',
        'manual_scale',
        'scale_cancelled',
        name='scaling_event_type'
    )
    
    # Create resource_metrics table
    op.create_table(
        'resource_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('instance_id', sa.String(255), nullable=False),
        sa.Column('resource_type', resource_type_enum, nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for resource_metrics
    op.create_index('ix_resource_metrics_id', 'resource_metrics', ['id'])
    op.create_index('ix_resource_metrics_agent_id', 'resource_metrics', ['agent_id'])
    op.create_index('ix_resource_metrics_customer_id', 'resource_metrics', ['customer_id'])
    op.create_index('ix_resource_metrics_instance_id', 'resource_metrics', ['instance_id'])
    op.create_index('ix_resource_metrics_resource_type', 'resource_metrics', ['resource_type'])
    op.create_index('ix_resource_metrics_metric_name', 'resource_metrics', ['metric_name'])
    op.create_index('ix_resource_metrics_timestamp', 'resource_metrics', ['timestamp'])
    op.create_index('ix_resource_metrics_agent_instance', 'resource_metrics', ['agent_id', 'instance_id'])
    op.create_index('ix_resource_metrics_customer_type', 'resource_metrics', ['customer_id', 'resource_type'])
    op.create_index('ix_resource_metrics_instance_timestamp', 'resource_metrics', ['instance_id', 'timestamp'])
    op.create_index('ix_resource_metrics_type_name', 'resource_metrics', ['resource_type', 'metric_name'])
    
    # Create scaling_events table
    op.create_table(
        'scaling_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_execution_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', scaling_event_type_enum, nullable=False),
        sa.Column('trigger_reason', sa.String(500), nullable=False),
        sa.Column('before_state', postgresql.JSONB(), nullable=False),
        sa.Column('after_state', postgresql.JSONB(), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('error_details', postgresql.JSONB(), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workflow_execution_id'], ['workflow_executions.id'], ondelete='SET NULL'),
    )
    
    # Create indexes for scaling_events
    op.create_index('ix_scaling_events_id', 'scaling_events', ['id'])
    op.create_index('ix_scaling_events_agent_id', 'scaling_events', ['agent_id'])
    op.create_index('ix_scaling_events_customer_id', 'scaling_events', ['customer_id'])
    op.create_index('ix_scaling_events_workflow_execution_id', 'scaling_events', ['workflow_execution_id'])
    op.create_index('ix_scaling_events_event_type', 'scaling_events', ['event_type'])
    op.create_index('ix_scaling_events_success', 'scaling_events', ['success'])
    op.create_index('ix_scaling_events_executed_at', 'scaling_events', ['executed_at'])
    op.create_index('ix_scaling_events_agent_type', 'scaling_events', ['agent_id', 'event_type'])
    op.create_index('ix_scaling_events_customer_success', 'scaling_events', ['customer_id', 'success'])
    op.create_index('ix_scaling_events_workflow', 'scaling_events', ['workflow_execution_id'])


def downgrade() -> None:
    """Drop resource schema tables"""
    
    # Drop scaling_events table and indexes
    op.drop_index('ix_scaling_events_workflow', 'scaling_events')
    op.drop_index('ix_scaling_events_customer_success', 'scaling_events')
    op.drop_index('ix_scaling_events_agent_type', 'scaling_events')
    op.drop_index('ix_scaling_events_executed_at', 'scaling_events')
    op.drop_index('ix_scaling_events_success', 'scaling_events')
    op.drop_index('ix_scaling_events_event_type', 'scaling_events')
    op.drop_index('ix_scaling_events_workflow_execution_id', 'scaling_events')
    op.drop_index('ix_scaling_events_customer_id', 'scaling_events')
    op.drop_index('ix_scaling_events_agent_id', 'scaling_events')
    op.drop_index('ix_scaling_events_id', 'scaling_events')
    op.drop_table('scaling_events')
    
    # Drop resource_metrics table and indexes
    op.drop_index('ix_resource_metrics_type_name', 'resource_metrics')
    op.drop_index('ix_resource_metrics_instance_timestamp', 'resource_metrics')
    op.drop_index('ix_resource_metrics_customer_type', 'resource_metrics')
    op.drop_index('ix_resource_metrics_agent_instance', 'resource_metrics')
    op.drop_index('ix_resource_metrics_timestamp', 'resource_metrics')
    op.drop_index('ix_resource_metrics_metric_name', 'resource_metrics')
    op.drop_index('ix_resource_metrics_resource_type', 'resource_metrics')
    op.drop_index('ix_resource_metrics_instance_id', 'resource_metrics')
    op.drop_index('ix_resource_metrics_customer_id', 'resource_metrics')
    op.drop_index('ix_resource_metrics_agent_id', 'resource_metrics')
    op.drop_index('ix_resource_metrics_id', 'resource_metrics')
    op.drop_table('resource_metrics')
    
    # Drop ENUM types
    sa.Enum(name='scaling_event_type').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='resource_type').drop(op.get_bind(), checkfirst=True)
