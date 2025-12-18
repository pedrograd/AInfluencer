"""Team collaboration API endpoints."""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.team import Team, TeamMember, TeamRole
from app.models.user import User
from app.api.auth import get_current_user_from_token

logger = logging.getLogger(__name__)

router = APIRouter()


# Helper functions for team access control
async def get_team_membership(
    team_id: UUID,
    user_id: UUID,
    db: AsyncSession,
    require_active: bool = True,
) -> TeamMember | None:
    """Get user's team membership if it exists.
    
    Args:
        team_id: UUID of the team.
        user_id: UUID of the user.
        db: Database session.
        require_active: If True, only return active memberships.
        
    Returns:
        TeamMember if found, None otherwise.
    """
    conditions = [
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id,
        TeamMember.deleted_at.is_(None),
    ]
    if require_active:
        conditions.append(TeamMember.is_active == True)
    
    query = select(TeamMember).where(and_(*conditions))
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def verify_team_access(
    team_id: UUID,
    user_id: UUID,
    db: AsyncSession,
    required_role: TeamRole | None = None,
) -> tuple[Team, TeamMember]:
    """Verify user has access to team and optionally required role.
    
    Args:
        team_id: UUID of the team.
        user_id: UUID of the user.
        db: Database session.
        required_role: Optional minimum role required (owner > admin > member > viewer).
        
    Returns:
        Tuple of (Team, TeamMember).
        
    Raises:
        HTTPException: 404 if team not found, 403 if access denied.
    """
    # Get team
    query = select(Team).where(
        and_(
            Team.id == team_id,
            Team.deleted_at.is_(None),
            Team.is_active == True,
        )
    )
    result = await db.execute(query)
    team = result.scalar_one_or_none()
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team '{team_id}' not found",
        )
    
    # Get user's membership
    membership = await get_team_membership(team_id, user_id, db, require_active=True)
    
    # Owner always has access
    if team.owner_id == user_id:
        # Create a virtual membership for owner
        membership = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role=TeamRole.OWNER.value,
            is_active=True,
        )
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this team",
        )
    
    # Check role requirement
    if required_role:
        role_hierarchy = {
            TeamRole.VIEWER: 0,
            TeamRole.MEMBER: 1,
            TeamRole.ADMIN: 2,
            TeamRole.OWNER: 3,
        }
        user_role = TeamRole(membership.role)
        if role_hierarchy.get(user_role, -1) < role_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role.value} role or higher",
            )
    
    return team, membership


# Request/Response Models
class TeamCreate(BaseModel):
    """Request model for creating a team."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Team name")
    description: str | None = Field(None, max_length=1000, description="Team description")


class TeamUpdate(BaseModel):
    """Request model for updating a team."""
    
    name: str | None = Field(None, min_length=1, max_length=255, description="Team name")
    description: str | None = Field(None, max_length=1000, description="Team description")
    is_active: bool | None = Field(None, description="Whether team is active")


class TeamResponse(BaseModel):
    """Response model for team information."""
    
    id: str
    name: str
    description: str | None
    owner_id: str
    is_active: bool
    created_at: str
    updated_at: str
    member_count: int | None = None
    
    class Config:
        from_attributes = True


class TeamMemberInvite(BaseModel):
    """Request model for inviting a user to a team."""
    
    user_id: str = Field(..., description="UUID of user to invite")
    role: TeamRole = Field(default=TeamRole.MEMBER, description="Role to assign")


class TeamMemberUpdate(BaseModel):
    """Request model for updating a team member's role."""
    
    role: TeamRole = Field(..., description="New role for the member")


class TeamMemberResponse(BaseModel):
    """Response model for team member information."""
    
    id: str
    team_id: str
    user_id: str
    role: str
    is_active: bool
    invited_by_id: str | None
    joined_at: str
    created_at: str
    updated_at: str
    user_email: str | None = None
    user_full_name: str | None = None
    
    class Config:
        from_attributes = True


# Team CRUD Endpoints
@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
) -> TeamResponse:
    """Create a new team.
    
    The creator automatically becomes the team owner and a member with OWNER role.
    """
    # Create team
    team = Team(
        name=team_data.name,
        description=team_data.description,
        owner_id=current_user.id,
    )
    db.add(team)
    await db.flush()  # Get team.id
    
    # Add creator as owner member
    owner_member = TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        role=TeamRole.OWNER.value,
        is_active=True,
        invited_by_id=None,
    )
    db.add(owner_member)
    await db.commit()
    await db.refresh(team)
    
    return TeamResponse(
        id=str(team.id),
        name=team.name,
        description=team.description,
        owner_id=str(team.owner_id),
        is_active=team.is_active,
        created_at=team.created_at.isoformat(),
        updated_at=team.updated_at.isoformat(),
        member_count=1,
    )


@router.get("", response_model=list[TeamResponse])
async def list_teams(
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[TeamResponse]:
    """List all teams the current user is a member of or owns."""
    # Get teams where user is owner or member
    query = (
        select(Team)
        .join(TeamMember, Team.id == TeamMember.team_id, isouter=True)
        .where(
            and_(
                or_(
                    Team.owner_id == current_user.id,
                    TeamMember.user_id == current_user.id,
                ),
                Team.deleted_at.is_(None),
                Team.is_active == True,
                or_(
                    TeamMember.deleted_at.is_(None),
                    TeamMember.id.is_(None),  # Owner without membership record
                ),
                or_(
                    TeamMember.is_active == True,
                    TeamMember.id.is_(None),
                ),
            )
        )
        .distinct()
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(query)
    teams = result.scalars().all()
    
    # Get member counts
    team_responses = []
    for team in teams:
        member_count_query = select(func.count(TeamMember.id)).where(
            and_(
                TeamMember.team_id == team.id,
                TeamMember.deleted_at.is_(None),
                TeamMember.is_active == True,
            )
        )
        member_count_result = await db.execute(member_count_query)
        member_count = member_count_result.scalar() or 0
        
        # Add owner if not in members
        if team.owner_id not in [m.user_id for m in team.members if m.is_active]:
            member_count += 1
        
        team_responses.append(
            TeamResponse(
                id=str(team.id),
                name=team.name,
                description=team.description,
                owner_id=str(team.owner_id),
                is_active=team.is_active,
                created_at=team.created_at.isoformat(),
                updated_at=team.updated_at.isoformat(),
                member_count=member_count,
            )
        )
    
    return team_responses


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: UUID,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
) -> TeamResponse:
    """Get team details."""
    team, _ = await verify_team_access(team_id, current_user.id, db)
    
    # Get member count
    member_count_query = select(func.count(TeamMember.id)).where(
        and_(
            TeamMember.team_id == team.id,
            TeamMember.deleted_at.is_(None),
            TeamMember.is_active == True,
        )
    )
    member_count_result = await db.execute(member_count_query)
    member_count = member_count_result.scalar() or 0
    
    # Add owner if not in members
    if team.owner_id not in [m.user_id for m in team.members if m.is_active]:
        member_count += 1
    
    return TeamResponse(
        id=str(team.id),
        name=team.name,
        description=team.description,
        owner_id=str(team.owner_id),
        is_active=team.is_active,
        created_at=team.created_at.isoformat(),
        updated_at=team.updated_at.isoformat(),
        member_count=member_count,
    )


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: UUID,
    team_data: TeamUpdate,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
) -> TeamResponse:
    """Update team information. Requires ADMIN or OWNER role."""
    team, membership = await verify_team_access(
        team_id, current_user.id, db, required_role=TeamRole.ADMIN
    )
    
    # Update fields
    if team_data.name is not None:
        team.name = team_data.name
    if team_data.description is not None:
        team.description = team_data.description
    if team_data.is_active is not None:
        team.is_active = team_data.is_active
    
    await db.commit()
    await db.refresh(team)
    
    # Get member count
    member_count_query = select(func.count(TeamMember.id)).where(
        and_(
            TeamMember.team_id == team.id,
            TeamMember.deleted_at.is_(None),
            TeamMember.is_active == True,
        )
    )
    member_count_result = await db.execute(member_count_query)
    member_count = member_count_result.scalar() or 0
    
    if team.owner_id not in [m.user_id for m in team.members if m.is_active]:
        member_count += 1
    
    return TeamResponse(
        id=str(team.id),
        name=team.name,
        description=team.description,
        owner_id=str(team.owner_id),
        is_active=team.is_active,
        created_at=team.created_at.isoformat(),
        updated_at=team.updated_at.isoformat(),
        member_count=member_count,
    )


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_team(
    team_id: UUID,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """Delete a team. Only the owner can delete."""
    team, membership = await verify_team_access(team_id, current_user.id, db)
    
    # Only owner can delete
    if team.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team owner can delete the team",
        )
    
    # Soft delete
    team.deleted_at = datetime.utcnow()
    await db.commit()


# Team Member Management Endpoints
@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(
    team_id: UUID,
    invite_data: TeamMemberInvite,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
) -> TeamMemberResponse:
    """Invite a user to join the team. Requires ADMIN or OWNER role."""
    team, membership = await verify_team_access(
        team_id, current_user.id, db, required_role=TeamRole.ADMIN
    )
    
    # Verify user exists
    user_query = select(User).where(
        and_(
            User.id == UUID(invite_data.user_id),
            User.deleted_at.is_(None),
            User.is_active == True,
        )
    )
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{invite_data.user_id}' not found",
        )
    
    # Check if already a member
    existing = await get_team_membership(team_id, UUID(invite_data.user_id), db, require_active=False)
    if existing and existing.deleted_at.is_(None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this team",
        )
    
    # Create membership
    member = TeamMember(
        team_id=team_id,
        user_id=UUID(invite_data.user_id),
        role=invite_data.role.value,
        is_active=True,
        invited_by_id=current_user.id,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    
    return TeamMemberResponse(
        id=str(member.id),
        team_id=str(member.team_id),
        user_id=str(member.user_id),
        role=member.role,
        is_active=member.is_active,
        invited_by_id=str(member.invited_by_id) if member.invited_by_id else None,
        joined_at=member.joined_at.isoformat(),
        created_at=member.created_at.isoformat(),
        updated_at=member.updated_at.isoformat(),
        user_email=user.email,
        user_full_name=user.full_name,
    )


@router.get("/{team_id}/members", response_model=list[TeamMemberResponse])
async def list_members(
    team_id: UUID,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
) -> list[TeamMemberResponse]:
    """List all team members."""
    team, _ = await verify_team_access(team_id, current_user.id, db)
    
    query = (
        select(TeamMember, User)
        .join(User, TeamMember.user_id == User.id)
        .where(
            and_(
                TeamMember.team_id == team_id,
                TeamMember.deleted_at.is_(None),
                TeamMember.is_active == True,
            )
        )
    )
    result = await db.execute(query)
    rows = result.all()
    
    members = []
    for member, user in rows:
        members.append(
            TeamMemberResponse(
                id=str(member.id),
                team_id=str(member.team_id),
                user_id=str(member.user_id),
                role=member.role,
                is_active=member.is_active,
                invited_by_id=str(member.invited_by_id) if member.invited_by_id else None,
                joined_at=member.joined_at.isoformat(),
                created_at=member.created_at.isoformat(),
                updated_at=member.updated_at.isoformat(),
                user_email=user.email,
                user_full_name=user.full_name,
            )
        )
    
    # Add owner if not in members list
    owner_query = select(User).where(User.id == team.owner_id)
    owner_result = await db.execute(owner_query)
    owner = owner_result.scalar_one_or_none()
    
    if owner and team.owner_id not in [UUID(m.user_id) for m in members]:
        members.insert(
            0,
            TeamMemberResponse(
                id="",  # Virtual member
                team_id=str(team.id),
                user_id=str(team.owner_id),
                role=TeamRole.OWNER.value,
                is_active=True,
                invited_by_id=None,
                joined_at=team.created_at.isoformat(),
                created_at=team.created_at.isoformat(),
                updated_at=team.updated_at.isoformat(),
                user_email=owner.email,
                user_full_name=owner.full_name,
            )
        )
    
    return members


@router.patch("/{team_id}/members/{member_id}", response_model=TeamMemberResponse)
async def update_member_role(
    team_id: UUID,
    member_id: UUID,
    member_data: TeamMemberUpdate,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
) -> TeamMemberResponse:
    """Update a team member's role. Requires ADMIN or OWNER role."""
    team, membership = await verify_team_access(
        team_id, current_user.id, db, required_role=TeamRole.ADMIN
    )
    
    # Get member
    query = select(TeamMember).where(
        and_(
            TeamMember.id == member_id,
            TeamMember.team_id == team_id,
            TeamMember.deleted_at.is_(None),
        )
    )
    result = await db.execute(query)
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team member '{member_id}' not found",
        )
    
    # Cannot change owner role
    if member.role == TeamRole.OWNER.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change owner role",
        )
    
    # Update role
    member.role = member_data.role.value
    await db.commit()
    await db.refresh(member)
    
    # Get user info
    user_query = select(User).where(User.id == member.user_id)
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    return TeamMemberResponse(
        id=str(member.id),
        team_id=str(member.team_id),
        user_id=str(member.user_id),
        role=member.role,
        is_active=member.is_active,
        invited_by_id=str(member.invited_by_id) if member.invited_by_id else None,
        joined_at=member.joined_at.isoformat(),
        created_at=member.created_at.isoformat(),
        updated_at=member.updated_at.isoformat(),
        user_email=user.email if user else None,
        user_full_name=user.full_name if user else None,
    )


@router.delete("/{team_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def remove_member(
    team_id: UUID,
    member_id: UUID,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db),
):
    """Remove a member from the team. Requires ADMIN or OWNER role. Members can remove themselves."""
    team, membership = await verify_team_access(team_id, current_user.id, db)
    
    # Get member
    query = select(TeamMember).where(
        and_(
            TeamMember.id == member_id,
            TeamMember.team_id == team_id,
            TeamMember.deleted_at.is_(None),
        )
    )
    result = await db.execute(query)
    member = result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team member '{member_id}' not found",
        )
    
    # Check permissions: admin/owner can remove anyone, members can remove themselves
    is_self = member.user_id == current_user.id
    is_admin_or_owner = membership.role in [TeamRole.ADMIN.value, TeamRole.OWNER.value] or team.owner_id == current_user.id
    
    if not (is_self or is_admin_or_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to remove this member",
        )
    
    # Cannot remove owner
    if member.role == TeamRole.OWNER.value or member.user_id == team.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove team owner",
        )
    
    # Soft delete
    member.deleted_at = datetime.utcnow()
    member.is_active = False
    await db.commit()
