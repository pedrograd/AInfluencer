"""Authentication API endpoints.

Provides REST endpoints for user registration, login, token refresh, and authentication management.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import auth_service

router = APIRouter()


class RegisterRequest(BaseModel):
    """User registration request model."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (minimum 8 characters)")
    full_name: str | None = Field(None, max_length=255, description="User full name (optional)")


class RegisterResponse(BaseModel):
    """User registration response model."""

    id: str
    email: str
    full_name: str | None
    is_verified: bool
    created_at: str | None


class LoginRequest(BaseModel):
    """User login request model."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    """User login response model."""

    user: dict
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int | None = None


class TokenRefreshRequest(BaseModel):
    """Token refresh request model."""

    refresh_token: str = Field(..., description="Refresh token")


class TokenRefreshResponse(BaseModel):
    """Token refresh response model."""

    access_token: str
    token_type: str
    expires_in: int


class UserResponse(BaseModel):
    """Current user response model."""

    id: str
    email: str
    full_name: str | None
    is_verified: bool
    is_active: bool
    created_at: str | None
    last_login_at: str | None


async def get_current_user_from_token(
    authorization: str | None = Header(None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and verify JWT token from Authorization header, return current user.
    
    This dependency extracts the Bearer token from the Authorization header,
    verifies it, and returns the authenticated user from the database.
    
    Args:
        authorization: Authorization header value (format: "Bearer <token>").
        db: Database session.
        
    Returns:
        User: Authenticated user object.
        
    Raises:
        HTTPException: If token is missing, invalid, or user not found.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    # Verify token
    payload = await auth_service.verify_token(token, token_type="access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user ID from token
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    return user


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    """Register a new user.
    
    Creates a new user account with email and password. The user will need to
    verify their email before full account access is granted.
    
    Args:
        request: Registration request with email, password, and optional full name.
        db: Database session.
        
    Returns:
        RegisterResponse: Created user information.
        
    Raises:
        HTTPException: If email already exists or password is invalid.
    """
    try:
        user_data = await auth_service.register_user(
            db=db,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
        )
        return RegisterResponse(**user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """Authenticate user and return tokens.
    
    Validates user credentials and returns JWT access and refresh tokens
    for authenticated requests.
    
    Args:
        request: Login request with email and password.
        db: Database session.
        
    Returns:
        LoginResponse: User information and authentication tokens.
        
    Raises:
        HTTPException: If credentials are invalid or user is inactive.
    """
    auth_result = await auth_service.authenticate_user(
        db=db,
        email=request.email,
        password=request.password,
    )
    
    if not auth_result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    return LoginResponse(**auth_result)


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    request: TokenRefreshRequest,
) -> TokenRefreshResponse:
    """Refresh access token using refresh token.
    
    Generates a new access token using a valid refresh token. The refresh token
    must not be expired.
    
    Args:
        request: Token refresh request with refresh token.
        
    Returns:
        TokenRefreshResponse: New access token and metadata.
        
    Raises:
        HTTPException: If refresh token is invalid or expired.
    """
    payload = await auth_service.verify_token(request.refresh_token, token_type="refresh")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    # Generate new access token
    user_id = payload.get("sub")
    email = payload.get("email")
    
    if not user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    tokens = auth_service._generate_tokens(user_id, email)
    
    return TokenRefreshResponse(
        access_token=tokens["access_token"],
        token_type=tokens["token_type"],
        expires_in=tokens.get("expires_in", auth_service.access_token_expire_minutes * 60),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: User = Depends(get_current_user_from_token),
) -> UserResponse:
    """Get current authenticated user information.
    
    Returns information about the currently authenticated user based on
    the JWT token in the Authorization header.
    
    Args:
        current_user: Authenticated user (from token dependency).
        
    Returns:
        UserResponse: Current user information.
        
    Raises:
        HTTPException: If token is invalid, missing, or user is inactive.
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_verified=current_user.is_verified,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None,
        last_login_at=current_user.last_login_at.isoformat() if current_user.last_login_at else None,
    )

