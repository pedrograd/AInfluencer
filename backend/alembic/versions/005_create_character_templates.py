"""create character_templates table

Revision ID: 005_create_character_templates
Revises: 004_create_white_label_config
Create Date: 2025-12-17 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

# revision identifiers, used by Alembic.
revision: str = '005_create_character_templates'
down_revision: Union[str, None] = '004_create_white_label_config'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create character_templates table
    op.create_table(
        'character_templates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('creator_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('tags', ARRAY(sa.String), nullable=True),
        sa.Column('template_data', JSONB, nullable=False),
        sa.Column('preview_image_url', sa.Text, nullable=True),
        sa.Column('is_featured', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_public', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('download_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('rating', sa.Numeric(3, 2), nullable=True),
        sa.Column('rating_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("LENGTH(name) >= 1 AND LENGTH(name) <= 255", name="template_name_length_check"),
        sa.CheckConstraint("rating IS NULL OR (rating >= 0.0 AND rating <= 5.0)", name="rating_range_check"),
        sa.CheckConstraint("download_count >= 0", name="download_count_check"),
        sa.CheckConstraint("rating_count >= 0", name="rating_count_check"),
    )
    
    # Create indexes
    op.create_index('ix_character_templates_creator_id', 'character_templates', ['creator_id'])
    op.create_index('ix_character_templates_name', 'character_templates', ['name'])
    op.create_index('ix_character_templates_category', 'character_templates', ['category'])
    op.create_index('ix_character_templates_is_featured', 'character_templates', ['is_featured'])
    op.create_index('ix_character_templates_is_public', 'character_templates', ['is_public'])
    op.create_index('ix_character_templates_created_at', 'character_templates', ['created_at'])


def downgrade() -> None:
    # Drop character_templates table
    op.drop_table('character_templates')
