"""Authentication API endpoints.

Provides REST endpoints for user registration, login, token refresh, and authentication management.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
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


@router.get("/me")
async def get_current_user(
    token: str = Depends(lambda: None),  # TODO: Implement token extraction from Authorization header
) -> dict:
    """Get current authenticated user information.
    
    Returns information about the currently authenticated user based on
    the JWT token in the request.
    
    Args:
        token: JWT access token (extracted from Authorization header).
        
    Returns:
        dict: Current user information.
        
    Raises:
        HTTPException: If token is invalid or missing.
    """
    # TODO: Implement proper token extraction from Authorization header
    # TODO: Implement user lookup from database
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint not yet implemented - requires token extraction and user lookup",
    )

