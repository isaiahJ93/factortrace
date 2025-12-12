"""Add emission_factor_id FK to emissions

Revision ID: c3d4e5f67890
Revises: a1b2c3d4e5f6
Create Date: 2025-12-12

This migration adds:
1. emission_factor_id column to emissions table
2. FK constraint to emission_factors table
3. Index for performance

Purpose: Enables traceability of which emission factor was used
for each emission calculation (CSRD audit requirement).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f67890'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add emission_factor_id column
    op.add_column(
        'emissions',
        sa.Column(
            'emission_factor_id',
            sa.Integer(),
            nullable=True,
            comment='FK to emission_factors table for audit/traceability'
        )
    )

    # 2. Create index for FK lookups
    op.create_index(
        'idx_emissions_factor_id',
        'emissions',
        ['emission_factor_id']
    )

    # 3. Add FK constraint (with SET NULL on delete for safety)
    # Note: This is wrapped in a try/except because SQLite doesn't enforce FKs
    # the same way. In production (PostgreSQL), this will work properly.
    try:
        op.create_foreign_key(
            'fk_emissions_emission_factor',
            'emissions',
            'emission_factors',
            ['emission_factor_id'],
            ['id'],
            ondelete='SET NULL'
        )
    except Exception:
        # SQLite may not support adding FK constraints after table creation
        pass


def downgrade() -> None:
    # 1. Drop FK constraint (if it exists)
    try:
        op.drop_constraint('fk_emissions_emission_factor', 'emissions', type_='foreignkey')
    except Exception:
        pass

    # 2. Drop index
    op.drop_index('idx_emissions_factor_id', table_name='emissions')

    # 3. Drop column
    op.drop_column('emissions', 'emission_factor_id')
