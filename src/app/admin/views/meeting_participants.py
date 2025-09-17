from sqladmin import ModelView

from src.app.models.meeting_participants import MeetingParticipant


class MeetingParticipantAdmin(ModelView, model=MeetingParticipant):
    name = 'Meeting Participant'
    name_plural = 'Meeting Participants'
    icon = 'fa-solid fa-handshake'

    column_list = [
        MeetingParticipant.meeting_id,
        MeetingParticipant.user_id
    ]
    column_searchable_list = [MeetingParticipant.meeting_id]
    column_sortable_list = [
        MeetingParticipant.meeting_id,
        MeetingParticipant.user_id
    ]

    form_columns = [
        MeetingParticipant.meeting,
        MeetingParticipant.user
    ]
