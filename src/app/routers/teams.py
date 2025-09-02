from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.schemas.team import TeamRead, TeamCreate, TeamUpdate
from src.app.database import get_db
from src.app.models.user import User
from src.app.auth.dependencies import get_current_user, require_role
from src.app.services import team_crud


router = APIRouter(prefix='/teams', tags=['teams'])


async def check_team(
        db: AsyncSession,
        team_id: int,
        user: User
):
    """Общая функция для проверки команды"""
    team = await team_crud.get_team(db, team_id)
    if user.team_id != team_id and user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав'
        )
    
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Команда не найдена'
        )
    
    return team
    

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


@router.get('/{team_id}', response_model=TeamRead)
async def get_team(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Получение команды по id"""
    team = await check_team(db, team_id, user)
    return team


@router.put('/{team_id}', response_model=TeamRead)
async def update_team(
    team_id: int,
    team_data: TeamUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin'))
):
    """
    Изменение команды
    (доступно только менеджерам и админам)
    """
    team = await check_team(db, team_id, user)

    return await team_crud.update_team(db, team, team_data)


@router.delete('/{team_id}')
async def delete_team(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin'))
):
    """
    Удаление команды
    (доступно только менеджерам и админам)
    """
    team = await check_team(db, team_id, user)

    await team_crud.delete_team(db, team)
    return {'detail': f'Команда {team_id} удалена'}
