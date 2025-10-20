"""Create application schema tables

Revision ID: 005_application_schema
Revises: 004_resource_schema
Create Date: 2025-01-20 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_application_schema'
down_revision = '004_resource_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create application schema tables"""
    
    # Create ENUM types
    baseline_type_enum = postgresql.ENUM(
        'initial',
        'updated',
        'rollback',
        name='baseline_type'
    )
    
    regression_type_enum = postgresql.ENUM(
        'quality_drop',
        'latency_increase',
        'hallucination_spike',
        'toxicity_increase',
        name='regression_type'
    )
    
    regression_severity_enum = postgresql.ENUM(
        'low',
        'medium',
        'high',
        'critical',
        name='regression_severity'
    )
    
    regression_action_enum = postgresql.ENUM(
        'alert_only',
        'rollback_triggered',
        'manual_review',
        'auto_fixed',
        name='regression_action'
    )
    
    # Create quality_metrics table
    op.create_table(
        'quality_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('request_id', sa.String(255), nullable=False, unique=True),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True),
        sa.Column('completion_tokens', sa.Integer(), nullable=True),
        sa.Column('latency_ms', sa.Float(), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('coherence_score', sa.Float(), nullable=True),
        sa.Column('factuality_score', sa.Float(), nullable=True),
        sa.Column('hallucination_detected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('toxicity_score', sa.Float(), nullable=True),
        sa.Column('overall_quality_score', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for quality_metrics
    op.create_index('ix_quality_metrics_id', 'quality_metrics', ['id'])
    op.create_index('ix_quality_metrics_agent_id', 'quality_metrics', ['agent_id'])
    op.create_index('ix_quality_metrics_customer_id', 'quality_metrics', ['customer_id'])
    op.create_index('ix_quality_metrics_request_id', 'quality_metrics', ['request_id'], unique=True)
    op.create_index('ix_quality_metrics_model_name', 'quality_metrics', ['model_name'])
    op.create_index('ix_quality_metrics_hallucination_detected', 'quality_metrics', ['hallucination_detected'])
    op.create_index('ix_quality_metrics_overall_quality_score', 'quality_metrics', ['overall_quality_score'])
    op.create_index('ix_quality_metrics_timestamp', 'quality_metrics', ['timestamp'])
    op.create_index('ix_quality_metrics_agent_model', 'quality_metrics', ['agent_id', 'model_name'])
    op.create_index('ix_quality_metrics_customer_model', 'quality_metrics', ['customer_id', 'model_name'])
    op.create_index('ix_quality_metrics_model_timestamp', 'quality_metrics', ['model_name', 'timestamp'])
    
    # Create quality_baselines table
    op.create_table(
        'quality_baselines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('baseline_type', baseline_type_enum, nullable=False),
        sa.Column('sample_size', sa.Integer(), nullable=False),
        sa.Column('avg_relevance_score', sa.Float(), nullable=True),
        sa.Column('avg_coherence_score', sa.Float(), nullable=True),
        sa.Column('avg_factuality_score', sa.Float(), nullable=True),
        sa.Column('avg_overall_score', sa.Float(), nullable=False),
        sa.Column('p95_latency_ms', sa.Float(), nullable=True),
        sa.Column('established_at', sa.DateTime(), nullable=False),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for quality_baselines
    op.create_index('ix_quality_baselines_id', 'quality_baselines', ['id'])
    op.create_index('ix_quality_baselines_agent_id', 'quality_baselines', ['agent_id'])
    op.create_index('ix_quality_baselines_customer_id', 'quality_baselines', ['customer_id'])
    op.create_index('ix_quality_baselines_model_name', 'quality_baselines', ['model_name'])
    op.create_index('ix_quality_baselines_baseline_type', 'quality_baselines', ['baseline_type'])
    op.create_index('ix_quality_baselines_established_at', 'quality_baselines', ['established_at'])
    op.create_index('ix_quality_baselines_agent_model', 'quality_baselines', ['agent_id', 'model_name'])
    op.create_index('ix_quality_baselines_customer_model', 'quality_baselines', ['customer_id', 'model_name'])
    op.create_index('ix_quality_baselines_type', 'quality_baselines', ['baseline_type'])
    
    # Create quality_regressions table
    op.create_table(
        'quality_regressions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('baseline_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_execution_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('regression_type', regression_type_enum, nullable=False),
        sa.Column('severity', regression_severity_enum, nullable=False),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('baseline_value', sa.Float(), nullable=False),
        sa.Column('current_value', sa.Float(), nullable=False),
        sa.Column('delta_percent', sa.Float(), nullable=False),
        sa.Column('sample_size', sa.Integer(), nullable=False),
        sa.Column('action_taken', regression_action_enum, nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['baseline_id'], ['quality_baselines.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workflow_execution_id'], ['workflow_executions.id'], ondelete='SET NULL'),
    )
    
    # Create indexes for quality_regressions
    op.create_index('ix_quality_regressions_id', 'quality_regressions', ['id'])
    op.create_index('ix_quality_regressions_agent_id', 'quality_regressions', ['agent_id'])
    op.create_index('ix_quality_regressions_customer_id', 'quality_regressions', ['customer_id'])
    op.create_index('ix_quality_regressions_baseline_id', 'quality_regressions', ['baseline_id'])
    op.create_index('ix_quality_regressions_workflow_execution_id', 'quality_regressions', ['workflow_execution_id'])
    op.create_index('ix_quality_regressions_regression_type', 'quality_regressions', ['regression_type'])
    op.create_index('ix_quality_regressions_severity', 'quality_regressions', ['severity'])
    op.create_index('ix_quality_regressions_action_taken', 'quality_regressions', ['action_taken'])
    op.create_index('ix_quality_regressions_detected_at', 'quality_regressions', ['detected_at'])
    op.create_index('ix_quality_regressions_agent_severity', 'quality_regressions', ['agent_id', 'severity'])
    op.create_index('ix_quality_regressions_customer_type', 'quality_regressions', ['customer_id', 'regression_type'])
    op.create_index('ix_quality_regressions_baseline', 'quality_regressions', ['baseline_id'])
    op.create_index('ix_quality_regressions_workflow', 'quality_regressions', ['workflow_execution_id'])
    op.create_index('ix_quality_regressions_unresolved', 'quality_regressions', ['resolved_at'])


def downgrade() -> None:
    """Drop application schema tables"""
    
    # Drop quality_regressions table and indexes
    op.drop_index('ix_quality_regressions_unresolved', 'quality_regressions')
    op.drop_index('ix_quality_regressions_workflow', 'quality_regressions')
    op.drop_index('ix_quality_regressions_baseline', 'quality_regressions')
    op.drop_index('ix_quality_regressions_customer_type', 'quality_regressions')
    op.drop_index('ix_quality_regressions_agent_severity', 'quality_regressions')
    op.drop_index('ix_quality_regressions_detected_at', 'quality_regressions')
    op.drop_index('ix_quality_regressions_action_taken', 'quality_regressions')
    op.drop_index('ix_quality_regressions_severity', 'quality_regressions')
    op.drop_index('ix_quality_regressions_regression_type', 'quality_regressions')
    op.drop_index('ix_quality_regressions_workflow_execution_id', 'quality_regressions')
    op.drop_index('ix_quality_regressions_baseline_id', 'quality_regressions')
    op.drop_index('ix_quality_regressions_customer_id', 'quality_regressions')
    op.drop_index('ix_quality_regressions_agent_id', 'quality_regressions')
    op.drop_index('ix_quality_regressions_id', 'quality_regressions')
    op.drop_table('quality_regressions')
    
    # Drop quality_baselines table and indexes
    op.drop_index('ix_quality_baselines_type', 'quality_baselines')
    op.drop_index('ix_quality_baselines_customer_model', 'quality_baselines')
    op.drop_index('ix_quality_baselines_agent_model', 'quality_baselines')
    op.drop_index('ix_quality_baselines_established_at', 'quality_baselines')
    op.drop_index('ix_quality_baselines_baseline_type', 'quality_baselines')
    op.drop_index('ix_quality_baselines_model_name', 'quality_baselines')
    op.drop_index('ix_quality_baselines_customer_id', 'quality_baselines')
    op.drop_index('ix_quality_baselines_agent_id', 'quality_baselines')
    op.drop_index('ix_quality_baselines_id', 'quality_baselines')
    op.drop_table('quality_baselines')
    
    # Drop quality_metrics table and indexes
    op.drop_index('ix_quality_metrics_model_timestamp', 'quality_metrics')
    op.drop_index('ix_quality_metrics_customer_model', 'quality_metrics')
    op.drop_index('ix_quality_metrics_agent_model', 'quality_metrics')
    op.drop_index('ix_quality_metrics_timestamp', 'quality_metrics')
    op.drop_index('ix_quality_metrics_overall_quality_score', 'quality_metrics')
    op.drop_index('ix_quality_metrics_hallucination_detected', 'quality_metrics')
    op.drop_index('ix_quality_metrics_model_name', 'quality_metrics')
    op.drop_index('ix_quality_metrics_request_id', 'quality_metrics')
    op.drop_index('ix_quality_metrics_customer_id', 'quality_metrics')
    op.drop_index('ix_quality_metrics_agent_id', 'quality_metrics')
    op.drop_index('ix_quality_metrics_id', 'quality_metrics')
    op.drop_table('quality_metrics')
    
    # Drop ENUM types
    sa.Enum(name='regression_action').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='regression_severity').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='regression_type').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='baseline_type').drop(op.get_bind(), checkfirst=True)
