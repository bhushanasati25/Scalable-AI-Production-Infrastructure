"""
Users API — User management endpoints.
"""

from __future__ import annotations

import sys
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db_session
from app.models.database import User

sys.path.insert(0, "/app")
from shared.common.exceptions import ConflictError, NotFoundError
from shared.common.logging import get_logger
from shared.common.schemas import (
    APIResponse,
    PaginatedResponse,
    UserCreate,
    UserResponse,
)

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[UserResponse]:
    """Create a new user account."""
    # Check for existing email
    existing = await db.execute(select(User).where(User.email == user_data.email))
    if existing.scalar_one_or_none():
        raise ConflictError(f"User with email '{user_data.email}' already exists")

    # TODO: Hash password properly with argon2
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=f"hashed_{user_data.password}",  # placeholder
        is_active=user_data.is_active,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    logger.info("User created", user_id=str(user.id), email=user.email)

    return APIResponse(
        data=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            role=user.role,
            created_at=user.created_at,
        ),
        message="User created successfully",
    )


@router.get("/", response_model=APIResponse[PaginatedResponse[UserResponse]])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[PaginatedResponse[UserResponse]]:
    """List users with pagination."""
    count_query = select(func.count()).select_from(User)
    total = (await db.execute(count_query)).scalar() or 0

    query = (
        select(User)
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    users = result.scalars().all()

    pages = max(1, (total + page_size - 1) // page_size)

    return APIResponse(
        data=PaginatedResponse(
            items=[
                UserResponse(
                    id=u.id,
                    email=u.email,
                    full_name=u.full_name,
                    is_active=u.is_active,
                    role=u.role,
                    created_at=u.created_at,
                    updated_at=u.updated_at,
                )
                for u in users
            ],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        ),
    )


@router.get("/{user_id}", response_model=APIResponse[UserResponse])
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[UserResponse]:
    """Get a user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundError("User", str(user_id))

    return APIResponse(
        data=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            role=user.role,
            created_at=user.created_at,
            updated_at=user.updated_at,
        ),
    )
