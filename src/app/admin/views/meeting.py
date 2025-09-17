from sqladmin import ModelView

from src.app.models.meeting import Meeting


class MeetingAdmin(ModelView, model=Meeting):
    name = 'Meeting'
    name_plural = 'Meetings'
    icon = 'fa-solid fa-calendar'

    column_list = [
        Meeting.id,
        Meeting.title,
        Meeting.scheduled_at,
        Meeting.team_id,
        Meeting.organizer_id
    ]
    column_searchable_list = [Meeting.title, Meeting.team_id]
    column_sortable_list = [
        Meeting.id,
        Meeting.scheduled_at,
        Meeting.team_id,
        Meeting.organizer_id
    ]

    form_columns = [
        Meeting.title,
        Meeting.description,
        Meeting.scheduled_at,
        Meeting.organizer,
        Meeting.team
    ]
