from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.schemas.task import TaskRead, TaskCreate
from src.app.database import get_db
from src.app.auth.dependencies import get_current_user, require_role
from src.app.models.user import User
from src.app.services import task_crud

router = APIRouter(prefix='/tasks', tags=['tasks'])


@router.post('/', response_model=TaskRead)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Создание задачи"""
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
    team_id: Optional[int] = None,
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
