"""create teams and team_members tables, add team_id to characters

Revision ID: 003_create_teams
Revises: 002_create_api_keys
Create Date: 2025-12-17 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_create_teams'
down_revision: Union[str, None] = '002_create_api_keys'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create teams table
    op.create_table(
        'teams',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for teams
    op.create_index('ix_teams_name', 'teams', ['name'])
    op.create_index('ix_teams_owner_id', 'teams', ['owner_id'])
    
    # Create foreign key constraint for teams.owner_id
    op.create_foreign_key(
        'fk_teams_owner_id',
        'teams', 'users',
        ['owner_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Create team_members table
    op.create_table(
        'team_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='member'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('invited_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for team_members
    op.create_index('ix_team_members_team_id', 'team_members', ['team_id'])
    op.create_index('ix_team_members_user_id', 'team_members', ['user_id'])
    
    # Create unique constraint: one active membership per user per team
    op.create_unique_constraint(
        'uq_team_members_team_user_active',
        'team_members',
        ['team_id', 'user_id'],
        postgresql_where=sa.text("deleted_at IS NULL AND is_active = true")
    )
    
    # Create foreign key constraints for team_members
    op.create_foreign_key(
        'fk_team_members_team_id',
        'team_members', 'teams',
        ['team_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_team_members_user_id',
        'team_members', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_team_members_invited_by_id',
        'team_members', 'users',
        ['invited_by_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Add team_id column to characters table (optional, for team-shared characters)
    op.add_column('characters',
        sa.Column('team_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Create index for characters.team_id
    op.create_index('ix_characters_team_id', 'characters', ['team_id'])
    
    # Create foreign key constraint for characters.team_id
    op.create_foreign_key(
        'fk_characters_team_id',
        'characters', 'teams',
        ['team_id'], ['id'],
        ondelete='SET NULL'  # If team is deleted, set team_id to NULL (character becomes personal)
    )


def downgrade() -> None:
    # Remove foreign key constraint and column for characters.team_id
    op.drop_constraint('fk_characters_team_id', 'characters', type_='foreignkey')
    op.drop_index('ix_characters_team_id', table_name='characters')
    op.drop_column('characters', 'team_id')
    
    # Remove foreign key constraints for team_members
    op.drop_constraint('fk_team_members_invited_by_id', 'team_members', type_='foreignkey')
    op.drop_constraint('fk_team_members_user_id', 'team_members', type_='foreignkey')
    op.drop_constraint('fk_team_members_team_id', 'team_members', type_='foreignkey')
    op.drop_constraint('uq_team_members_team_user_active', 'team_members', type_='unique')
    
    # Drop indexes for team_members
    op.drop_index('ix_team_members_user_id', table_name='team_members')
    op.drop_index('ix_team_members_team_id', table_name='team_members')
    
    # Drop team_members table
    op.drop_table('team_members')
    
    # Remove foreign key constraint for teams
    op.drop_constraint('fk_teams_owner_id', 'teams', type_='foreignkey')
    
    # Drop indexes for teams
    op.drop_index('ix_teams_owner_id', table_name='teams')
    op.drop_index('ix_teams_name', table_name='teams')
    
    # Drop teams table
    op.drop_table('teams')
