import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.app.database import get_db
from src.app.models.user import User, UserRole
from src.app.schemas.user import UserRead, UserUpdate, ChangePassword
from src.app.auth.dependencies import get_current_user, require_role
from src.app.auth.user_manager import get_user_manager, UserManager
from src.app.services import evaluation_service

router = APIRouter(prefix='/users', tags=['users'])
templates = Jinja2Templates(directory='src/app/templates')


# Маршруты для пользователей
@router.get('/profile')
async def profile_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    message: Optional[str] = None
):
    """Страница профиля пользователя"""
    if not user:
        return templates.TemplateResponse('login.html', {'request': request, 'error': 'Войдите в аккаунт'})
    
    avg_grade = round(await evaluation_service.get_average_by_user(db, user.id), 1)
    return templates.TemplateResponse('profile/profile.html', {
        'request': request,
        'user': user,
        'message': message,
        'avg_grade': avg_grade or 0.0
        })


@router.get('/profile/edit')
async def edit_profile_page(request: Request, user: User = Depends(get_current_user)):
    """Страница редактирования профиля"""
    return templates.TemplateResponse('profile/edit_profile.html', {'request': request, 'user': user})


@router.post('/profile/edit')
async def update_current_user(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Редактирование профиля"""
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    if not user:
        return templates.TemplateResponse('profile/edit_profile.html', {
            'request': request,
            'user': user,
            'error': 'Пользователь не найден'
        })
    
    user.first_name = first_name
    user.last_name = last_name
    user.email = email

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return RedirectResponse(
        url='/users/profile?message=Профиль успешно обновлен',
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post('/delete')
async def delete_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удалить текущего пользователя"""
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден'
        )
    
    await db.delete(user)
    await db.commit()
    response = RedirectResponse(
        url="/?message=Вы%20успешно%20удалили%20аккаунт",
        status_code=status.HTTP_303_SEE_OTHER
    )

    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')

    return response


@router.get('/profile/change-password')
async def change_password_page(request: Request, user: User = Depends(get_current_user)):
    """Страница изменения пароля"""
    return templates.TemplateResponse('profile/change_password.html', {'request': request, 'error': None, 'message': None})


@router.post('/profile/change-password')
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    user_manager: UserManager = Depends(get_user_manager)
):
    """Изменить пароль текущего пользователя"""
    error = None

    credentials = OAuth2PasswordRequestForm(
        username=user.email,
        password=current_password
    )

    authenticated_user = await user_manager.authenticate(credentials)

    if not authenticated_user:
        return templates.TemplateResponse(
            'profile/change_password.html',
            {'request': request, 'error': 'Старый пароль введен неверно', 'message': None}
        )

    if new_password != confirm_password:
        return templates.TemplateResponse(
            'profile/change_password.html',
            {'request': request, 'error': 'Пароли не совпадают', 'message': None}
        )

    if len(new_password) < 8:
        error = 'Пароль должен быть не менее 8 символов'
    if not re.search(r'[A-Za-z]', new_password):
        error = 'Пароль должен содержать хотя бы одну букву'
    if not re.search(r'\d', new_password):
        error = 'Пароль должен содержать хотя бы одну цифру'

    if error:
        return templates.TemplateResponse(
            'profile/change_password.html',
            {'request': request, 'error': error, 'message': None}
        )
    
    user = await db.merge(user)
    user.hashed_password = user_manager.password_helper.hash(new_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return RedirectResponse(
        url='/users/profile?message=Пароль успешно изменен',
        status_code=status.HTTP_303_SEE_OTHER
    )


# Маршруты для администраторов
@router.get('/admin/all', response_model=list[UserRead])
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


@router.get('/admin/{user_id}', response_model=UserRead)
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


@router.patch('/admin/{user_id}', response_model=UserRead)
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


@router.delete('/admin/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
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


@router.patch('/admin/{user_id}/role')
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
