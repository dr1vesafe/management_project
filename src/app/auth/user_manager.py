import os
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi_users import BaseUserManager, schemas, models
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi import Depends, Request, HTTPException, status

from src.app.database import async_session
from src.app.models.user import User

load_dotenv()

SECRET = os.getenv('SECRET')


class UserManager(BaseUserManager[User, int]):
    """Класс менеджера пользователей"""
    user_db_model = User
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET
    
    
    async def create(
        self, 
        user_create: schemas.UC, 
        safe: bool = False, 
        request: Request | None = None
    ) -> models.UP:
        """Переопределение метода create, необходимое из-за несовместимости версий"""
        await self.validate_password(user_create.password, user_create)

        existing_user = await self.user_db.get_by_email(user_create.email)
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Пользователь с таким email уже существует'
            )
    
        user_dict = {
            "email": user_create.email,
            "hashed_password": self.password_helper.hash(user_create.password),
            "is_active": True,
            "is_superuser": False,
        }
        
        if hasattr(user_create, 'first_name'):
            user_dict["first_name"] = user_create.first_name
        if hasattr(user_create, 'last_name'):
            user_dict["last_name"] = user_create.last_name
        if hasattr(user_create, 'role'):
            user_dict["role"] = user_create.role
        
        if not safe and hasattr(user_create, 'is_superuser'):
            user_dict["is_superuser"] = user_create.is_superuser
        if not safe and hasattr(user_create, 'is_active'):
            user_dict["is_active"] = user_create.is_active

        created_user = await self.user_db.create(user_dict)
        await self.on_after_register(created_user, request)
        return created_user
    
    async def update(
        self,
        user_update: schemas.UU,
        user: models.UP,
        safe: bool = False,
        request: Request | None = None,
    ) -> models.UP:
        """Переопределение метода update, необходимое из-за несовместимости версий"""
        update_dict: Dict[str, Any] = {}
        
        if hasattr(user_update, 'email') and user_update.email is not None:
            update_dict["email"] = user_update.email
        
        if hasattr(user_update, 'password') and user_update.password is not None:
            update_dict["hashed_password"] = self.password_helper.hash(user_update.password)
        
        if hasattr(user_update, 'first_name') and user_update.first_name is not None:
            update_dict["first_name"] = user_update.first_name
        
        if hasattr(user_update, 'last_name') and user_update.last_name is not None:
            update_dict["last_name"] = user_update.last_name
        
        if hasattr(user_update, 'role') and user_update.role is not None:
            update_dict["role"] = user_update.role
        
        if hasattr(user_update, 'team_id') and user_update.team_id is not None:
            update_dict["team_id"] = user_update.team_id
        
        if not safe:
            if hasattr(user_update, 'is_superuser') and user_update.is_superuser is not None:
                update_dict["is_superuser"] = user_update.is_superuser
            
            if hasattr(user_update, 'is_active') and user_update.is_active is not None:
                update_dict["is_active"] = user_update.is_active
        
        if update_dict:
            updated_user = await self.user_db.update(user, update_dict)
            await self.on_after_update(updated_user, update_dict, request)
            return updated_user
        
        return user
    
    def parse_id(self, id: str) -> int:
        return int(id)
    
    async def on_after_login(self, user: User, request: Request | None = None, response = None):
        print(f'Пользователь {user.id} вошел в аккаунт')

    async def on_after_logout(self, user: User, request: Request | None = None):
        print(f'Пользователь {user.id} вышел из аккаунта.')
    
    async def on_after_register(self, user: User, request: Request | None = None):
        print(f'Пользователь {user.id} зарегистрирован.')


async def get_user_db():
    async with async_session() as session:
        yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db=Depends(get_user_db)):
    """Зависимость для использования менеджера через Depends"""
    yield UserManager(user_db)
