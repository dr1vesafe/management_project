from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.app.schemas.evaluation import EvaluationRead, EvaluationCreate
from src.app.database import get_db
from src.app.auth.dependencies import get_current_user, require_role
from src.app.models.user import User
from src.app.models.task import Task
from src.app.services import evaluation_crud

router = APIRouter(prefix='/evaluations', tags=['evaluations'])


@router.post('/', response_model=EvaluationRead)
async def create_evaluation(
    evaluation_data: EvaluationCreate,
    db: AsyncSession = Depends(get_db),
    manager: User = Depends(require_role('manager', 'admin')),
):
    """
    Создание оценки
    (доступно только менеджерам и админам)
    """
    evaluation_task = await db.execute(select(Task).where(Task.id == evaluation_data.task_id))
    task = evaluation_task.scalars().first()
    if task.team_id != manager.team_id and manager.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Невозможно давать оценки задачам не своей команды'
        )
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Задача не найдена'
        )
    
    evaluation_user = await db.execute(select(User).where(User.id == task.performer_id))
    user = evaluation_user.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден'
        )
    
    if user.team_id != manager.team_id and manager.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Невозможно давать оценки участникам других команд'
        )
    
    evaluation_data.manager_id = manager.id
    evaluation_data.user_id = task.performer_id
    evaluation = await evaluation_crud.create_evaluation(db, evaluation_data)
    db.commit()
    db.refresh(evaluation)
    return evaluation
