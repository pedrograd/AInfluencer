"""create api_keys table for third-party integrations

Revision ID: 002_create_api_keys
Revises: 001_add_user_id
Create Date: 2025-12-17 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_create_api_keys'
down_revision: Union[str, None] = '001_add_user_id'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('key_hash', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scopes', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('rate_limit', sa.Integer, nullable=False, server_default='1000'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes
    op.create_index('ix_api_keys_key_hash', 'api_keys', ['key_hash'])
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'])
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_api_keys_user_id',
        'api_keys', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Remove foreign key constraint
    op.drop_constraint('fk_api_keys_user_id', 'api_keys', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('ix_api_keys_user_id', table_name='api_keys')
    op.drop_index('ix_api_keys_key_hash', table_name='api_keys')
    
    # Drop table
    op.drop_table('api_keys')
