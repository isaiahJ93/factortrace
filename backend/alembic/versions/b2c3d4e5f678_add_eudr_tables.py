"""add_eudr_tables

Revision ID: b2c3d4e5f678
Revises: 7a0aad56030f
Create Date: 2025-12-12 21:00:00.000000

Adds EUDR (EU Deforestation Regulation) tables:
- eudr_commodities: Reference data for EUDR commodities
- eudr_operators: Operators/traders in supply chain (tenant-owned)
- eudr_supply_sites: Geographic production sites with coordinates (tenant-owned)
- eudr_batches: Commodity batches/lots (tenant-owned)
- eudr_supply_chain_links: Directed graph edges (tenant-owned)
- eudr_georisk_snapshots: Point-in-time risk assessments (tenant-owned)
- eudr_due_diligences: Due diligence statements (tenant-owned)
- eudr_due_diligence_batch_links: Batch links to DD statements
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f678'
down_revision: Union[str, Sequence[str], None] = '7a0aad56030f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create EUDR tables."""

    # 1. eudr_commodities - Reference data (not tenant-owned)
    op.create_table('eudr_commodities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('commodity_type', sa.Enum('CATTLE', 'COCOA', 'COFFEE', 'PALM_OIL', 'SOY', 'TIMBER', 'RUBBER', name='eudrcommoditytype'), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('hs_code', sa.String(length=10), nullable=True),
        sa.Column('risk_profile_default', sa.Enum('LOW', 'MEDIUM', 'HIGH', name='eudrrisklevel'), nullable=False, server_default='MEDIUM'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_eudr_commodities'))
    )
    op.create_index(op.f('ix_eudr_commodities_commodity_type'), 'eudr_commodities', ['commodity_type'], unique=False)
    op.create_index(op.f('ix_eudr_commodities_hs_code'), 'eudr_commodities', ['hs_code'], unique=False)
    op.create_index(op.f('ix_eudr_commodities_name'), 'eudr_commodities', ['name'], unique=True)
    op.create_index('idx_eudr_commodity_type_active', 'eudr_commodities', ['commodity_type', 'is_active'], unique=False)

    # 2. eudr_operators - Tenant-owned
    op.create_table('eudr_operators',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('role', sa.Enum('OPERATOR', 'TRADER', 'SUPPLIER', name='eudroperatorrole'), nullable=False),
        sa.Column('country', sa.String(length=2), nullable=False),
        sa.Column('identifier', sa.String(length=100), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_eudr_operators_tenant_id_tenants'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_eudr_operators'))
    )
    op.create_index(op.f('ix_eudr_operators_country'), 'eudr_operators', ['country'], unique=False)
    op.create_index(op.f('ix_eudr_operators_role'), 'eudr_operators', ['role'], unique=False)
    op.create_index(op.f('ix_eudr_operators_tenant_id'), 'eudr_operators', ['tenant_id'], unique=False)
    op.create_index('idx_eudr_operator_tenant_role', 'eudr_operators', ['tenant_id', 'role'], unique=False)
    op.create_index('idx_eudr_operator_tenant_country', 'eudr_operators', ['tenant_id', 'country'], unique=False)
    op.create_index('idx_eudr_operator_tenant_name', 'eudr_operators', ['tenant_id', 'name'], unique=False)

    # 3. eudr_supply_sites - Tenant-owned with geospatial fields
    op.create_table('eudr_supply_sites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('operator_id', sa.Integer(), nullable=False),
        sa.Column('commodity_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('site_reference', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=2), nullable=False),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('geometry_geojson', sa.Text(), nullable=True),
        sa.Column('area_ha', sa.Float(), nullable=True),
        sa.Column('legal_title_reference', sa.String(length=200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['commodity_id'], ['eudr_commodities.id'], name=op.f('fk_eudr_supply_sites_commodity_id_eudr_commodities'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['operator_id'], ['eudr_operators.id'], name=op.f('fk_eudr_supply_sites_operator_id_eudr_operators'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_eudr_supply_sites_tenant_id_tenants'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_eudr_supply_sites'))
    )
    op.create_index(op.f('ix_eudr_supply_sites_commodity_id'), 'eudr_supply_sites', ['commodity_id'], unique=False)
    op.create_index(op.f('ix_eudr_supply_sites_country'), 'eudr_supply_sites', ['country'], unique=False)
    op.create_index(op.f('ix_eudr_supply_sites_operator_id'), 'eudr_supply_sites', ['operator_id'], unique=False)
    op.create_index(op.f('ix_eudr_supply_sites_tenant_id'), 'eudr_supply_sites', ['tenant_id'], unique=False)
    op.create_index('idx_eudr_site_tenant_operator', 'eudr_supply_sites', ['tenant_id', 'operator_id'], unique=False)
    op.create_index('idx_eudr_site_tenant_commodity', 'eudr_supply_sites', ['tenant_id', 'commodity_id'], unique=False)
    op.create_index('idx_eudr_site_tenant_country', 'eudr_supply_sites', ['tenant_id', 'country'], unique=False)
    op.create_index('idx_eudr_site_coordinates', 'eudr_supply_sites', ['latitude', 'longitude'], unique=False)

    # 4. eudr_batches - Tenant-owned
    op.create_table('eudr_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('batch_reference', sa.String(length=100), nullable=False),
        sa.Column('commodity_id', sa.Integer(), nullable=False),
        sa.Column('volume', sa.Float(), nullable=False),
        sa.Column('volume_unit', sa.String(length=20), nullable=False, server_default='tonne'),
        sa.Column('harvest_year', sa.Integer(), nullable=True),
        sa.Column('origin_site_id', sa.Integer(), nullable=True),
        sa.Column('origin_country', sa.String(length=2), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['commodity_id'], ['eudr_commodities.id'], name=op.f('fk_eudr_batches_commodity_id_eudr_commodities'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['origin_site_id'], ['eudr_supply_sites.id'], name=op.f('fk_eudr_batches_origin_site_id_eudr_supply_sites'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_eudr_batches_tenant_id_tenants'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_eudr_batches'))
    )
    op.create_index(op.f('ix_eudr_batches_batch_reference'), 'eudr_batches', ['batch_reference'], unique=False)
    op.create_index(op.f('ix_eudr_batches_commodity_id'), 'eudr_batches', ['commodity_id'], unique=False)
    op.create_index(op.f('ix_eudr_batches_harvest_year'), 'eudr_batches', ['harvest_year'], unique=False)
    op.create_index(op.f('ix_eudr_batches_origin_country'), 'eudr_batches', ['origin_country'], unique=False)
    op.create_index(op.f('ix_eudr_batches_origin_site_id'), 'eudr_batches', ['origin_site_id'], unique=False)
    op.create_index(op.f('ix_eudr_batches_tenant_id'), 'eudr_batches', ['tenant_id'], unique=False)
    op.create_index('idx_eudr_batch_tenant_ref', 'eudr_batches', ['tenant_id', 'batch_reference'], unique=False)
    op.create_index('idx_eudr_batch_tenant_commodity', 'eudr_batches', ['tenant_id', 'commodity_id'], unique=False)
    op.create_index('idx_eudr_batch_tenant_origin', 'eudr_batches', ['tenant_id', 'origin_country'], unique=False)
    op.create_index('idx_eudr_batch_tenant_year', 'eudr_batches', ['tenant_id', 'harvest_year'], unique=False)

    # 5. eudr_supply_chain_links - Tenant-owned (graph edges)
    op.create_table('eudr_supply_chain_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('from_batch_id', sa.Integer(), nullable=True),
        sa.Column('from_operator_id', sa.Integer(), nullable=False),
        sa.Column('to_batch_id', sa.Integer(), nullable=True),
        sa.Column('to_operator_id', sa.Integer(), nullable=False),
        sa.Column('link_type', sa.Enum('PURCHASE', 'PROCESSING', 'MIXING', 'TRANSPORT', 'AGGREGATION', name='eudrsupplychainlinktype'), nullable=False),
        sa.Column('documentation_reference', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['from_batch_id'], ['eudr_batches.id'], name=op.f('fk_eudr_supply_chain_links_from_batch_id_eudr_batches'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['from_operator_id'], ['eudr_operators.id'], name=op.f('fk_eudr_supply_chain_links_from_operator_id_eudr_operators'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_eudr_supply_chain_links_tenant_id_tenants'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_batch_id'], ['eudr_batches.id'], name=op.f('fk_eudr_supply_chain_links_to_batch_id_eudr_batches'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_operator_id'], ['eudr_operators.id'], name=op.f('fk_eudr_supply_chain_links_to_operator_id_eudr_operators'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_eudr_supply_chain_links'))
    )
    op.create_index(op.f('ix_eudr_supply_chain_links_from_batch_id'), 'eudr_supply_chain_links', ['from_batch_id'], unique=False)
    op.create_index(op.f('ix_eudr_supply_chain_links_from_operator_id'), 'eudr_supply_chain_links', ['from_operator_id'], unique=False)
    op.create_index(op.f('ix_eudr_supply_chain_links_link_type'), 'eudr_supply_chain_links', ['link_type'], unique=False)
    op.create_index(op.f('ix_eudr_supply_chain_links_tenant_id'), 'eudr_supply_chain_links', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_eudr_supply_chain_links_to_batch_id'), 'eudr_supply_chain_links', ['to_batch_id'], unique=False)
    op.create_index(op.f('ix_eudr_supply_chain_links_to_operator_id'), 'eudr_supply_chain_links', ['to_operator_id'], unique=False)
    op.create_index('idx_eudr_link_tenant_from', 'eudr_supply_chain_links', ['tenant_id', 'from_batch_id', 'from_operator_id'], unique=False)
    op.create_index('idx_eudr_link_tenant_to', 'eudr_supply_chain_links', ['tenant_id', 'to_batch_id', 'to_operator_id'], unique=False)
    op.create_index('idx_eudr_link_tenant_type', 'eudr_supply_chain_links', ['tenant_id', 'link_type'], unique=False)

    # 6. eudr_georisk_snapshots - Tenant-owned
    op.create_table('eudr_georisk_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('supply_site_id', sa.Integer(), nullable=False),
        sa.Column('source', sa.Enum('GFW', 'NATIONAL_CADASTRE', 'EUDR_BENCHMARK', 'MANUAL', 'MOCK', name='eudrgeoriskssource'), nullable=False),
        sa.Column('snapshot_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.Column('deforestation_flag', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('tree_cover_loss_ha', sa.Float(), nullable=True),
        sa.Column('protected_area_overlap', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('risk_score_raw', sa.Float(), nullable=True),
        sa.Column('risk_level', sa.Enum('LOW', 'MEDIUM', 'HIGH', name='eudrrisklevel', create_type=False), nullable=True),
        sa.Column('details_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['supply_site_id'], ['eudr_supply_sites.id'], name=op.f('fk_eudr_georisk_snapshots_supply_site_id_eudr_supply_sites'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_eudr_georisk_snapshots_tenant_id_tenants'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_eudr_georisk_snapshots'))
    )
    op.create_index(op.f('ix_eudr_georisk_snapshots_risk_level'), 'eudr_georisk_snapshots', ['risk_level'], unique=False)
    op.create_index(op.f('ix_eudr_georisk_snapshots_snapshot_date'), 'eudr_georisk_snapshots', ['snapshot_date'], unique=False)
    op.create_index(op.f('ix_eudr_georisk_snapshots_source'), 'eudr_georisk_snapshots', ['source'], unique=False)
    op.create_index(op.f('ix_eudr_georisk_snapshots_supply_site_id'), 'eudr_georisk_snapshots', ['supply_site_id'], unique=False)
    op.create_index(op.f('ix_eudr_georisk_snapshots_tenant_id'), 'eudr_georisk_snapshots', ['tenant_id'], unique=False)
    op.create_index('idx_eudr_georisk_tenant_site', 'eudr_georisk_snapshots', ['tenant_id', 'supply_site_id'], unique=False)
    op.create_index('idx_eudr_georisk_tenant_date', 'eudr_georisk_snapshots', ['tenant_id', 'snapshot_date'], unique=False)
    op.create_index('idx_eudr_georisk_site_date', 'eudr_georisk_snapshots', ['supply_site_id', 'snapshot_date'], unique=False)

    # 7. eudr_due_diligences - Tenant-owned
    op.create_table('eudr_due_diligences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('operator_id', sa.Integer(), nullable=False),
        sa.Column('reference', sa.String(length=100), nullable=True),
        sa.Column('commodity_id', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'FINAL', 'ARCHIVED', name='eudrduediligencestatus'), nullable=False, server_default='DRAFT'),
        sa.Column('overall_risk_level', sa.Enum('LOW', 'MEDIUM', 'HIGH', name='eudrrisklevel', create_type=False), nullable=True),
        sa.Column('overall_risk_score', sa.Float(), nullable=True),
        sa.Column('justification_summary', sa.Text(), nullable=True),
        sa.Column('total_volume', sa.Float(), nullable=True, server_default=sa.text('0.0')),
        sa.Column('total_volume_unit', sa.String(length=20), nullable=True, server_default='tonne'),
        sa.Column('batch_count', sa.Integer(), nullable=True, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['commodity_id'], ['eudr_commodities.id'], name=op.f('fk_eudr_due_diligences_commodity_id_eudr_commodities'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name=op.f('fk_eudr_due_diligences_created_by_user_id_users')),
        sa.ForeignKeyConstraint(['operator_id'], ['eudr_operators.id'], name=op.f('fk_eudr_due_diligences_operator_id_eudr_operators'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_eudr_due_diligences_tenant_id_tenants'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_eudr_due_diligences'))
    )
    op.create_index(op.f('ix_eudr_due_diligences_commodity_id'), 'eudr_due_diligences', ['commodity_id'], unique=False)
    op.create_index(op.f('ix_eudr_due_diligences_operator_id'), 'eudr_due_diligences', ['operator_id'], unique=False)
    op.create_index(op.f('ix_eudr_due_diligences_reference'), 'eudr_due_diligences', ['reference'], unique=False)
    op.create_index(op.f('ix_eudr_due_diligences_status'), 'eudr_due_diligences', ['status'], unique=False)
    op.create_index(op.f('ix_eudr_due_diligences_tenant_id'), 'eudr_due_diligences', ['tenant_id'], unique=False)
    op.create_index('idx_eudr_dd_tenant_status', 'eudr_due_diligences', ['tenant_id', 'status'], unique=False)
    op.create_index('idx_eudr_dd_tenant_operator', 'eudr_due_diligences', ['tenant_id', 'operator_id'], unique=False)
    op.create_index('idx_eudr_dd_tenant_commodity', 'eudr_due_diligences', ['tenant_id', 'commodity_id'], unique=False)
    op.create_index('idx_eudr_dd_tenant_period', 'eudr_due_diligences', ['tenant_id', 'period_start', 'period_end'], unique=False)
    op.create_index('idx_eudr_dd_tenant_ref', 'eudr_due_diligences', ['tenant_id', 'reference'], unique=False)

    # 8. eudr_due_diligence_batch_links - Links batches to DD statements
    op.create_table('eudr_due_diligence_batch_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('due_diligence_id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=False),
        sa.Column('batch_risk_score', sa.Float(), nullable=True),
        sa.Column('batch_risk_level', sa.Enum('LOW', 'MEDIUM', 'HIGH', name='eudrrisklevel', create_type=False), nullable=True),
        sa.Column('included_volume', sa.Float(), nullable=True),
        sa.Column('included_volume_unit', sa.String(length=20), nullable=True, server_default='tonne'),
        sa.Column('assessment_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['batch_id'], ['eudr_batches.id'], name=op.f('fk_eudr_due_diligence_batch_links_batch_id_eudr_batches'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['due_diligence_id'], ['eudr_due_diligences.id'], name=op.f('fk_eudr_due_diligence_batch_links_due_diligence_id_eudr_due_diligences'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_eudr_due_diligence_batch_links'))
    )
    op.create_index(op.f('ix_eudr_due_diligence_batch_links_batch_id'), 'eudr_due_diligence_batch_links', ['batch_id'], unique=False)
    op.create_index(op.f('ix_eudr_due_diligence_batch_links_due_diligence_id'), 'eudr_due_diligence_batch_links', ['due_diligence_id'], unique=False)
    op.create_index('idx_eudr_dd_batch_dd', 'eudr_due_diligence_batch_links', ['due_diligence_id', 'batch_id'], unique=True)
    op.create_index('idx_eudr_dd_batch_risk', 'eudr_due_diligence_batch_links', ['batch_risk_level'], unique=False)


def downgrade() -> None:
    """Drop EUDR tables."""
    op.drop_table('eudr_due_diligence_batch_links')
    op.drop_table('eudr_due_diligences')
    op.drop_table('eudr_georisk_snapshots')
    op.drop_table('eudr_supply_chain_links')
    op.drop_table('eudr_batches')
    op.drop_table('eudr_supply_sites')
    op.drop_table('eudr_operators')
    op.drop_table('eudr_commodities')

    # Drop enums (PostgreSQL)
    op.execute("DROP TYPE IF EXISTS eudrduediligencestatus")
    op.execute("DROP TYPE IF EXISTS eudrgeoriskssource")
    op.execute("DROP TYPE IF EXISTS eudrsupplychainlinktype")
    op.execute("DROP TYPE IF EXISTS eudroperatorrole")
    op.execute("DROP TYPE IF EXISTS eudrrisklevel")
    op.execute("DROP TYPE IF EXISTS eudrcommoditytype")
