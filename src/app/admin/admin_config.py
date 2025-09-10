from fastapi import Request, HTTPException
from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, JWTError

from src.app.admin.views import user, team, task, meeting, evaluation, meeting_participants
from src.app.database import async_session
from src.app.config import settings
from src.app.models.user import User

SECRET_KEY = settings.SECRET
ALGORITHM = 'HS256'


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        return True

    async def logout(self, request: Request) -> bool:
        return True

    async def authenticate(self, request: Request) -> bool:
        raw_token = request.cookies.get("access_token")
        if not raw_token:
            raise HTTPException(status_code=403, detail="Not authorized")

        token = raw_token.replace('Bearer ', '')
        
        try:
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM],
                audience='fastapi-users:auth'
            )
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=403, detail="Invalid token")
        except JWTError:
            raise HTTPException(status_code=403, detail="Invalid token")

        async with async_session() as session:
            result = await session.execute(select(User).where(User.id == int(user_id)))
            user = result.scalar_one_or_none()
            if not user or user.role != "admin":
                raise HTTPException(status_code=403, detail="Forbidden")

        return True

    

def setup_admin(app, engine):
    admin = Admin(
        app,
        engine,
        authentication_backend=AdminAuth(secret_key=SECRET_KEY)
    )

    admin.add_view(user.UserAdmin)
    admin.add_view(team.TeamAdmin)
    admin.add_view(task.TaskAdmin)
    admin.add_view(meeting.MeetingAdmin)
    admin.add_view(evaluation.EvaluationAdmin)
    admin.add_view(meeting_participants.MeetingParticipantAdmin)
    
    return admin
