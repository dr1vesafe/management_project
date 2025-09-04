from typing import Optional

from pydantic import BaseModel


class TeamBase(BaseModel):
    """Базовая схема команды"""
    name: str


class TeamCreate(TeamBase):
    """Схема для создания команды"""
    pass


class TeamRead(TeamBase):
    """Схема для получения данных команды"""
    id: int
    code: str

    class Config:
        from_attributes = True


class TeamUpdate(BaseModel):
    """Схема для обновления данных команды"""
    name: Optional[str] = None


class JoinTeamRequest(BaseModel):
    """Схема для вступления в команду по коду"""
    team_code: str