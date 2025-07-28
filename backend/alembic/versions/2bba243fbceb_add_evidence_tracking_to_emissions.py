"""add evidence tracking to emissions

Revision ID: 2bba243fbceb
Revises: 45896604602d
Create Date: 2025-07-12 14:18:35.587545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2bba243fbceb'
down_revision: Union[str, Sequence[str], None] = '45896604602d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
