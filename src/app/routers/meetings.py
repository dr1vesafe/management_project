from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.schemas.meeting import MeetingRead, MeetingCreate
from src.app.database import get_db
from src.app.services import meeting_crud
from src.app.auth.dependencies import get_current_user, require_role
from src.app.models.user import User

router = APIRouter(prefix='/meetings', tags=['meetings'])


@router.post('/', response_model=MeetingRead)
async def create_meeting(
    meeting_data: MeetingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin'))
):
    """
    Создание встречи
    (доступно только менеджерам и админам)
    """
    if user.team_id != meeting_data.team_id and user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав'
        )
    
    return await meeting_crud.create_meeting(db, meeting_data)
