from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.schemas.task import TaskRead, TaskCreate, TaskUpdate
from src.app.database import get_db
from src.app.auth.dependencies import get_current_user, require_role
from src.app.models.user import User
from src.app.services import task_crud

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
):
    """Получить задачи для команды"""
    if not team_id:
        if not user.team_id:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = 'Пользователь должен состоять в команде'
            )
        return await task_crud.get_tasks_by_team(db, user.team_id)
    
    if user.team_id != team_id and user.role != 'admin':
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = 'Недостаточно прав'
        )
    
    return await task_crud.get_tasks_by_team(db, team_id)


@router.get('/performer', response_model=list[TaskRead])
async def get_tasks_by_performer(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    performer_id: Optional[int] = Query(None, description='id пользователя'),
):
    """Получить задачи для пользователя"""
    if not performer_id:
        return await task_crud.get_tasks_by_team(db, user.id)
    
    if user.id != performer_id and user.role != 'admin':
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = 'Недостаточно прав'
        )
    
    return await task_crud.get_tasks_by_performer(db, performer_id)


@router.get('/all', response_model=list[TaskRead])
async def get_all_tasks(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role('admin'))
):
    """
    Получить список всех задач
    (доступно только админам)
    """
    return await task_crud.get_tasks(db)


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
