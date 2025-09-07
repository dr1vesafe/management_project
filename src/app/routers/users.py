from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.app.database import get_db
from src.app.models.user import User, UserRole
from src.app.schemas.user import UserRead, UserUpdate, ChangePassword
from src.app.auth.dependencies import get_current_user, require_role
from src.app.auth.user_manager import get_user_manager, UserManager

router = APIRouter(prefix='/users', tags=['users'])
templates = Jinja2Templates(directory='src/app/templates')


@router.get('/profile')
async def profile_page(request: Request, user: User = Depends(get_current_user)):
    """Страница профиля пользователя"""
    if not user:
        return templates.TemplateResponse('login.html', {'request': request, 'error': 'Войдите в аккаунт'})
    
    return templates.TemplateResponse('profile.html', {'request': request, 'user': user})
   

@router.get('/me', response_model=UserRead)
async def get_me(user: User = Depends(get_current_user)):
    """
    Получить данные текущего пользователя
    (доступно любому авторизованному пользователю)
    """
    return user


@router.patch('/me', response_model=UserRead)
async def update_current_user(
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Изменить данные текущего пользователя
    (доступно любому авторизованному пользователю)
    """
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден'
        )
    
    for field, value in data.dict(exclude_unset=True).items():
        setattr(user, field, value)

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete('/me', status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Удалить текущего пользователя
    (доступно любому авторизованному пользователю)
    """
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден'
        )
    
    await db.delete(user)
    await db.commit()
    return {'msg': 'Пользователь удален'}


@router.get('/', response_model=list[UserRead])
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role('admin')),
    email: Optional[str] = Query(None, description="Фильтрация по email"),
    role: Optional[UserRole] = Query(None, description='Филтрация по роли'),
    team_id: Optional[int] = Query(None, description='Фильтрация по команде'),
    is_active: Optional[bool] = Query(None, description='Фильтрация по статусу'),
    limit: int = Query(10, ge=1, le=100, description='Количество записей'),
    offset: int = Query(0, ge=0, description='Смещение')
):
    """
    Получить всех пользователей
    (доступно только админам)
    """
    stmt = select(User)

    if email:
        stmt = stmt.where(User.email.ilike(f'%{email}'))
    if role:
        stmt = stmt.where(User.role == role)
    if team_id is not None:
        stmt = stmt.where(User.team_id == team_id)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)

    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get('/{user_id}', response_model=UserRead)
async def get_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role('admin')),
):
    """
    Получить пользователя по id
    (доступно только админам)
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден'
        )
    
    return user


@router.patch('/{user_id}', response_model=UserRead)
async def update_user_by_id(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role('admin'))
):
    """
    Изменить пользователя с указанным id
    (доступно только админам)
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден'
        )
    
    for field, value in data.dict(exclude_unset=True).items():
        setattr(user, field, value)

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete('/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role('admin'))
):
    """
    Удалить пользователя с указанным id
    (доступно только админам)
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден'
        )

    await db.delete(user)
    await db.commit()
    return {'msg': f'Пользователь {user_id} удален'}


@router.patch('/{user_id}/role')
async def update_user_role(
    user_id: int,
    new_role: UserRole,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role('admin'))
):
    """
    Изменить роль пользователя с указанным id
    (доступно только админам)
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден'
        )
    
    user.role = new_role.value
    await db.commit()
    await db.refresh(user)

    return {'msg': f'Роль пользователя {user.id} изменена на {new_role.value}'}


@router.post('/change-password')
async def change_password(
    data: ChangePassword,
    user: User = Depends(get_current_user),
    user_manager: UserManager = Depends(get_user_manager)
):
    """
    Изменить пароль текущего пользователя
    (доступно любому авторизованному пользователю)
    """
    credentials = OAuth2PasswordRequestForm(
        username=user.email,
        password=data.old_password
    )

    authenticated_user = await user_manager.authenticate(credentials)

    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Неверно введен старый пароль'
        )
    
    hashed_new_password = user_manager.password_helper.hash(data.new_password)

    update_dict = {
        'hashed_password': hashed_new_password
    }

    await user_manager.user_db.update(user, update_dict)
    return {'detail': 'Пароль успешно изменен'}
