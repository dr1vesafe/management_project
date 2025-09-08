from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from src.app.schemas.meeting import MeetingRead, MeetingCreate, MeetingUpdate
from src.app.database import get_db
from src.app.services import meeting_crud
from src.app.auth.dependencies import get_current_user, require_role
from src.app.models.user import User
from src.app.models.meeting import Meeting
from src.app.models.meeting_participants import MeetingParticipant

router = APIRouter(prefix='/meetings', tags=['meetings'])
templates = Jinja2Templates(directory='src/app/templates')



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


# Маршруты для пользователей
@router.get('/')
async def meetings_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    status: Optional[str] = Query(None, regex='^(past|upcoming)?$'),
    my_meetings: bool = Query(False),
    page: int = Query(1, ge=1)
):
    """Страница со встречами команды"""
    limit = 10
    offset = (page - 1) * limit

    query = select(Meeting).options(selectinload(Meeting.participants).selectinload(MeetingParticipant.user))
    count_query = select(func.count(Meeting.id))

    query = query.where(Meeting.team_id == user.team_id)
    count_query = count_query.where(Meeting.team_id == user.team_id)

    now = datetime.utcnow()

    if status == 'past':
        query = query.where(Meeting.scheduled_at < now)
        count_query = count_query.where(Meeting.scheduled_at < now)
    elif status == 'upcoming':
        query = query.where(Meeting.scheduled_at >= now)
        count_query = count_query.where(Meeting.scheduled_at >= now)

    if my_meetings:
        query = query.join(MeetingParticipant).where(MeetingParticipant.user_id == user.id)
        count_query = count_query.join(MeetingParticipant).where(MeetingParticipant.user_id == user.id)

    total_meetings = await db.scalar(count_query)
    total_pages = max((total_meetings + limit - 1) // limit, 1)

    meetings = (await db.execute(query.offset(offset).limit(limit))).scalars().all()

    return templates.TemplateResponse(
        'meeting/meetings.html',
        {
            'request': request,
            'meetings': meetings,
            'status': status or '',
            'my_meetings': my_meetings,
            'page': page,
            'total_pages': total_pages,
            'user': user
        }
    )


# Маршруты для администраторов
@router.post('/admin/create', response_model=MeetingRead)
async def create_meeting(
    meeting_data: MeetingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('admin'))
):
    """
    Создать встречу
    (доступно только админам)
    """
    if meeting_data.team_id:
        if user.team_id != meeting_data.team_id and user.role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Недостаточно прав'
            )
    
    return await meeting_crud.create_meeting(db, meeting_data, user)


@router.get('/admin/all', response_model=list[MeetingRead])
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


@router.get('/admin/{meeting_id}', response_model=MeetingRead)
async def get_meeting_by_id(
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('admin'))
):
    """Получить встречу по id"""
    meeting = await check_meeting(db, meeting_id, user)

    return meeting


@router.get('/admin/{team_id}', response_model=list[MeetingRead])
async def get_meetings_by_team(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    organizer_id: Optional[int] = Query(None, description='Фильтрация по организатору'),
    scheduled_before: Optional[datetime] = Query(None, description='Встречи до даты'),
    scheduled_after: Optional[datetime] = Query(None, description='Встречи после даты'),
    limit: int = Query(10, ge=1, le=100, description='Количество записей'),
    offset: int = Query(0, ge=0, description='Смещение'),
):
    """Получить встречи для команды"""
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
    user: User = Depends(require_role('admin')),
):
    """
    Изменить встречу по id
    (доступно толькои админам)
    """
    meeting = await check_meeting(db, meeting_id, user)
    
    return await meeting_crud.update_meeting(db, meeting, meeting_data)


@router.delete('/{meeting_id}')
async def delete_meeting(
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('admin')),
):
    """
    Удалить встречу по id
    (доступно только админам)
    """
    meeting = await check_meeting(db, meeting_id, user)
    
    await meeting_crud.delete_meeting(db, meeting)
    return {'detail': f'Встреча {meeting_id} удалена'}
