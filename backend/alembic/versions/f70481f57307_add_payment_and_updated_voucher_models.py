"""Add payment and updated voucher models

Revision ID: f70481f57307
Revises: 2bba243fbceb
Create Date: 2024-XX-XX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'f70481f57307'
down_revision = '2bba243fbceb'
branch_labels = None
depends_on = None

def upgrade():
    # Get the bind to check database type
    bind = op.get_bind()
    
    # Only run PostgreSQL-specific code for PostgreSQL
    if bind.dialect.name == 'postgresql':
        # Check if EmissionScope enum type exists
        result = bind.execute(
            text("SELECT 1 FROM pg_type WHERE typname = 'emissionscope'")
        ).fetchone()
        
        if not result:
            # Create enum type
            op.execute("CREATE TYPE emissionscope AS ENUM ('scope_1', 'scope_2', 'scope_3')")
    
    # Add your table creation/modification code here
    # This should work for both PostgreSQL and SQLite
    pass

def downgrade():
    pass
