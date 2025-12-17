"""add user_id to characters for multi-user support

Revision ID: 001_add_user_id
Revises: 
Create Date: 2025-12-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_add_user_id'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add user_id column to characters table
    # First, add as nullable to handle existing data
    op.add_column('characters', 
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Create index for better query performance
    op.create_index('ix_characters_user_id', 'characters', ['user_id'])
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_characters_user_id',
        'characters', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Note: For existing characters, user_id will be NULL
    # In a production scenario, you would need to:
    # 1. Create a default user or assign existing characters to a user
    # 2. Update all NULL user_id values
    # 3. Then make the column NOT NULL
    # For now, we keep it nullable to allow migration without data loss


def downgrade() -> None:
    # Remove foreign key constraint
    op.drop_constraint('fk_characters_user_id', 'characters', type_='foreignkey')
    
    # Drop index
    op.drop_index('ix_characters_user_id', table_name='characters')
    
    # Remove column
    op.drop_column('characters', 'user_id')
