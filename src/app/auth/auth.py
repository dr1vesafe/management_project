from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy

from src.app.auth.user_manager import get_user_manager, SECRET
from src.app.models.user import User

access_transport = BearerTransport(tokenUrl='auth/jwt/login')

refresh_transport = BearerTransport(tokenUrl='auth/jwt/refresh')


def get_access_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


def get_refresh_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET + '_REFRESH', lifetime_seconds=2592000)


access_backend = AuthenticationBackend(
    name='access',
    transport=access_transport,
    get_strategy=get_access_jwt_strategy,
)

refresh_backend = AuthenticationBackend(
    name='refresh',
    transport=refresh_transport,
    get_strategy=get_refresh_jwt_strategy,
)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [access_backend, refresh_backend],
)
