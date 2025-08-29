from fastapi import FastAPI, Depends

from .config import settings
from src.app.auth.auth import fastapi_users, auth_backend
from src.app.schemas.user import UserRead, UserCreate


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        debug=settings.DEBUG,
    )

    app.include_router(
        fastapi_users.get_register_router(UserRead, UserCreate),
        prefix='/auth',
        tags=['auth']
    )

    app.include_router(
        fastapi_users.get_auth_router(auth_backend),
        prefix='/auth/jwt',
        tags=['auth']
    )

    app.include_router(
        fastapi_users.get_users_router(UserRead, UserCreate),
        prefix='/users',
        tags=['users']
    )

    return app


app = create_application()