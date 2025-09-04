from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.app.schemas.task import TaskRead, TaskCreate, TaskUpdate
from src.app.database import get_db
from src.app.auth.dependencies import get_current_user, require_role
from src.app.models.user import User
from src.app.models.task import TaskStatus, Task
from src.app.services import task_crud, task_service

router = APIRouter(prefix='/tasks', tags=['tasks'])


async def check_task(
        db: AsyncSession,
        task_id: int,
        user: User
):
    task = await task_crud.get_task(db, task_id)

    if task.team_id != user.team_id and user.role != 'admin':
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = 'Недостаточно прав'
        )
    
    if not task:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = 'Задача не найдена'
        )
    
    return task


@router.post('/', response_model=TaskRead)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin')),
):
    """
    Создание задачи
    (доступно только менеджерам и админам)
    """
    if task_data.team_id != user.team_id and user.role != 'admin':
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail='Пользователь должен состоять в команде'
        )
    
    return await task_crud.create_task(db, task_data)


@router.get('/', response_model=list[TaskRead])
async def get_tasks_by_team(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    team_id: Optional[int] = Query(None, description='id команды'),
    task_status: Optional[TaskStatus] = Query(None, description='Фильтраци по статусу задачи'),
    performer_id: Optional[int] = Query(None, description='Фильтрация по пользователю'),
    deadline_before: Optional[datetime] = Query(None, description='Дедлайн до даты'),
    deadline_after: Optional[datetime] = Query(None, description='Дедлайн после даты'),
    limit: int = Query(10, ge=1, le=100, description='Количество записей'),
    offset: int = Query(0, ge=0, description='Смещение'),
):
    """Получить задачи для команды"""
    if not team_id:
        if not user.team_id:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = 'Пользователь должен состоять в команде'
            )
        team_id = user.team_id
    
    if user.team_id != team_id and user.role != 'admin':
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = 'Недостаточно прав'
        )
    
    stmt = select(Task).where(Task.team_id == team_id)

    if task_status:
        stmt = stmt.where(Task.status == task_status)
    if performer_id:
        stmt = stmt.where(Task.performer_id == performer_id)
    if deadline_before:
        stmt = stmt.where(Task.deadline_date <= deadline_before)
    if deadline_after:
        stmt = stmt.where(Task.deadline_date >= deadline_after)

    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get('/all', response_model=list[TaskRead])
async def get_all_tasks(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role('admin')),
    task_status: Optional[TaskStatus] = Query(None, description='Фильтраци по статусу задачи'),
    performer_id: Optional[int] = Query(None, description='Фильтрация по пользователю'),
    team_id: Optional[int] = Query(None, description='Фильрация по команде'),
    deadline_before: Optional[datetime] = Query(None, description='Дедлайн до даты'),
    deadline_after: Optional[datetime] = Query(None, description='Дедлайн после даты'),
    limit: int = Query(10, ge=1, le=100, description='Количество записей'),
    offset: int = Query(0, ge=0, description='Смещение'),
):
    """
    Получить список всех задач
    (доступно только админам)
    """
    stmt = select(Task)

    if task_status:
        stmt = stmt.where(Task.status == task_status)
    if performer_id:
        stmt = stmt.where(Task.performer_id == performer_id)
    if team_id:
        stmt = stmt.where(Task.team_id == team_id)
    if deadline_before:
        stmt = stmt.where(Task.deadline_date <= deadline_before)
    if deadline_after:
        stmt = stmt.where(Task.deadline_date >= deadline_after)

    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get('/{task_id}', response_model=TaskRead)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Получить задачу по id"""
    task = await check_task(db, task_id, user)
    
    return task


@router.put('/{task_id}', response_model=TaskRead)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin')),
):
    """
    Изменить задачу по id
    (доступно только менеджерам и админам)
    """
    task = await check_task(db, task_id, user)
    
    return await task_crud.update_task(db, task=task, task_data=task_data)


@router.delete('/{task_id}')
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin')),
):
    """
    Удалить задачу по id
    (доступно только менеджерам и админам)
    """
    task = await check_task(db, task_id, user)
    
    await task_crud.delete_task(db, task)
    return {'detail': f'Задача {task_id} удалена'}


@router.patch('/{task_id}/status', response_model=TaskRead)
async def update_task_status(
    task_id: int,
    new_status: TaskStatus = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Изменить статус задачи"""
    task = await check_task(db, task_id, user)

    task = await task_service.change_task_status(db, task, new_status, user)
    return task
