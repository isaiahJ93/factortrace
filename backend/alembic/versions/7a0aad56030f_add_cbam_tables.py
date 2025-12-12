"""add_cbam_tables

Revision ID: 7a0aad56030f
Revises: add_multi_tenant_001
Create Date: 2025-12-12 19:52:56.316174

Adds CBAM (Carbon Border Adjustment Mechanism) tables:
- cbam_factor_sources: Reference data for emission factor datasets
- cbam_products: CN code product definitions
- cbam_declarations: Tenant-owned declaration records
- cbam_declaration_lines: Line items per declaration
- cbam_installations: Plant/facility information for specific factors
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a0aad56030f'
down_revision: Union[str, Sequence[str], None] = 'add_multi_tenant_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create CBAM tables."""

    # 1. cbam_factor_sources - Reference data (not tenant-owned)
    op.create_table('cbam_factor_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset', sa.Enum('CBAM_DEFAULT', 'CBAM_PLANT_SPECIFIC', 'EXIOBASE_2020', name='cbamfactordataset'), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('effective_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expiry_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_cbam_factor_sources'))
    )
    op.create_index('idx_cbam_factor_source_dataset_version', 'cbam_factor_sources', ['dataset', 'version'], unique=True)
    op.create_index(op.f('ix_cbam_factor_sources_dataset'), 'cbam_factor_sources', ['dataset'], unique=False)

    # 2. cbam_products - Reference data (not tenant-owned)
    op.create_table('cbam_products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cn_code', sa.String(length=10), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('sector', sa.Enum('IRON_STEEL', 'ALUMINIUM', 'CEMENT', 'FERTILISERS', 'ELECTRICITY', 'HYDROGEN', name='cbamproductsector'), nullable=False),
        sa.Column('default_factor_id', sa.Integer(), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=False, server_default='tonne'),
        sa.Column('hs_code', sa.String(length=6), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['default_factor_id'], ['emission_factors.id'], name=op.f('fk_cbam_products_default_factor_id_emission_factors'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_cbam_products'))
    )
    op.create_index('idx_cbam_product_sector_active', 'cbam_products', ['sector', 'is_active'], unique=False)
    op.create_index(op.f('ix_cbam_products_cn_code'), 'cbam_products', ['cn_code'], unique=True)
    op.create_index(op.f('ix_cbam_products_hs_code'), 'cbam_products', ['hs_code'], unique=False)
    op.create_index(op.f('ix_cbam_products_sector'), 'cbam_products', ['sector'], unique=False)

    # 3. cbam_installations - Tenant-owned
    op.create_table('cbam_installations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('installation_id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('country', sa.String(length=2), nullable=False),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('operator_name', sa.String(length=200), nullable=True),
        sa.Column('operator_id', sa.String(length=100), nullable=True),
        sa.Column('sector', sa.Enum('IRON_STEEL', 'ALUMINIUM', 'CEMENT', 'FERTILISERS', 'ELECTRICITY', 'HYDROGEN', name='cbamproductsector', create_type=False), nullable=False),
        sa.Column('specific_emission_factor', sa.Float(), nullable=True),
        sa.Column('specific_factor_unit', sa.String(length=50), nullable=True),
        sa.Column('specific_factor_valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('specific_factor_valid_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('verification_body', sa.String(length=200), nullable=True),
        sa.Column('verification_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_reference', sa.String(length=200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_cbam_installations_tenant_id_tenants'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_cbam_installations'))
    )
    op.create_index('idx_cbam_installation_tenant_country', 'cbam_installations', ['tenant_id', 'country'], unique=False)
    op.create_index('idx_cbam_installation_tenant_id', 'cbam_installations', ['tenant_id', 'installation_id'], unique=True)
    op.create_index('idx_cbam_installation_tenant_sector', 'cbam_installations', ['tenant_id', 'sector'], unique=False)
    op.create_index(op.f('ix_cbam_installations_country'), 'cbam_installations', ['country'], unique=False)
    op.create_index(op.f('ix_cbam_installations_installation_id'), 'cbam_installations', ['installation_id'], unique=False)
    op.create_index(op.f('ix_cbam_installations_sector'), 'cbam_installations', ['sector'], unique=False)
    op.create_index(op.f('ix_cbam_installations_tenant_id'), 'cbam_installations', ['tenant_id'], unique=False)

    # 4. cbam_declarations - Tenant-owned
    op.create_table('cbam_declarations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.String(length=36), nullable=False),
        sa.Column('declaration_reference', sa.String(length=100), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'SUBMITTED', 'AMENDED', 'VERIFIED', 'ARCHIVED', name='cbamdeclarationstatus'), nullable=False, server_default='DRAFT'),
        sa.Column('total_embedded_emissions_tco2e', sa.Float(), nullable=True, server_default=sa.text('0.0')),
        sa.Column('total_quantity', sa.Float(), nullable=True, server_default=sa.text('0.0')),
        sa.Column('importer_name', sa.String(length=200), nullable=True),
        sa.Column('importer_eori', sa.String(length=17), nullable=True),
        sa.Column('importer_country', sa.String(length=2), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True, server_default=sa.text('0')),
        sa.Column('verified_by', sa.String(length=200), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('submission_reference', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name=op.f('fk_cbam_declarations_created_by_user_id_users')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name=op.f('fk_cbam_declarations_tenant_id_tenants'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_cbam_declarations'))
    )
    op.create_index('idx_cbam_declaration_tenant_period', 'cbam_declarations', ['tenant_id', 'period_start', 'period_end'], unique=False)
    op.create_index('idx_cbam_declaration_tenant_ref', 'cbam_declarations', ['tenant_id', 'declaration_reference'], unique=False)
    op.create_index('idx_cbam_declaration_tenant_status', 'cbam_declarations', ['tenant_id', 'status'], unique=False)
    op.create_index(op.f('ix_cbam_declarations_declaration_reference'), 'cbam_declarations', ['declaration_reference'], unique=False)
    op.create_index(op.f('ix_cbam_declarations_importer_eori'), 'cbam_declarations', ['importer_eori'], unique=False)
    op.create_index(op.f('ix_cbam_declarations_status'), 'cbam_declarations', ['status'], unique=False)
    op.create_index(op.f('ix_cbam_declarations_tenant_id'), 'cbam_declarations', ['tenant_id'], unique=False)

    # 5. cbam_declaration_lines - Tenant-owned via parent declaration
    op.create_table('cbam_declaration_lines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('declaration_id', sa.Integer(), nullable=False),
        sa.Column('cbam_product_id', sa.Integer(), nullable=False),
        sa.Column('country_of_origin', sa.String(length=2), nullable=False),
        sa.Column('facility_id', sa.String(length=100), nullable=True),
        sa.Column('facility_name', sa.String(length=200), nullable=True),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('quantity_unit', sa.String(length=20), nullable=False, server_default='tonne'),
        sa.Column('embedded_emissions_tco2e', sa.Float(), nullable=True),
        sa.Column('emission_factor_value', sa.Float(), nullable=True),
        sa.Column('emission_factor_unit', sa.String(length=50), nullable=True),
        sa.Column('emission_factor_id', sa.Integer(), nullable=True),
        sa.Column('factor_dataset', sa.Enum('CBAM_DEFAULT', 'CBAM_PLANT_SPECIFIC', 'EXIOBASE_2020', name='cbamfactordataset', create_type=False), nullable=True),
        sa.Column('is_default_factor', sa.Boolean(), nullable=True, server_default=sa.text('1')),
        sa.Column('evidence_reference', sa.String(length=500), nullable=True),
        sa.Column('evidence_document_id', sa.Integer(), nullable=True),
        sa.Column('calculation_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('calculation_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['cbam_product_id'], ['cbam_products.id'], name=op.f('fk_cbam_declaration_lines_cbam_product_id_cbam_products'), ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['declaration_id'], ['cbam_declarations.id'], name=op.f('fk_cbam_declaration_lines_declaration_id_cbam_declarations'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['emission_factor_id'], ['emission_factors.id'], name=op.f('fk_cbam_declaration_lines_emission_factor_id_emission_factors'), ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['evidence_document_id'], ['evidence_documents.id'], name=op.f('fk_cbam_declaration_lines_evidence_document_id_evidence_documents'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_cbam_declaration_lines'))
    )
    op.create_index('idx_cbam_line_country', 'cbam_declaration_lines', ['country_of_origin'], unique=False)
    op.create_index('idx_cbam_line_declaration_product', 'cbam_declaration_lines', ['declaration_id', 'cbam_product_id'], unique=False)
    op.create_index('idx_cbam_line_factor_dataset', 'cbam_declaration_lines', ['factor_dataset'], unique=False)
    op.create_index(op.f('ix_cbam_declaration_lines_cbam_product_id'), 'cbam_declaration_lines', ['cbam_product_id'], unique=False)
    op.create_index(op.f('ix_cbam_declaration_lines_country_of_origin'), 'cbam_declaration_lines', ['country_of_origin'], unique=False)
    op.create_index(op.f('ix_cbam_declaration_lines_declaration_id'), 'cbam_declaration_lines', ['declaration_id'], unique=False)


def downgrade() -> None:
    """Drop CBAM tables."""
    op.drop_table('cbam_declaration_lines')
    op.drop_table('cbam_declarations')
    op.drop_table('cbam_installations')
    op.drop_table('cbam_products')
    op.drop_table('cbam_factor_sources')

    # Drop enums (PostgreSQL)
    op.execute("DROP TYPE IF EXISTS cbamdeclarationstatus")
    op.execute("DROP TYPE IF EXISTS cbamfactordataset")
    op.execute("DROP TYPE IF EXISTS cbamproductsector")
