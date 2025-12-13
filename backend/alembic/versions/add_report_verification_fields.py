"""Add report verification fields

Revision ID: add_verification_fields
Revises: 83e7815eabd8
Create Date: 2024-12-13

Adds verification layer fields to compliance_wizard_sessions:
- report_hash: SHA-256 content hash
- signature: Ed25519 digital signature
- signed_at: Signing timestamp
- verification_url: QR code verification URL

Part of Phase 1 + Phase 2 verification layer implementation.
See docs/features/verification-layer.md
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_verification_fields'
down_revision = '83e7815eabd8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add verification fields to compliance_wizard_sessions
    op.add_column(
        'compliance_wizard_sessions',
        sa.Column('report_hash', sa.String(64), nullable=True)
    )
    op.add_column(
        'compliance_wizard_sessions',
        sa.Column('signature', sa.String(128), nullable=True)
    )
    op.add_column(
        'compliance_wizard_sessions',
        sa.Column('signed_at', sa.DateTime(), nullable=True)
    )
    op.add_column(
        'compliance_wizard_sessions',
        sa.Column('verification_url', sa.String(255), nullable=True)
    )

    # Add index on report_hash for verification lookups
    op.create_index(
        'idx_wizard_sessions_report_hash',
        'compliance_wizard_sessions',
        ['report_hash']
    )


def downgrade() -> None:
    # Remove index
    op.drop_index(
        'idx_wizard_sessions_report_hash',
        table_name='compliance_wizard_sessions'
    )

    # Remove columns
    op.drop_column('compliance_wizard_sessions', 'verification_url')
    op.drop_column('compliance_wizard_sessions', 'signed_at')
    op.drop_column('compliance_wizard_sessions', 'signature')
    op.drop_column('compliance_wizard_sessions', 'report_hash')
