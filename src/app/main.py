from fastapi import FastAPI
from sqladmin import Admin

from .config import settings
from .database import engine
from src.app.routers import users, auth, tasks, teams, evaluations, meetings, index
from src.app.admin import user, team, task, meeting, evaluation, meeting_participants


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        debug=settings.DEBUG,
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

admin = Admin(app, engine)

admin.add_view(user.UserAdmin)
admin.add_view(team.TeamAdmin)
admin.add_view(task.TaskAdmin)
admin.add_view(meeting.MeetingAdmin)
admin.add_view(evaluation.EvaluationAdmin)
admin.add_view(meeting_participants.MeetingParticipantAdmin)
