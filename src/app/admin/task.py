from sqladmin import ModelView

from src.app.models.task import Task


class TaskAdmin(ModelView, model=Task):
    name = 'Task'
    name_plural = 'Tasks'
    icon = 'fa-solid fa-briefcase'

    column_list = [
        Task.id,
        Task.title,
        Task.status,
        Task.created_at,
        Task.updated_at,
        Task.deadline_date,
        Task.team_id,
        Task.performer_id
    ]
    column_searchable_list = [Task.title, Task.team_id]
    column_sortable_list = [Task.id, Task.created_at, Task.deadline_date, Task.team_id, Task.performer_id]

    form_columns = [
        Task.title,
        Task.description,
        Task.status,
        Task.deadline_date,
        Task.team_id,
        Task.performer_id,
    ]
