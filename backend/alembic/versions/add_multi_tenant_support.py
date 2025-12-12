"""add_multi_tenant_support

Add tenant_id to all tenant-owned tables for multi-tenant isolation.
This is a breaking migration that:
1. Creates the tenants table
2. Adds tenant_id columns to all tenant-owned tables
3. Drops existing test data (pre-production, no customer data)
4. Adds indexes for tenant-scoped queries
5. Removes deprecated ghg_organizations references

Revision ID: add_multi_tenant_001
Revises: 141b18e4bcd2
Create Date: 2025-12-12

Security: This migration implements critical tenant isolation required
for multi-tenant SaaS operation. All tenant-owned data MUST have tenant_id.

Note: Uses batch mode for SQLite compatibility.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_multi_tenant_001'
down_revision: Union[str, Sequence[str], None] = '141b18e4bcd2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add multi-tenant support to all tenant-owned tables.

    Strategy:
    1. Create tenants table first (referenced by all others)
    2. Delete existing test data (pre-production, clean slate)
    3. Add tenant_id columns
    4. Add performance indexes for tenant-scoped queries
    5. Add is_super_admin flag to users

    Note: SQLite doesn't support ALTER for foreign keys, so we use
    batch_alter_table which recreates tables. For PostgreSQL in production,
    this will use standard ALTER TABLE statements.
    """

    # =========================================================================
    # STEP 1: Create tenants table
    # =========================================================================
    op.create_table(
        'tenants',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True, unique=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('settings', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_tenants_slug', 'tenants', ['slug'], unique=True)
    op.create_index('ix_tenants_is_active', 'tenants', ['is_active'])

    # =========================================================================
    # STEP 2: Create development tenant FIRST (needed for foreign keys)
    # =========================================================================
    op.execute("""
        INSERT INTO tenants (id, name, slug, is_active, created_at, updated_at)
        VALUES (
            'dev-tenant-00000000-0000-0000-0000-000000000000',
            'Development Tenant',
            'dev',
            1,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        )
    """)

    # =========================================================================
    # STEP 3: Delete existing test data (clean slate per decision)
    # =========================================================================
    # Delete in order respecting foreign keys

    # Delete GHG tables that reference ghg_organizations
    op.execute("DELETE FROM ghg_category_results")
    op.execute("DELETE FROM ghg_activity_data")
    op.execute("DELETE FROM ghg_scope3_inventories")
    op.execute("DELETE FROM ghg_data_quality_scores")
    op.execute("DELETE FROM ghg_calculation_results")
    op.execute("DELETE FROM ghg_audit_logs")
    op.execute("DELETE FROM ghg_emission_factors")
    op.execute("DELETE FROM ghg_reporting_periods")
    op.execute("DELETE FROM ghg_organizations")

    # Delete core tenant-owned tables
    op.execute("DELETE FROM evidence_documents")
    op.execute("DELETE FROM data_quality_scores")
    op.execute("DELETE FROM emissions")
    op.execute("DELETE FROM vouchers")
    op.execute("DELETE FROM payments")
    op.execute("DELETE FROM users")

    # =========================================================================
    # STEP 4: Add tenant_id to users table (using batch mode for SQLite)
    # =========================================================================
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tenant_id', sa.String(36), nullable=True))
        batch_op.add_column(sa.Column('is_super_admin', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.create_index('ix_users_tenant_id', ['tenant_id'])

    # Set default tenant_id for any existing rows (should be none after DELETE)
    op.execute("""
        UPDATE users SET tenant_id = 'dev-tenant-00000000-0000-0000-0000-000000000000'
        WHERE tenant_id IS NULL
    """)

    # =========================================================================
    # STEP 5: Add tenant_id to emissions table
    # =========================================================================
    with op.batch_alter_table('emissions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tenant_id', sa.String(36), nullable=True))
        batch_op.create_index('ix_emissions_tenant_id', ['tenant_id'])
        batch_op.create_index('idx_emissions_tenant_scope', ['tenant_id', 'scope'])
        batch_op.create_index('idx_emissions_tenant_category', ['tenant_id', 'category'])

    op.execute("""
        UPDATE emissions SET tenant_id = 'dev-tenant-00000000-0000-0000-0000-000000000000'
        WHERE tenant_id IS NULL
    """)

    # =========================================================================
    # STEP 6: Add tenant_id to payments table
    # =========================================================================
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tenant_id', sa.String(36), nullable=True))
        batch_op.create_index('ix_payments_tenant_id', ['tenant_id'])
        batch_op.create_index('idx_payments_tenant_status', ['tenant_id', 'status'])

    op.execute("""
        UPDATE payments SET tenant_id = 'dev-tenant-00000000-0000-0000-0000-000000000000'
        WHERE tenant_id IS NULL
    """)

    # =========================================================================
    # STEP 7: Add tenant_id to vouchers table
    # =========================================================================
    with op.batch_alter_table('vouchers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tenant_id', sa.String(36), nullable=True))
        batch_op.create_index('ix_vouchers_tenant_id', ['tenant_id'])
        batch_op.create_index('idx_vouchers_tenant_status', ['tenant_id', 'status'])

    op.execute("""
        UPDATE vouchers SET tenant_id = 'dev-tenant-00000000-0000-0000-0000-000000000000'
        WHERE tenant_id IS NULL
    """)

    # =========================================================================
    # STEP 8: Add tenant_id to data_quality_scores table
    # =========================================================================
    with op.batch_alter_table('data_quality_scores', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tenant_id', sa.String(36), nullable=True))
        batch_op.create_index('ix_data_quality_scores_tenant_id', ['tenant_id'])
        batch_op.create_index('idx_dq_tenant_emission', ['tenant_id', 'emission_id'])

    op.execute("""
        UPDATE data_quality_scores SET tenant_id = 'dev-tenant-00000000-0000-0000-0000-000000000000'
        WHERE tenant_id IS NULL
    """)

    # =========================================================================
    # STEP 9: Add tenant_id to evidence_documents table
    # =========================================================================
    with op.batch_alter_table('evidence_documents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tenant_id', sa.String(36), nullable=True))
        batch_op.create_index('ix_evidence_documents_tenant_id', ['tenant_id'])
        batch_op.create_index('idx_evidence_tenant_emission', ['tenant_id', 'emission_id'])

    op.execute("""
        UPDATE evidence_documents SET tenant_id = 'dev-tenant-00000000-0000-0000-0000-000000000000'
        WHERE tenant_id IS NULL
    """)

    # =========================================================================
    # STEP 10: Update GHG tables - add tenant_id (replacing organization_id)
    # =========================================================================

    # ghg_reporting_periods
    with op.batch_alter_table('ghg_reporting_periods', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tenant_id', sa.String(36), nullable=True))
        batch_op.create_index('idx_ghg_rp_tenant', ['tenant_id'])
        # Drop organization_id if it exists
        try:
            batch_op.drop_column('organization_id')
        except Exception:
            pass

    # ghg_emission_factors (tenant_id can be NULL for global factors)
    with op.batch_alter_table('ghg_emission_factors', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tenant_id', sa.String(36), nullable=True))
        batch_op.create_index('idx_ghg_ef_tenant_category', ['tenant_id', 'category'])
        try:
            batch_op.drop_column('organization_id')
        except Exception:
            pass

    # ghg_activity_data
    with op.batch_alter_table('ghg_activity_data', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tenant_id', sa.String(36), nullable=True))
        batch_op.create_index('idx_ghg_ad_tenant_calc', ['tenant_id', 'calculation_id'])
        try:
            batch_op.drop_column('organization_id')
        except Exception:
            pass

    # ghg_calculation_results
    with op.batch_alter_table('ghg_calculation_results', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tenant_id', sa.String(36), nullable=True))
        batch_op.create_index('idx_ghg_cr_tenant_status', ['tenant_id', 'status'])
        try:
            batch_op.drop_column('organization_id')
        except Exception:
            pass

    # ghg_category_results
    with op.batch_alter_table('ghg_category_results', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tenant_id', sa.String(36), nullable=True))
        batch_op.create_index('idx_ghg_catr_tenant_calc', ['tenant_id', 'calculation_id'])
        try:
            batch_op.drop_column('organization_id')
        except Exception:
            pass

    # ghg_data_quality_scores
    with op.batch_alter_table('ghg_data_quality_scores', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tenant_id', sa.String(36), nullable=True))
        batch_op.create_index('idx_ghg_dqs_tenant', ['tenant_id'])
        try:
            batch_op.drop_column('organization_id')
        except Exception:
            pass

    # ghg_scope3_inventories
    with op.batch_alter_table('ghg_scope3_inventories', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tenant_id', sa.String(36), nullable=True))
        batch_op.create_index('idx_ghg_s3i_tenant_year', ['tenant_id', 'year'])
        try:
            batch_op.drop_column('organization_id')
        except Exception:
            pass

    # ghg_audit_logs
    with op.batch_alter_table('ghg_audit_logs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tenant_id', sa.String(36), nullable=True))
        batch_op.create_index('idx_ghg_audit_tenant_entity', ['tenant_id', 'entity_type'])
        try:
            batch_op.drop_column('organization_id')
        except Exception:
            pass

    # =========================================================================
    # STEP 11: Drop deprecated ghg_organizations table
    # =========================================================================
    op.drop_table('ghg_organizations')


def downgrade() -> None:
    """
    Revert multi-tenant support.

    WARNING: This will remove all tenant isolation!
    Only use in development/testing.
    """
    # Recreate ghg_organizations table
    op.create_table(
        'ghg_organizations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('industry', sa.String(100), nullable=True),
        sa.Column('country', sa.String(2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    # Drop tenant_id columns using batch mode
    tables_with_tenant = [
        'ghg_audit_logs',
        'ghg_scope3_inventories',
        'ghg_data_quality_scores',
        'ghg_category_results',
        'ghg_calculation_results',
        'ghg_activity_data',
        'ghg_emission_factors',
        'ghg_reporting_periods',
        'evidence_documents',
        'data_quality_scores',
        'vouchers',
        'payments',
        'emissions',
        'users',
    ]

    for table in tables_with_tenant:
        with op.batch_alter_table(table, schema=None) as batch_op:
            try:
                batch_op.drop_index(f'ix_{table}_tenant_id')
            except Exception:
                pass
            try:
                batch_op.drop_column('tenant_id')
            except Exception:
                pass

    # Drop users.is_super_admin
    with op.batch_alter_table('users', schema=None) as batch_op:
        try:
            batch_op.drop_column('is_super_admin')
        except Exception:
            pass

    # Delete dev tenant and drop tenants table
    op.execute("DELETE FROM tenants WHERE slug = 'dev'")
    op.drop_index('ix_tenants_is_active', table_name='tenants')
    op.drop_index('ix_tenants_slug', table_name='tenants')
    op.drop_table('tenants')
