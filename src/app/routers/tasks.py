from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.schemas.task import TaskRead, TaskCreate
from src.app.database import get_db
from src.app.auth.dependencies import get_current_user
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
