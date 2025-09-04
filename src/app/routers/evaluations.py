from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.app.schemas.evaluation import EvaluationRead, EvaluationCreate, EvaluationUpdate
from src.app.database import get_db
from src.app.auth.dependencies import get_current_user, require_role
from src.app.models.user import User
from src.app.models.task import Task
from src.app.models.evaluation import Evaluation, EvaluationGrade
from src.app.services import evaluation_crud, evaluation_service

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
    _: User = Depends(require_role('admin')),
    task_id: Optional[int] = Query(None, description='Фильтрация по задаче'),
    user_id: Optional[int] = Query(None, description='Фильтрация по пользователю'),
    manager_id: Optional[int] = Query(None, description='Фильтрация по менеджеру'),
    grade: Optional[EvaluationGrade] = Query(None, description='Фильтрация по оценке'),
    created_before: Optional[datetime] = Query(None, description='Оценки до даты'),
    created_after: Optional[datetime] = Query(None, description='Оценки после даты'),
    limit: int = Query(10, ge=1, le=100, description='Количество записей'),
    offset: int = Query(0, ge=0, description='Смещение'),
):
    """
    Получение всех оценок
    (доступно только админам)
    """
    stmt = select(Evaluation)

    if task_id:
        stmt = stmt.where(Evaluation.task_id == task_id)
    if user_id:
        stmt = stmt.where(Evaluation.user_id == user_id)
    if manager_id:
        stmt = stmt.where(Evaluation.manager_id == manager_id)
    if grade:
        stmt = stmt.where(Evaluation.grade == grade)
    if created_before:
        stmt = stmt.where(Evaluation.created_at <= created_before)
    if created_after:
        stmt = stmt.where(Evaluation.created_at >= created_after)

    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()


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
async def get_evaluations_by_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Получить оценки для задачи"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()
    if user.team_id != task.team_id and user.role != 'admin':
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = 'Недостаточно прав'
        )
    
    stmt = select(Evaluation).where(Evaluation.task_id == task_id).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()


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


@router.get('/average/user/{user_id}')
async def get_average_grade_by_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role('manager', 'admin'))
):
    """Получить среднюю оценку пользователя"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден'
        )
    
    if current_user.team_id != user.team_id and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав'
        )
    
    avg = await evaluation_service.get_average_by_user(db, user_id)
    return {'user_id': user_id, 'average_grade': avg}


@router.get("/average/team/{team_id}")
async def average_grade_team(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role('manager', 'admin'))
):
    """Получить среднню оценку команды"""
    if current_user.team_id != team_id and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав'
        )
    
    avg = await evaluation_service.get_average_grade_by_team(db, team_id)
    return {"team_id": team_id, "average_grade": avg}
