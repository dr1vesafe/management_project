from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from src.app.models.evaluation import EvaluationGrade


class EvaluationBase(BaseModel):
    """Базовая схема оценок"""
    grade: EvaluationGrade
    comment: str | None = None
    manager_id: int | None = None
    user_id: int | None = None
    task_id: int


class EvaluationCreate(EvaluationBase):
    """Схема для создания оценки"""
    pass


class EvaluationRead(EvaluationBase):
    """Схема для получения данных оценки"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class EvaluationUpdate(BaseModel):
    """Схема для обновления данных оценки"""
    grade: Optional[EvaluationGrade] = None
    comment: Optional[str] = None
