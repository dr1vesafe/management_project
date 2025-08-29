from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.app.auth.auth import access_backend
from src.app.auth.user_manager import get_user_manager, UserManager
from src.app.models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_manager: UserManager = Depends(get_user_manager),
    strategy = Depends(access_backend.get_strategy),
) -> User:
    try:
        token = credentials.credentials
        user = await strategy.read_token(token, user_manager)
        if not user:
            raise HTTPException(
                status_code=401,
                detail='Неверный access токен'
            )
        
        return user
        
    except Exception as e:
        print(f'Ошибка аутентификации: {e}')
        raise HTTPException(
                status_code=401,
                detail='Неверный access токен'
        )
    

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
