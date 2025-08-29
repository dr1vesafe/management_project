from fastapi import Depends, HTTPException, status

from src.app.auth.auth import fastapi_users
from src.app.models.user import User

get_current_user = fastapi_users.current_user()


def require_role(role: str):
    """Проверка роли пользователя"""
    async def dependency(user: User = Depends(get_current_user)):
        if user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Недостаточно прав'
            )
        return user
    return dependency
