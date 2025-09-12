from typing import Optional
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.app.auth.dependencies import get_current_user
from src.app.models.user import User
from src.app.models.team import Team
from src.app.models.task import Task
from src.app.models.meeting import Meeting
from src.app.models.meeting_participants import MeetingParticipant
from src.app.database import get_db

router = APIRouter(tags=['index'])
templates = Jinja2Templates(directory='src/app/templates')


@router.get('/')
async def index(
    request: Request,
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    message: Optional[str] = None
):
    """Главная страница"""
    team = None
    tasks = []
    meetings = []

    if user:
        team_result = await db.execute(
            select(Team).where(Team.id == user.team_id)
        )
        team = team_result.scalars().first()

        tasks_result = await db.execute(
            select(Task)
            .where(
                Task.performer_id == user.id,
                Task.status.in_(['open', 'in_progress'])
            )
        )
        tasks = tasks_result.scalars().all()

        current_date = datetime.now(UTC)
        meetings_result = await db.execute(
            select(Meeting)
            .join(MeetingParticipant)
            .where(
                MeetingParticipant.user_id == user.id,
                Meeting.scheduled_at >= current_date
            )
        )
        meetings = meetings_result.scalars().all()

    if user is None and request.cookies.get("refresh_token"):
        return RedirectResponse(url="/auth/refresh?next=/")

    return templates.TemplateResponse(
        request,
        'main_page/index.html',
        {
            'user': user,
            'team': team,
            'tasks': tasks,
            'meetings': meetings,
            'message': message
        }
    )
