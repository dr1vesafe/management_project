from sqladmin import ModelView

from src.app.models.team import Team


class TeamAdmin(ModelView, model=Team):
    name = 'Team'
    name_plural = 'Teams'
    icon = 'fa-solid fa-users'

    column_list = [
        Team.id,
        Team.name,
        Team.code
    ]
    column_searchable_list = [Team.name]
    column_sortable_list = [Team.id, Team.name]

    form_columns = [
        Team.name,
        Team.code
    ]
