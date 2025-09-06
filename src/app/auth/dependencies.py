from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.utils import get_authorization_scheme_param

from src.app.auth.auth import access_backend
from src.app.auth.user_manager import get_user_manager, UserManager
from src.app.models.user import User


class OptionalHTTPBearer(HTTPBearer):
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        authorization: str = request.headers.get('Authorization')
        scheme, credentials = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != 'bearer':
            return None
        return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)


security = OptionalHTTPBearer()


async def get_current_user(
    request: Request,
    user_manager: UserManager = Depends(get_user_manager)
) -> Optional[User]:
    auth_header = request.headers.get('Authorization')
    token = None
    if auth_header and auth_header.lower().startswith('bearer '):
        token = auth_header[7:].strip()
    elif request.cookies.get('access_token'):
        token = request.cookies.get('access_token').removeprefix('Bearer ').strip()

    if not token:
        return None

    try:
        user = await access_backend.get_strategy().read_token(token, user_manager)
        return user
    except Exception:
        return None 
    

def require_role(*roles: str):
    '''Проверка роли пользователя'''
    async def dependency(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Недостаточно прав'
            )
        return user
    return dependency
