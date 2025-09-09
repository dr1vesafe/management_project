from sqladmin import Admin

from src.app.admin.views import user, team, task, meeting, evaluation, meeting_participants


def setup_admin(app, engine):
    admin = Admin(app, engine)

    admin.add_view(user.UserAdmin)
    admin.add_view(team.TeamAdmin)
    admin.add_view(task.TaskAdmin)
    admin.add_view(meeting.MeetingAdmin)
    admin.add_view(evaluation.EvaluationAdmin)
    admin.add_view(meeting_participants.MeetingParticipantAdmin)
    
    return admin
