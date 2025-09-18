from typing import Optional
from datetime import datetime, UTC

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
    Request,
    Form
)
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import ValidationError

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
    status: Optional[str] = Query(None, pattern='^(past|upcoming)?$'),
    my_meetings: bool = Query(False),
    page: int = Query(1, ge=1)
):
    """Страница со встречами команды"""
    limit = 10
    offset = (page - 1) * limit

    query = (
        select(Meeting)
        .options(
            selectinload(Meeting.participants)
            .selectinload(MeetingParticipant.user)
        )
    )
    count_query = select(func.count(Meeting.id))

    query = query.where(Meeting.team_id == user.team_id)
    count_query = count_query.where(Meeting.team_id == user.team_id)

    now = datetime.now(UTC)

    if status == 'past':
        query = query.where(Meeting.scheduled_at < now)
        count_query = count_query.where(Meeting.scheduled_at < now)
    elif status == 'upcoming':
        query = query.where(Meeting.scheduled_at >= now)
        count_query = count_query.where(Meeting.scheduled_at >= now)

    if my_meetings:
        query = (
            query.join(MeetingParticipant)
            .where(MeetingParticipant.user_id == user.id)
        )
        count_query = (
            count_query.join(MeetingParticipant)
            .where(MeetingParticipant.user_id == user.id)
        )

    total_meetings = await db.scalar(count_query)
    total_pages = max((total_meetings + limit - 1) // limit, 1)

    meetings_result = await db.execute(query.offset(offset).limit(limit))
    meetings = meetings_result.scalars().all()

    return templates.TemplateResponse(
        request,
        'meeting/meetings.html',
        {
            'meetings': meetings,
            'status': status or '',
            'my_meetings': my_meetings,
            'page': page,
            'total_pages': total_pages,
            'user': user
        }
    )


@router.get('/create')
async def create_meeting_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin'))
):
    """Страница создания встречи"""
    result = await db.execute(select(User).where(User.team_id == user.team_id))
    team_members = result.scalars().all()

    return templates.TemplateResponse(
        request,
        'meeting/create_meeting.html',
        {
            'error': None,
            'user': user,
            'team_members': team_members
        }
    )


@router.post('/create')
async def create_meeting_submit(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    scheduled_at: str = Form(...),
    team_id: int = Form(...),
    participant_ids: list[int] = Form(default=[]),
    add_all_team: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin'))
):
    """Создать встречу"""
    try:
        scheduled_dt = datetime.fromisoformat(scheduled_at)
    except ValueError:
        result = await db.execute(
            select(User).where(User.team_id == user.team_id)
        )
        team_members = result.scalars().all()
        return templates.TemplateResponse(
            'meeting/create_meeting.html',
            {
                'request': request,
                'error': 'Неверный формат даты/времени',
                'user': user,
                'team_members': team_members
            }
        )

    conflict_query = await db.execute(
        select(Meeting)
        .where(Meeting.team_id == team_id)
        .where(Meeting.scheduled_at == scheduled_dt)
    )
    conflict_meeting = conflict_query.scalars().first()

    if conflict_meeting:
        result = await db.execute(
            select(User).where(User.team_id == user.team_id)
        )
        team_members = result.scalars().all()
        return templates.TemplateResponse(
            request,
            'meeting/create_meeting.html',
            {
                'error': 'На это время уже назначена встреча',
                'user': user,
                'team_members': team_members
            }
        )

    try:
        meeting_data = MeetingCreate(
            title=title,
            description=description,
            scheduled_at=scheduled_dt,
            team_id=team_id,
            participants_id=participant_ids,
            add_team_members=add_all_team
        )
    except ValidationError as e:
        result = await db.execute(
            select(User).where(User.team_id == user.team_id)
        )
        team_members = result.scalars().all()
        error_msg = '; '.join(err['msg'] for err in e.errors())
        return templates.TemplateResponse(
            request,
            'meeting/create_meeting.html',
            {
                'error': error_msg,
                'user': user,
                'team_members': team_members
            }
        )

    if (
        meeting_data.team_id and
        user.team_id != meeting_data.team_id and
        user.role != 'admin'
    ):
        result = await db.execute(
            select(User).where(User.team_id == user.team_id)
        )
        team_members = result.scalars().all()
        return templates.TemplateResponse(
            request,
            'meeting/create_meeting.html',
            {
                'error': 'Недостаточно прав для создания встречи',
                'user': user,
                'team_members': team_members
            }
        )

    meeting = await meeting_crud.create_meeting(db, meeting_data, user)

    return RedirectResponse(
        url=f'/meetings/{meeting.id}',
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get('/{meeting_id}')
async def meeting_detail_page(
    meeting_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Детальная страница встречи"""
    result = await db.execute(
        select(Meeting)
        .where(Meeting.id == meeting_id)
        .options(selectinload(Meeting.organizer),
                 selectinload(Meeting.team))
    )
    meeting = result.scalars().first()
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Встреча не найдена'
        )

    if user.team_id != meeting.team_id and user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Встреча не найдена'
        )

    participants_query = await db.execute(
        select(MeetingParticipant)
        .where(MeetingParticipant.meeting_id == meeting_id)
        .options(selectinload(MeetingParticipant.user))
    )
    participants = participants_query.scalars().all()

    return templates.TemplateResponse(
        request,
        'meeting/meeting_detail.html',
        {
            'meeting': meeting,
            'participants': participants,
            'user': user
        }
    )


@router.get('/{meeting_id}/edit')
async def edit_meeting_page(
    meeting_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin'))
):
    """Страница для изменения встречи"""
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    meeting = result.scalars().first()
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Встреча не найдена'
        )

    if user.team_id != meeting.team_id and user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Встреча не найдена'
        )

    return templates.TemplateResponse(
        request,
        'meeting/edit_meeting.html',
        {'meeting': meeting, 'user': user}
    )


@router.post('/{meeting_id}/edit')
async def edit_meeting_submit(
    meeting_id: int,
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    scheduled_at: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin'))
):
    """Изменение встречи"""
    meeting = await check_meeting(db, meeting_id, user)

    try:
        scheduled_dt = datetime.fromisoformat(scheduled_at)
    except ValueError:
        return templates.TemplateResponse(
            request,
            'meeting/edit_meeting.html',
            {
                'error': 'Неверный формат даты/времени',
                'user': user,
                'meeting': meeting
            }
        )

    conflict_query = await db.execute(
        select(Meeting)
        .where(Meeting.team_id == user.team_id)
        .where(Meeting.scheduled_at == scheduled_dt)
    )
    conflict_meeting = conflict_query.scalars().first()

    if conflict_meeting:
        return templates.TemplateResponse(
            request,
            'meeting/edit_meeting.html',
            {
                'error': 'На это время уже назначена встреча',
                'user': user,
                'meeting': meeting
            }
        )

    try:
        meeting_data = MeetingUpdate(
            title=title,
            description=description,
            scheduled_at=scheduled_dt
        )
    except ValidationError as e:
        error_msg = '; '.join(err['msg'] for err in e.errors())
        return templates.TemplateResponse(
            request,
            'meeting/edit_meeting.html',
            {
                'error': error_msg,
                'user': user,
                'meeting': meeting
            }
        )

    await meeting_crud.update_meeting(db, meeting, meeting_data)
    return RedirectResponse(
        url=f'/meetings/{meeting_id}',
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post('/{meeting_id}/delete')
async def delete_meeting_submit(
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin'))
):
    """Удаление встречи"""
    meeting = await check_meeting(db, meeting_id, user)

    await meeting_crud.delete_meeting(db, meeting)

    return RedirectResponse(
        url='/meetings',
        status_code=status.HTTP_303_SEE_OTHER
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
    return await meeting_crud.create_meeting(db, meeting_data, user)


@router.get('/admin/all', response_model=list[MeetingRead])
async def get_all_meetings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role('admin')),
    team_id: Optional[int] = Query(None, description='Фильтрация по команде'),
    organizer_id: Optional[int] = Query(
        None,
        description='Фильтрация по организатору'
    ),
    scheduled_before: Optional[datetime] = Query(
        None,
        description='Встречи до даты'
    ),
    scheduled_after: Optional[datetime] = Query(
        None,
        description='Встречи после даты'
    ),
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
    _: User = Depends(require_role('admin')),
    organizer_id: Optional[int] = Query(
        None,
        description='Фильтрация по организатору'
    ),
    scheduled_before: Optional[datetime] = Query(
        None,
        description='Встречи до даты'
    ),
    scheduled_after: Optional[datetime] = Query(
        None,
        description='Встречи после даты'
    ),
    limit: int = Query(10, ge=1, le=100, description='Количество записей'),
    offset: int = Query(0, ge=0, description='Смещение'),
):
    """Получить встречи для команды"""
    stmt = (
        select(Meeting)
        .options(selectinload(Meeting.participants))
        .where(Meeting.team_id == team_id)
    )

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
