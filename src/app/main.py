from fastapi import FastAPI, Depends
from sqladmin import Admin

from .config import settings
from .database import engine
from src.app.auth.auth import fastapi_users
from src.app.schemas.user import UserRead, UserCreate
from src.app.routers import users, auth, tasks, teams, evaluations, meetings
from src.app.admin import user, team


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
    app.include_router(tasks.router)
    app.include_router(teams.router)
    app.include_router(evaluations.router)
    app.include_router(meetings.router)

    return app


app = create_application()

admin = Admin(app, engine)

admin.add_view(user.UserAdmin)
admin.add_view(team.TeamAdmin)
