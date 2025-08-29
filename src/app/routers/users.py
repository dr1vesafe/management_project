from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.app.database import get_db
from src.app.models.user import User, UserRole
from src.app.schemas.user import UserRead, UserUpdate
from src.app.auth.dependencies import get_current_user, require_role

router = APIRouter(prefix='/users', tags=['users'])


@router.get('/me', response_model=UserRead)
async def get_current_user(user: User = Depends(get_current_user)):
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
    _: User = Depends(require_role('admin'))
):
    """
    Получить всех пользователей
    (доступно только админам)
    """
    result = await db.execute(select(User))
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
