from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.app.schemas.meeting import MeetingRead, MeetingCreate, MeetingUpdate
from src.app.database import get_db
from src.app.services import meeting_crud
from src.app.auth.dependencies import get_current_user, require_role
from src.app.models.user import User
from src.app.models.meeting import Meeting

router = APIRouter(prefix='/meetings', tags=['meetings'])


async def check_meeting(
        db: AsyncSession,
        meeting_id: int,
        user: User
):
    """Общая функция для проверки встречи"""
    meeting = await meeting_crud.get_meeting(db, meeting_id)
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Встреча не найдена'
        )
    
    if user.team_id != meeting.team_id and user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав'
        )
    
    return meeting


@router.post('/', response_model=MeetingRead)
async def create_meeting(
    meeting_data: MeetingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin'))
):
    """
    Создать встречу
    (доступно только менеджерам и админам)
    """
    if user.team_id != meeting_data.team_id and user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав'
        )
    
    return await meeting_crud.create_meeting(db, meeting_data)


@router.get('/all', response_model=list[MeetingRead])
async def get_all_meetings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role('admin')),
    team_id: Optional[int] = Query(None, description='Фильтрация по команде'),
    organizer_id: Optional[int] = Query(None, description='Фильтрация по организатору'),
    scheduled_before: Optional[datetime] = Query(None, description='Встречи до даты'),
    scheduled_after: Optional[datetime] = Query(None, description='Встречи после даты'),
    limit: int = Query(10, ge=1, le=100, description='Количество записей'),
    offset: int = Query(0, ge=0, description='Смещение'),
):
    """
    Получить список всех встреч
    (доступно только админам)
    """
    stmt = select(Meeting).options(selectinload(Meeting.participants))

    if team_id:
        stmt = stmt.where(Meeting.team_id == team_id)
    if organizer_id:
        stmt = stmt.where(Meeting.organizer_id == organizer_id)
    if scheduled_before:
        stmt = stmt.where(Meeting.scheduled_at <= scheduled_before)
    if scheduled_after:
        stmt = stmt.where(Meeting.scheduled_at >= scheduled_after)

    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get('/{meeting_id}', response_model=MeetingRead)
async def get_meeting_by_id(
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Получить встречу по id"""
    meeting = await check_meeting(db, meeting_id, user)

    return meeting


@router.get('/', response_model=list[MeetingRead])
async def get_meetings_by_team(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    team_id: Optional[int] = Query(None, description='id команды'),
    organizer_id: Optional[int] = Query(None, description='Фильтрация по организатору'),
    scheduled_before: Optional[datetime] = Query(None, description='Встречи до даты'),
    scheduled_after: Optional[datetime] = Query(None, description='Встречи после даты'),
    limit: int = Query(10, ge=1, le=100, description='Количество записей'),
    offset: int = Query(0, ge=0, description='Смещение'),
):
    """Получить встречи для команды"""
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
    
    stmt = select(Meeting).options(selectinload(Meeting.participants)).where(Meeting.team_id == team_id)

    if organizer_id:
        stmt = stmt.where(Meeting.organizer_id == organizer_id)
    if scheduled_before:
        stmt = stmt.where(Meeting.scheduled_at <= scheduled_before)
    if scheduled_after:
        stmt = stmt.where(Meeting.scheduled_at >= scheduled_after)

    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.put('/{meeting_id}', response_model=MeetingRead)
async def update_meeting(
    meeting_id: int,
    meeting_data: MeetingUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin')),
):
    """
    Изменить встречу по id
    (доступно только менеджерам и админам)
    """
    meeting = await check_meeting(db, meeting_id, user)
    
    return await meeting_crud.update_meeting(db, meeting, meeting_data)


@router.delete('/{meeting_id}')
async def delete_meeting(
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin')),
):
    """
    Удалить встречу по id
    (доступно только менеджерам и админам)
    """
    meeting = await check_meeting(db, meeting_id, user)
    
    await meeting_crud.delete_meeting(db, meeting)
    return {'detail': f'Встреча {meeting_id} удалена'}
