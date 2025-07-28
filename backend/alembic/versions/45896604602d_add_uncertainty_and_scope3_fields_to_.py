"""Add uncertainty and scope3 fields to emission factors

Revision ID: 45896604602d
Revises: ef8b6381b6d2
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '45896604602d'
down_revision = 'ef8b6381b6d2'
branch_labels = None
depends_on = None


def upgrade():
    # SQLite requires batch operations for ALTER TABLE
    with op.batch_alter_table('emission_factors', schema=None) as batch_op:
        batch_op.add_column(sa.Column('uncertainty_percentage', sa.Numeric(precision=5, scale=2), nullable=True))
        batch_op.add_column(sa.Column('lifecycle_stage', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('methodology', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('region', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('tier_level', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('scope3_category', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('calculation_method', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('last_verified', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('emission_factors', schema=None) as batch_op:
        batch_op.drop_column('last_verified')
        batch_op.drop_column('calculation_method')
        batch_op.drop_column('scope3_category')
        batch_op.drop_column('tier_level')
        batch_op.drop_column('region')
        batch_op.drop_column('methodology')
        batch_op.drop_column('lifecycle_stage')
        batch_op.drop_column('uncertainty_percentage')
