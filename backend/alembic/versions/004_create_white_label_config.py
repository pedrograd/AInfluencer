"""create white_label_config table

Revision ID: 004_create_white_label_config
Revises: 003_create_teams
Create Date: 2025-12-17 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004_create_white_label_config'
down_revision: Union[str, None] = '003_create_teams'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create white_label_config table (singleton pattern - single row)
    op.create_table(
        'white_label_config',
        sa.Column('id', sa.String(36), primary_key=True, server_default='00000000-0000-0000-0000-000000000001'),
        sa.Column('app_name', sa.String(255), nullable=False, server_default='AInfluencer'),
        sa.Column('app_description', sa.Text, nullable=True),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('favicon_url', sa.String(500), nullable=True),
        sa.Column('primary_color', sa.String(7), nullable=False, server_default='#6366f1'),
        sa.Column('secondary_color', sa.String(7), nullable=False, server_default='#8b5cf6'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    
    # Insert default row
    op.execute("""
        INSERT INTO white_label_config (id, app_name, primary_color, secondary_color, is_active)
        VALUES ('00000000-0000-0000-0000-000000000001', 'AInfluencer', '#6366f1', '#8b5cf6', true)
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    # Drop white_label_config table
    op.drop_table('white_label_config')
