from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.schemas.meeting import MeetingRead, MeetingCreate
from src.app.database import get_db
from src.app.services import meeting_crud
from src.app.auth.dependencies import get_current_user, require_role
from src.app.models.user import User

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


@router.get('/', response_model=list[MeetingRead])
async def get_all_meetings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role('admin'))
):
    """
    Получить список всех встреч
    (доступно только админам)
    """
    return await meeting_crud.get_all_meetings(db)


@router.get('/{meeting_id}', response_model=MeetingRead)
async def get_meeting_by_id(
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Получить встречу по id"""
    meeting = await check_meeting(db, meeting_id, user)

    return meeting
