from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.app.schemas.evaluation import EvaluationRead, EvaluationCreate, EvaluationUpdate
from src.app.database import get_db
from src.app.auth.dependencies import get_current_user, require_role
from src.app.models.user import User
from src.app.models.task import Task
from src.app.services import evaluation_crud

router = APIRouter(prefix='/evaluations', tags=['evaluations'])


async def check_evaluation(
        db: AsyncSession,
        evaluation_id: int,
        user: User
):
    """Общая функция для проверки оценки"""
    evaluation = await evaluation_crud.get_evaluation(db, evaluation_id)
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Оценка не найдена'
        )
    
    evaluation_task = await db.execute(select(Task).where(Task.id == evaluation.task_id))
    task = evaluation_task.scalars().first()
    if user.team_id != task.team_id and user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав'
        )
    
    return evaluation


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


@router.get('/', response_model=list[EvaluationRead])
async def get_all_evaluations(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role('admin'))
):
    """
    Получение всех оценок
    (доступно только админам)
    """
    return await evaluation_crud.get_all_evaluations(db)


@router.get('/{evaluation_id}', response_model=EvaluationRead)
async def get_evaluation_by_id(
    evaluation_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Получение оценки по id"""
    evaluation = await check_evaluation(db, evaluation_id, user)

    return evaluation


@router.get('/task/{task_id}', response_model=list[EvaluationRead])
async def get_tasks_by_team(
    task_id: int = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Получить оценки для задачи"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()
    if user.team_id != task.team_id and user.role != 'admin':
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = 'Недостаточно прав'
        )
    
    return await evaluation_crud.get_evaluations_by_task(db, task_id)


@router.put('/{evaluation_id}', response_model=EvaluationRead)
async def update_evaluation(
    evaluation_id: int,
    evaluation_data: EvaluationUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin'))
):
    """
    Изменение оценки
    (доступно только менеджерам и админам)
    """
    evaluation = await check_evaluation(db, evaluation_id, user)
    
    return await evaluation_crud.update_evaluation(db, evaluation, evaluation_data)


@router.delete('/{evaluation_id}')
async def delete_evaluation(
    evaluation_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin'))
):
    """
    Удаление оценки
    (доступно только менеджерам и админам)
    """
    evaluation = await check_evaluation(db, evaluation_id, user)
    
    await evaluation_crud.delete_evaluation(db, evaluation)
    return {'detail': f'Оценка {evaluation_id} удалена'}
