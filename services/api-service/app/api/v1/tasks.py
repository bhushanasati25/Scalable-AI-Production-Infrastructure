"""
Tasks API — CRUD endpoints for async task management.
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db_session
from app.models.database import Task

sys.path.insert(0, "/app")
from shared.common.exceptions import NotFoundError
from shared.common.logging import get_logger
from shared.common.schemas import (
    APIResponse,
    PaginatedResponse,
    TaskCreate,
    TaskResponse,
    TaskStatus,
)

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/",
    response_model=APIResponse[TaskResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[TaskResponse]:
    """Create a new async task."""
    # TODO: get owner_id from auth token
    owner_id = uuid.uuid4()  # placeholder

    task = Task(
        name=task_data.name,
        task_type=task_data.task_type,
        payload=task_data.payload,
        priority=task_data.priority,
        owner_id=owner_id,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)

    logger.info("Task created", task_id=str(task.id), task_type=task.task_type)

    return APIResponse(
        data=TaskResponse(
            id=task.id,
            name=task.name,
            task_type=task.task_type,
            status=TaskStatus(task.status),
            payload=task.payload,
            created_at=task.created_at,
        ),
        message="Task created successfully",
    )


@router.get("/", response_model=APIResponse[PaginatedResponse[TaskResponse]])
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: TaskStatus | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[PaginatedResponse[TaskResponse]]:
    """List tasks with pagination and optional status filter."""
    query = select(Task)

    if status_filter:
        query = query.where(Task.status == status_filter.value)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.order_by(Task.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    tasks = result.scalars().all()

    pages = max(1, (total + page_size - 1) // page_size)

    return APIResponse(
        data=PaginatedResponse(
            items=[
                TaskResponse(
                    id=t.id,
                    name=t.name,
                    task_type=t.task_type,
                    status=TaskStatus(t.status),
                    payload=t.payload,
                    result=t.result,
                    error_message=t.error_message,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                    started_at=t.started_at,
                    completed_at=t.completed_at,
                )
                for t in tasks
            ],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        ),
    )


@router.get("/{task_id}", response_model=APIResponse[TaskResponse])
async def get_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[TaskResponse]:
    """Get a task by ID."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise NotFoundError("Task", str(task_id))

    return APIResponse(
        data=TaskResponse(
            id=task.id,
            name=task.name,
            task_type=task.task_type,
            status=TaskStatus(task.status),
            payload=task.payload,
            result=task.result,
            error_message=task.error_message,
            created_at=task.created_at,
            updated_at=task.updated_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
        ),
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Cancel a pending task."""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise NotFoundError("Task", str(task_id))

    if task.status not in ("pending", "processing"):
        return  # Already terminal

    task.status = "cancelled"
    task.completed_at = datetime.utcnow()
    logger.info("Task cancelled", task_id=str(task_id))
