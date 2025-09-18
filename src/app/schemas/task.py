from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic_core import PydanticCustomError

from src.app.models.task import TaskStatus


class TaskBase(BaseModel):
    """Базовая схема задачи"""
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.open
    deadline_date: Optional[datetime] = None
    performer_id: Optional[int] = None
    manager_id: Optional[int] = None
    team_id: int


class TaskCreate(TaskBase):
    """Схема для создания задачи"""
    pass

    @field_validator('deadline_date')
    def validate_deadline_date(cls, value: datetime) -> datetime:
        if value is not None and value < datetime.now():
            raise PydanticCustomError(
                'incorrect_date',
                'Дата дедлайна не может быть в прошлом'
            )
        return value


class TaskRead(TaskBase):
    """Схема для получения данных задачи"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskUpdate(BaseModel):
    """Схема для обновления данных задачи"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    deadline_date: Optional[datetime] = None
    performer_id: Optional[int] = None
    team_id: Optional[int] = None

    @field_validator('deadline_date')
    def validate_deadline_date(cls, value: datetime) -> datetime:
        if value is not None and value < datetime.now():
            raise PydanticCustomError(
                'incorrect_date',
                'Дата дедлайна не может быть в прошлом'
            )
        return value
