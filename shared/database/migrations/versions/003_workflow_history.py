"""Create workflow history tables

Revision ID: 003_workflow_history
Revises: 002_agent_state_tables
Create Date: 2025-01-19 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_workflow_history'
down_revision = '002_agent_state_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create workflow history tables"""
    
    # Define ENUM types (SQLAlchemy will create them automatically)
    workflow_type_enum = postgresql.ENUM(
        'cost_analysis',
        'performance_tuning',
        'resource_optimization',
        'quality_check',
        'scaling_decision',
        'configuration_update',
        'health_check',
        'anomaly_detection',
        name='workflow_type'
    )
    
    workflow_status_enum = postgresql.ENUM(
        'pending',
        'running',
        'completed',
        'failed',
        'cancelled',
        'timeout',
        name='workflow_status'
    )
    
    step_status_enum = postgresql.ENUM(
        'pending',
        'running',
        'completed',
        'failed',
        'skipped',
        'retrying',
        name='step_status'
    )
    
    artifact_type_enum = postgresql.ENUM(
        'report',
        'config',
        'log',
        'recommendation',
        'chart',
        'metrics',
        'alert',
        'diagnostic',
        name='artifact_type'
    )
    
    # Create workflow_executions table (enums will be created automatically)
    op.create_table(
        'workflow_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_type', workflow_type_enum, nullable=False),
        sa.Column('status', workflow_status_enum, nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('input_data', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('output_data', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('error_details', postgresql.JSONB(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for workflow_executions
    op.create_index('ix_workflow_executions_id', 'workflow_executions', ['id'])
    op.create_index('ix_workflow_executions_agent_id', 'workflow_executions', ['agent_id'])
    op.create_index('ix_workflow_executions_customer_id', 'workflow_executions', ['customer_id'])
    op.create_index('ix_workflow_executions_workflow_type', 'workflow_executions', ['workflow_type'])
    op.create_index('ix_workflow_executions_status', 'workflow_executions', ['status'])
    op.create_index('ix_workflow_executions_started_at', 'workflow_executions', ['started_at'])
    op.create_index('ix_workflow_executions_agent_status', 'workflow_executions', ['agent_id', 'status'])
    op.create_index('ix_workflow_executions_customer_type', 'workflow_executions', ['customer_id', 'workflow_type'])
    
    # Create workflow_steps table
    op.create_table(
        'workflow_steps',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workflow_execution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('step_name', sa.String(255), nullable=False),
        sa.Column('step_order', sa.Integer(), nullable=False),
        sa.Column('status', step_status_enum, nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('input_data', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('output_data', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('error_details', postgresql.JSONB(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['workflow_execution_id'], ['workflow_executions.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for workflow_steps
    op.create_index('ix_workflow_steps_id', 'workflow_steps', ['id'])
    op.create_index('ix_workflow_steps_workflow_execution_id', 'workflow_steps', ['workflow_execution_id'])
    op.create_index('ix_workflow_steps_step_name', 'workflow_steps', ['step_name'])
    op.create_index('ix_workflow_steps_status', 'workflow_steps', ['status'])
    op.create_index('ix_workflow_steps_execution_order', 'workflow_steps', ['workflow_execution_id', 'step_order'])
    op.create_index('ix_workflow_steps_execution_status', 'workflow_steps', ['workflow_execution_id', 'status'])
    op.create_index('ix_workflow_steps_name_status', 'workflow_steps', ['step_name', 'status'])
    
    # Create workflow_artifacts table
    op.create_table(
        'workflow_artifacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workflow_execution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_step_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('artifact_type', artifact_type_enum, nullable=False),
        sa.Column('artifact_name', sa.String(255), nullable=False),
        sa.Column('artifact_path', sa.Text(), nullable=False),
        sa.Column('artifact_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('content_type', sa.String(100), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['workflow_execution_id'], ['workflow_executions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workflow_step_id'], ['workflow_steps.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for workflow_artifacts
    op.create_index('ix_workflow_artifacts_id', 'workflow_artifacts', ['id'])
    op.create_index('ix_workflow_artifacts_workflow_execution_id', 'workflow_artifacts', ['workflow_execution_id'])
    op.create_index('ix_workflow_artifacts_workflow_step_id', 'workflow_artifacts', ['workflow_step_id'])
    op.create_index('ix_workflow_artifacts_artifact_type', 'workflow_artifacts', ['artifact_type'])
    op.create_index('ix_workflow_artifacts_execution_type', 'workflow_artifacts', ['workflow_execution_id', 'artifact_type'])
    op.create_index('ix_workflow_artifacts_step_type', 'workflow_artifacts', ['workflow_step_id', 'artifact_type'])
    
    # Add current_workflow_id to agent_states (optional link)
    op.add_column(
        'agent_states',
        sa.Column('current_workflow_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'fk_agent_states_current_workflow',
        'agent_states',
        'workflow_executions',
        ['current_workflow_id'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_agent_states_current_workflow_id', 'agent_states', ['current_workflow_id'])


def downgrade() -> None:
    """Drop workflow history tables"""
    
    # Drop indexes and column from agent_states
    op.drop_index('ix_agent_states_current_workflow_id', 'agent_states')
    op.drop_constraint('fk_agent_states_current_workflow', 'agent_states', type_='foreignkey')
    op.drop_column('agent_states', 'current_workflow_id')
    
    # Drop workflow_artifacts table and indexes
    op.drop_index('ix_workflow_artifacts_step_type', 'workflow_artifacts')
    op.drop_index('ix_workflow_artifacts_execution_type', 'workflow_artifacts')
    op.drop_index('ix_workflow_artifacts_artifact_type', 'workflow_artifacts')
    op.drop_index('ix_workflow_artifacts_workflow_step_id', 'workflow_artifacts')
    op.drop_index('ix_workflow_artifacts_workflow_execution_id', 'workflow_artifacts')
    op.drop_index('ix_workflow_artifacts_id', 'workflow_artifacts')
    op.drop_table('workflow_artifacts')
    
    # Drop workflow_steps table and indexes
    op.drop_index('ix_workflow_steps_name_status', 'workflow_steps')
    op.drop_index('ix_workflow_steps_execution_status', 'workflow_steps')
    op.drop_index('ix_workflow_steps_execution_order', 'workflow_steps')
    op.drop_index('ix_workflow_steps_status', 'workflow_steps')
    op.drop_index('ix_workflow_steps_step_name', 'workflow_steps')
    op.drop_index('ix_workflow_steps_workflow_execution_id', 'workflow_steps')
    op.drop_index('ix_workflow_steps_id', 'workflow_steps')
    op.drop_table('workflow_steps')
    
    # Drop workflow_executions table and indexes
    op.drop_index('ix_workflow_executions_customer_type', 'workflow_executions')
    op.drop_index('ix_workflow_executions_agent_status', 'workflow_executions')
    op.drop_index('ix_workflow_executions_started_at', 'workflow_executions')
    op.drop_index('ix_workflow_executions_status', 'workflow_executions')
    op.drop_index('ix_workflow_executions_workflow_type', 'workflow_executions')
    op.drop_index('ix_workflow_executions_customer_id', 'workflow_executions')
    op.drop_index('ix_workflow_executions_agent_id', 'workflow_executions')
    op.drop_index('ix_workflow_executions_id', 'workflow_executions')
    op.drop_table('workflow_executions')
    
    # Drop ENUM types
    sa.Enum(name='artifact_type').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='step_status').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='workflow_status').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='workflow_type').drop(op.get_bind(), checkfirst=True)
