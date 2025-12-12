"""Add soft delete and audit logging

Revision ID: a1b2c3d4e5f6
Revises: f1eda72e46c2
Create Date: 2025-12-12

This migration adds:
1. deleted_at column to emissions table for soft delete
2. audit_logs table for tracking all CRUD operations
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f1eda72e46c2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add deleted_at column to emissions table
    op.add_column('emissions', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))

    # 2. Create index for soft delete queries (tenant_id + deleted_at)
    op.create_index('idx_emissions_tenant_deleted', 'emissions', ['tenant_id', 'deleted_at'])

    # 3. Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(20), nullable=False),  # CREATE, UPDATE, DELETE, RESTORE
        sa.Column('changes', sa.JSON(), nullable=True),  # {field: {old, new}}
        sa.Column('ip_address', sa.String(45), nullable=True),  # IPv4 or IPv6
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # 4. Create indexes for audit_logs
    op.create_index('idx_audit_tenant_entity', 'audit_logs', ['tenant_id', 'entity_type', 'entity_id'])
    op.create_index('idx_audit_tenant_created', 'audit_logs', ['tenant_id', 'created_at'])
    op.create_index('idx_audit_entity_type', 'audit_logs', ['entity_type', 'created_at'])


def downgrade() -> None:
    # Drop audit_logs indexes
    op.drop_index('idx_audit_entity_type', table_name='audit_logs')
    op.drop_index('idx_audit_tenant_created', table_name='audit_logs')
    op.drop_index('idx_audit_tenant_entity', table_name='audit_logs')

    # Drop audit_logs table
    op.drop_table('audit_logs')

    # Drop emissions soft delete index
    op.drop_index('idx_emissions_tenant_deleted', table_name='emissions')

    # Drop deleted_at column
    op.drop_column('emissions', 'deleted_at')
