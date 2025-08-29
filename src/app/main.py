from fastapi import FastAPI, Depends

from .config import settings
from src.app.auth.auth import fastapi_users
from src.app.schemas.user import UserRead, UserCreate
from src.app.routers import users, auth


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

    app.include_router(users.router)
    app.include_router(auth.router)

    return app


app = create_application()