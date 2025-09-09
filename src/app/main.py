from fastapi import FastAPI, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

from .config import settings
from .database import engine, async_session
from src.app.admin.admin_config import setup_admin
from src.app.routers import users, auth, tasks, teams, evaluations, meetings, index
from src.app.models import User
from src.app.auth.dependencies import require_role, get_current_user


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        debug=settings.DEBUG,
        docs_url=None,
        redoc_url=None,
    )

    app.include_router(users.router)
    app.include_router(auth.router)
    app.include_router(tasks.router)
    app.include_router(teams.router)
    app.include_router(evaluations.router)
    app.include_router(meetings.router)
    app.include_router(index.router)


    return app


app = create_application()


setup_admin(app, engine)


@app.get('/docs', include_in_schema=False)
async def custom_swagger_ui(user: User = Depends(require_role('admin'))):
    return get_swagger_ui_html(openapi_url='/openapi.json', title='Docs')


@app.get('/redoc', include_in_schema=False)
async def custom_redoc_ui(user: User = Depends(require_role('admin'))):
    return get_redoc_html(openapi_url='/openapi.json', title='ReDoc')
