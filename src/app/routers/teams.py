from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.app.schemas.team import TeamRead, TeamCreate, TeamUpdate, JoinTeamRequest
from src.app.database import get_db
from src.app.models.user import User
from src.app.models.team import Team, generate_team_code
from src.app.auth.dependencies import get_current_user, require_role
from src.app.services import team_crud, evaluation_service


router = APIRouter(prefix='/teams', tags=['teams'])
templates = Jinja2Templates(directory='src/app/templates')

role_order = {
    'admin': 0,
    'manager': 1,
    'user': 2
}


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
    

# Маршруты для пользователей
@router.get('/create')
async def create_team_page(request: Request):
    """Страница создания команды"""
    return templates.TemplateResponse(
        request,
        'team/create_team.html', 
        {'error': None}
    )


@router.post('/create')
async def create_team_submit(
    request: Request,
    name: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Создание команды"""
    if user.team_id:
        return templates.TemplateResponse(
            request,
            'team/create_team.html',
            {'error': 'Вы уже состоите в команде'}
        )
    
    if user.role == 'user':
        user.role = 'manager'

    new_team = await team_crud.create_team(db, TeamCreate(name=name))
    user = await db.merge(user)
    user.team_id = new_team.id

    await db.commit()
    await db.refresh(user)
    await db.refresh(new_team)

    return RedirectResponse(
        url=f"/?message=Команда%20'{new_team.name}'%20успешно%20создана",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post('/leave-team', status_code=status.HTTP_200_OK)
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
    team = await check_team(db, user.team_id, user)

    user.team_id = None
    if user.role == 'manager':
        user.role = 'user'

    team.code = generate_team_code()

    db.add(user)
    db.add(team)
    await db.commit()
    return RedirectResponse(
        url="/?message=Вы%20успешно%20покинули%20команду",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get('/join-team')
async def join_team_page(request: Request):
    """Страница вступления в команду"""
    return templates.TemplateResponse(
        request,
        'team/join_team.html',
        {'error': None, 'success': None}
    )


@router.post('/join-team')
async def join_team(
    request: Request,
    team_code: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Вступление в команду по коду"""
    error = None

    if not current_user:
        error = 'Необходимо войти в аккаунт'
        return templates.TemplateResponse(
            request,
            'team/join_team.html',
            {'error': error}
        )
        
    if current_user.team_id:
        error = 'Вы уже состоите в команде'
        return templates.TemplateResponse(
            request,
            'team/join_team.html',
            {'error': error}
        )
    
    result = await db.execute(select(Team).where(Team.code == team_code))
    team = result.scalars().first()

    if not team:
        error = 'Команда с таким кодом не найдена'
        return templates.TemplateResponse(
            request,
            'team/join_team.html',
            {'error': error}
        )
    
    user = await db.merge(current_user)
    user.team_id = team.id
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return RedirectResponse(
        url="/?message=Вы%20успешно%20вступили%20в%20команду",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get('/{team_id}')
async def team_page(
    team_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Страница команды"""
    if user.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав'
        )
    
    result = await db.execute(
        select(Team)
        .where(Team.id == team_id)
        .options(selectinload(Team.members))
    )
    team = result.scalars().first()
    
    members = team.members if hasattr(team, 'members') else []
    members = sorted(
        team.members,
        key=lambda m: role_order.get(m.role.name if m.role else 'user', 99)
    )

    try:
        avg_grade = round(await evaluation_service.get_average_grade_by_team(db, team_id), 1)
    except TypeError:
        avg_grade = 0.0
    
    return templates.TemplateResponse(
        request,
        'team/team.html',
        {'team': team, 'members': members, 'user': user, 'avg_grade': avg_grade}
    )


@router.get('/{team_id}/edit')
async def edit_team_page(
    team_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin'))
):
    """Страница изменения команды"""
    team = await check_team(db, team_id, user)
    
    return templates.TemplateResponse(
        request,
        'team/edit_team.html',
        {'team': team, 'error': None, 'user': user}
    )


@router.post('/{team_id}/edit')
async def edit_team_submit(
    team_id: int,
    name: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin'))
):
    """Изменение команды"""
    team = await check_team(db, team_id, user)
    team_data = TeamUpdate(name=name)
    await team_crud.update_team(db, team, team_data)

    return RedirectResponse(
        url=f'/teams/{team_id}',
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post('/{team_id}/delete')
async def delete_team_submit(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin'))
):
    """Удаление команды"""
    team = await check_team(db, team_id, user)

    member_result = await db.execute(
        select(User).where(User.team_id == team.id)
    )
    members = member_result.scalars().all()

    for member in members:
        if member.role == 'manager':
            member.role = 'user'
        member.team_id = None
        db.add(member)
    
    await team_crud.delete_team(db, team)
    await db.commit()

    return RedirectResponse(url='/?message=Команда%20успешно%20удалена', status_code=status.HTTP_303_SEE_OTHER)


@router.post('/{team_id}/code')
async def change_team_code_submit(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin'))
):
    """Генерация нового кода команды"""
    team = await check_team(db, team_id, user)
    team.code = generate_team_code()

    db.add(team)
    await db.commit()

    return RedirectResponse(url=f'/teams/{team_id}', status_code=status.HTTP_303_SEE_OTHER)


@router.post('/{team_id}/users/{user_id}/remove')
async def remove_user_from_team_submit(
    team_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin'))
):
    """Удалить пользователя из команды"""
    if user.team_id != team_id and user.role.name != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав'
        )

    if user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Вы не можете удалить себя'
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
    
    team = await check_team(db, team_id, user)
    team.code = generate_team_code()
    
    user.team_id = None
    if user.role == 'manager':
        user.role = 'user'
        
    db.add(user)
    db.add(team)
    await db.commit()
    
    return RedirectResponse(url=f'/teams/{team_id}', status_code=status.HTTP_303_SEE_OTHER)


@router.post('/{team_id}/users/{user_id}/promote')
async def promote_user_to_manager(
    team_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin'))
):
    """Повысить user до manager"""
    if user.team_id != team_id and user.role.name != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав'
        )

    if user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Вы не можете изменить свою роль'
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detailt='Пользователь не найден'
        )
    if user.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Пользователь не состоит в этой команде'
        )
    
    user.role = 'manager'
    db.add(user)
    await db.commit()

    return RedirectResponse(url=f'/teams/{team_id}', status_code=status.HTTP_303_SEE_OTHER)


@router.post('/{team_id}/users/{user_id}/downgrade')
async def downgrade_manager_to_user(
    team_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin'))
):
    """Понизить manager до user"""
    if user.team_id != team_id and user.role.name != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Недостаточно прав'
        )

    if user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Вы не можете изменить свою роль'
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detailt='Пользователь не найден'
        )
    if user.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Пользователь не состоит в этой команде'
        )
    
    user.role = 'user'
    db.add(user)
    await db.commit()

    return RedirectResponse(url=f'/teams/{team_id}', status_code=status.HTTP_303_SEE_OTHER)


# Маршруты для администраторов
@router.get('/admin/all', response_model=list[TeamRead])
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


@router.get('/admin/{team_id}', response_model=TeamRead)
async def get_team(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('admin'))
):
    """
    Получение команды по id
    (доступно только админам)
    """
    team = await check_team(db, team_id, user)
    return team


@router.put('/admin/{team_id}', response_model=TeamRead)
async def update_team(
    team_id: int,
    team_data: TeamUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('admin'))
):
    """
    Изменение команды
    (доступно только админам)
    """
    team = await check_team(db, team_id, user)

    return await team_crud.update_team(db, team, team_data)


@router.delete('/admin/{team_id}')
async def delete_team(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('admin'))
):
    """
    Удаление команды
    (доступно только админам)
    """
    team = await check_team(db, team_id, user)

    await team_crud.delete_team(db, team)
    return {'detail': f'Команда {team_id} удалена'}


@router.delete('/{team_id}/users/{user_id}', status_code=status.HTTP_200_OK)
async def remove_user_from_team(
    team_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role('admin'))
):
    """
    Удаление пользователя из команды
    (доступно только админам)
    """
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
