from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.core.config import settings
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMembership
from app.schemas.auth import UserRegister, UserLogin, AuthResponse, UserResponse, WorkspaceResponse
from app.security.password import hash_password, verify_password
from app.security.jwt import create_access_token
from app.security.dependencies import get_current_user, get_current_workspace

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegister,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user, create their default workspace, and set authentication cookie."""
    # Check if email is already taken
    stmt = select(User).where(User.email == payload.email)
    existing_user = (await db.execute(stmt)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists",
        )

    # Hash password & create user
    hashed = hash_password(payload.password)
    new_user = User(
        email=payload.email,
        password_hash=hashed,
        full_name=payload.full_name,
    )
    db.add(new_user)
    await db.flush() # populate new_user.id

    # Create default workspace
    workspace_name = f"{payload.full_name or 'Personal'}'s Workspace"
    new_workspace = Workspace(
        name=workspace_name,
        owner_id=new_user.id,
    )
    db.add(new_workspace)
    await db.flush()

    # Create workspace membership
    membership = WorkspaceMembership(
        workspace_id=new_workspace.id,
        user_id=new_user.id,
        role="OWNER",
        status="ACTIVE",
    )
    db.add(membership)
    await db.commit()
    await db.refresh(new_user)
    await db.refresh(new_workspace)

    # Issue JWT token
    token = create_access_token({"sub": str(new_user.id), "email": new_user.email})

    # Set httpOnly cookie
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return AuthResponse(
        user=UserResponse.model_validate(new_user),
        workspace=WorkspaceResponse.model_validate(new_workspace),
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate with email and password, returning user data and setting auth cookie."""
    stmt = select(User).where(User.email == payload.email)
    user = (await db.execute(stmt)).scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended or inactive",
        )

    # Resolve primary workspace
    ws_stmt = (
        select(Workspace)
        .where(Workspace.owner_id == user.id)
        .order_by(Workspace.created_at.asc())
    )
    workspace = (await db.execute(ws_stmt)).scalars().first()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No workspace associated with this user account",
        )

    # Issue JWT token
    token = create_access_token({"sub": str(user.id), "email": user.email})

    # Set httpOnly cookie
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return AuthResponse(
        user=UserResponse.model_validate(user),
        workspace=WorkspaceResponse.model_validate(workspace),
    )


@router.post("/logout")
async def logout(response: Response):
    """Clear session authentication cookie."""
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=AuthResponse)
async def get_me(
    user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
):
    """Return authenticated user profile and active workspace."""
    return AuthResponse(
        user=UserResponse.model_validate(user),
        workspace=WorkspaceResponse.model_validate(workspace),
    )
