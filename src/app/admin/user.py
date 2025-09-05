from sqladmin import ModelView

from src.app.models.user import User


class UserAdmin(ModelView, model=User):
    name = 'User'
    name_plural = 'Users'
    icon = 'fa-solid fa-user'

    column_list = [
        User.id,
        User.first_name,
        User.last_name,
        User.email,
        User.is_active,
        User.role,
        User.team_id
    ]
    column_searchable_list = [User.email, User.team_id]
    column_sortable_list = [User.id, User.team_id, User.role, User.is_active]

    form_columns = [
        User.first_name,
        User.last_name,
        User.email,
        User.is_active,
        User.role,
        User.team_id
    ]
