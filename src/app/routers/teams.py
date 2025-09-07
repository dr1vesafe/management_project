from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.app.schemas.team import TeamRead, TeamCreate, TeamUpdate, JoinTeamRequest
from src.app.database import get_db
from src.app.models.user import User
from src.app.models.team import Team
from src.app.auth.dependencies import get_current_user, require_role
from src.app.services import team_crud


router = APIRouter(prefix='/teams', tags=['teams'])
templates = Jinja2Templates(directory='src/app/templates')


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
    _: User = Depends(require_role('admin')),
    name: Optional[str] = Query(None, description='Фильтрация по названию команды'),
    code: Optional[str] = Query(None, description='Филтрация по коду команды'),
    limit: int = Query(10, ge=1, le=100, description='Количество записей'),
    offset: int = Query(0, ge=0, description='Смещение')
):
    """
    Получение списка всех команд
    (доступно только админам)
    """
    stmt = select(Team)

    if name:
        stmt = stmt.where(Team.name.ilike(f'%{name}'))
    if code:
        stmt = stmt.where(Team.code.ilike(f'%{code}'))

    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.post('/membership')
async def join_team_by_code(
    body: JoinTeamRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Вступить в команду по коду"""
    if current_user.team_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Вы уже состоите в команде'
        )
    
    result = await db.execute(select(Team).where(Team.code == body.team_code))
    team = result.scalars().first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Команда с таким кодом не найдена'
        )
    
    user = await db.merge(current_user)
    user.team_id = team.id
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {'detail': f'Вы успешно присоединились к команде {team.name}'}


@router.delete('/membership', status_code=status.HTTP_200_OK)
async def leave_team(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Выйти из команды"""
    if not current_user.team_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Вы не состоите в команде'
        )
    
    user = await db.merge(current_user)
    user.team_id = None
    db.add(user)
    await db.commit()
    return {'detail': 'Вы успешно покинули команду'}


@router.get('/join-team')
async def join_team_page(request: Request):
    """Страница вступления в команду"""
    return templates.TemplateResponse('join_team.html', {
        'request': request,
        'error': None,
        'success': None
        })


@router.post('/join-team')
async def join_team(
    request: Request,
    team_code: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Вступление в команду по коду"""
    error = None
    success = None

    if not current_user:
        error = 'Необходимо войти в аккаунт'
        return templates.TemplateResponse('join_team.html', {
            'request': request,
            'error': error
        })
        
    if current_user.team_id:
        error = 'Вы уже состоите в команде'
        return templates.TemplateResponse('join_team.html', {
            'request': request,
            'error': error
        })
    
    result = await db.execute(select(Team).where(Team.code == team_code))
    team = result.scalars().first()

    if not team:
        error = 'Команда с таким кодом не найдена'
        return templates.TemplateResponse('join_team.html', {
            'request': request,
            'error': error
        })
    
    user = await db.merge(current_user)
    user.team_id = team.id
    db.add(user)
    await db.commit()
    await db.refresh(user)

    success = f'Вы успешно присоединились к команде {team.name}'
    return templates.TemplateResponse('join_team.html', {
            'request': request,
            'success': success
        })


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


@router.delete('/{team_id}/users/{user_id}', status_code=status.HTTP_200_OK)
async def remove_user_from_team(
    team_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role('manager', 'admin'))
):
    """
    Удаление пользователя из команды
    (доступно только менеджерам и админам)
    """

    if current_user.team_id != team_id and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав'
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден'
        )
    
    if user.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Пользователь не состоит в этой команде'
        )
    
    user.team_id = None
    db.add(user)
    await db.commit()
    return {'detail': f'Пользователь {user_id} удален из команды {team_id}'}
