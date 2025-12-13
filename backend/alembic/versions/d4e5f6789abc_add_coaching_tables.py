"""add coaching layer tables

Revision ID: d4e5f6789abc
Revises: add_report_verification_fields
Create Date: 2025-12-13 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6789abc'
down_revision: Union[str, Sequence[str], None] = 'add_report_verification_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add coaching layer tables."""
    # Create supplier_readiness table
    op.create_table('supplier_readiness',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('regime', sa.String(length=20), nullable=False),
        sa.Column('overall_band', sa.Enum('FOUNDATIONAL', 'EMERGING', 'ADVANCED', 'LEADER', name='readinessband'), nullable=False),
        sa.Column('previous_band', sa.Enum('FOUNDATIONAL', 'EMERGING', 'ADVANCED', 'LEADER', name='readinessband'), nullable=True),
        sa.Column('progress_trend', sa.Enum('IMPROVING', 'STABLE', 'DECLINING', name='progresstrend'), nullable=True),
        sa.Column('dimension_scores', sa.JSON(), nullable=False),
        sa.Column('improvement_actions', sa.JSON(), nullable=False),
        sa.Column('methodology_version', sa.String(length=20), nullable=True),
        sa.Column('confidence_level', sa.String(length=20), nullable=True),
        sa.Column('assessed_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_supplier_readiness_tenant_id_tenants'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_supplier_readiness'))
    )
    op.create_index(op.f('ix_supplier_readiness_id'), 'supplier_readiness', ['id'], unique=False)
    op.create_index(op.f('ix_supplier_readiness_regime'), 'supplier_readiness', ['regime'], unique=False)
    op.create_index(op.f('ix_supplier_readiness_tenant_id'), 'supplier_readiness', ['tenant_id'], unique=False)
    op.create_index('idx_readiness_tenant_regime', 'supplier_readiness', ['tenant_id', 'regime'], unique=False)
    op.create_index('idx_readiness_tenant_assessed', 'supplier_readiness', ['tenant_id', 'assessed_at'], unique=False)
    op.create_index('idx_readiness_regime_band', 'supplier_readiness', ['regime', 'overall_band'], unique=False)

    # Create coaching_acknowledgments table
    op.create_table('coaching_acknowledgments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('action_id', sa.String(length=100), nullable=False),
        sa.Column('regime', sa.String(length=20), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'STARTED', 'COMPLETED', 'DISMISSED', name='actionstatus'), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('dismissed_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_coaching_acknowledgments_tenant_id_tenants'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_coaching_acknowledgments'))
    )
    op.create_index(op.f('ix_coaching_acknowledgments_id'), 'coaching_acknowledgments', ['id'], unique=False)
    op.create_index(op.f('ix_coaching_acknowledgments_action_id'), 'coaching_acknowledgments', ['action_id'], unique=False)
    op.create_index(op.f('ix_coaching_acknowledgments_tenant_id'), 'coaching_acknowledgments', ['tenant_id'], unique=False)
    op.create_index('idx_ack_tenant_action', 'coaching_acknowledgments', ['tenant_id', 'action_id'], unique=False)
    op.create_index('idx_ack_tenant_regime', 'coaching_acknowledgments', ['tenant_id', 'regime'], unique=False)
    op.create_index('idx_ack_status', 'coaching_acknowledgments', ['tenant_id', 'status'], unique=False)


def downgrade() -> None:
    """Downgrade schema - Remove coaching layer tables."""
    # Drop coaching_acknowledgments table
    op.drop_index('idx_ack_status', table_name='coaching_acknowledgments')
    op.drop_index('idx_ack_tenant_regime', table_name='coaching_acknowledgments')
    op.drop_index('idx_ack_tenant_action', table_name='coaching_acknowledgments')
    op.drop_index(op.f('ix_coaching_acknowledgments_tenant_id'), table_name='coaching_acknowledgments')
    op.drop_index(op.f('ix_coaching_acknowledgments_action_id'), table_name='coaching_acknowledgments')
    op.drop_index(op.f('ix_coaching_acknowledgments_id'), table_name='coaching_acknowledgments')
    op.drop_table('coaching_acknowledgments')

    # Drop supplier_readiness table
    op.drop_index('idx_readiness_regime_band', table_name='supplier_readiness')
    op.drop_index('idx_readiness_tenant_assessed', table_name='supplier_readiness')
    op.drop_index('idx_readiness_tenant_regime', table_name='supplier_readiness')
    op.drop_index(op.f('ix_supplier_readiness_tenant_id'), table_name='supplier_readiness')
    op.drop_index(op.f('ix_supplier_readiness_regime'), table_name='supplier_readiness')
    op.drop_index(op.f('ix_supplier_readiness_id'), table_name='supplier_readiness')
    op.drop_table('supplier_readiness')

    # Drop enums (only if no other tables use them)
    op.execute("DROP TYPE IF EXISTS actionstatus")
    op.execute("DROP TYPE IF EXISTS progresstrend")
    op.execute("DROP TYPE IF EXISTS readinessband")
