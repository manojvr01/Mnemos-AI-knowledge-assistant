import uuid
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.security.jwt import decode_access_token
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMembership


async def get_token_from_request(request: Request) -> str:
    """Extract token from Authorization header or httpOnly cookie."""
    # Check Authorization header first (explicit bearer override)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]

    # Fallback to httpOnly cookie
    token = request.cookies.get("access_token")
    if token:
        return token
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication credentials were not provided",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    token: str = Depends(get_token_from_request),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Authenticate and return the current active User model."""
    try:
        payload = decode_access_token(token)
        user_id_str: str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        user_id = uuid.UUID(user_id_str)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = select(User).where(User.id == user_id, User.status == "ACTIVE")
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


async def get_current_workspace(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    """Resolve and verify user's active workspace."""
    # Check if a specific workspace was requested via header
    requested_ws_id = request.headers.get("X-Workspace-ID")
    
    if requested_ws_id:
        try:
            ws_uuid = uuid.UUID(requested_ws_id)
            # Verify membership
            stmt = (
                select(Workspace)
                .join(WorkspaceMembership, WorkspaceMembership.workspace_id == Workspace.id)
                .where(
                    Workspace.id == ws_uuid,
                    WorkspaceMembership.user_id == user.id,
                    WorkspaceMembership.status == "ACTIVE"
                )
            )
            result = await db.execute(stmt)
            workspace = result.scalar_one_or_none()
            if workspace:
                return workspace
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to requested workspace",
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid workspace ID format",
            )

    # Default to user's primary owned workspace
    stmt = (
        select(Workspace)
        .where(Workspace.owner_id == user.id)
        .order_by(Workspace.created_at.asc())
    )
    result = await db.execute(stmt)
    workspace = result.scalars().first()

    if not workspace:
        # Fallback to any active membership
        stmt = (
            select(Workspace)
            .join(WorkspaceMembership, WorkspaceMembership.workspace_id == Workspace.id)
            .where(WorkspaceMembership.user_id == user.id, WorkspaceMembership.status == "ACTIVE")
        )
        result = await db.execute(stmt)
        workspace = result.scalars().first()

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active workspace found for user",
        )
    return workspace
