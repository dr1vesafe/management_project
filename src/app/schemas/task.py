from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.app.models.task import TaskStatus


class TaskBase(BaseModel):
    """Базовая схема задачи"""
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.open
    deadline_date: Optional[datetime] = None
    performer_id: Optional[int] = None
    team_id: int


class TaskCreate(TaskBase):
    """Схема для создания задачи"""
    pass


class TaskRead(TaskBase):
    """Схема для получения данных задачи"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskUpdate(BaseModel):
    """Схема для обновления данных задачи"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    deadline_date: Optional[datetime] = None
    performer_id: Optional[int] = None
    team_id: Optional[int] = None
