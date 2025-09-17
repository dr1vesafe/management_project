from sqladmin import ModelView
from wtforms import PasswordField
from passlib.hash import bcrypt

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
        User.team
    ]

    async def scaffold_form(self):
        form_class = await super().scaffold_form()
        form_class.password = PasswordField('Password')
        return form_class

    async def on_model_change(self, data, model, is_created, request):
        password = data.pop('password', None)
        if password:
            model.hashed_password = bcrypt.hash(password)
        return await super().on_model_change(data, model, is_created, request)
