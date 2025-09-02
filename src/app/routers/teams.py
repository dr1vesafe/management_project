from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.schemas.team import TeamRead, TeamCreate
from src.app.database import get_db
from src.app.models.user import User
from src.app.auth.dependencies import get_current_user, require_role
from src.app.services import team_crud


router = APIRouter(prefix='/teams', tags=['teams'])


@router.post('/', response_model=TeamRead)
async def create_team(
    team_data: TeamCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin')),
):
    """
    Создание команды
    (доступно только менеджерам и админам)
    """
    if user.team_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Пользователь уже состоит в команде'
        )
    
    team = await team_crud.create_team(db, team_data)
    
    user = await db.merge(user)

    user.team_id = team.id

    await db.commit()
    await db.refresh(user)
    await db.refresh(team)
    
    return team



@router.get('/', response_model=list[TeamRead])
async def get_all_teams(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role('admin'))
):
    """
    Получение списка всех команд
    (доступно только админам)
    """
    return await team_crud.get_all_team(db)
