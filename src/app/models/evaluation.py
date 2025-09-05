from datetime import datetime
from enum import IntEnum

from sqlalchemy import Integer, Text, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.database import Base


class EvaluationGrade(IntEnum):
    """Варианты оценок"""
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5


class Evaluation(Base):
    """Модель для оценок задач"""
    __tablename__ = 'evaluations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    grade: Mapped[EvaluationGrade] = mapped_column(
        SQLEnum(EvaluationGrade, native_enum=False, validate_strings=True),
        nullable=False
    )

    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    manager_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    manager = relationship('User', back_populates='given_evaluations', foreign_keys=[manager_id])

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    user = relationship('User', back_populates='received_evaluations', foreign_keys=[user_id])

    task_id: Mapped[int] = mapped_column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    task = relationship('Task', back_populates='evaluations')

    def __repr__(self) -> str:
        return f'<Evaluation id={self.id} score={self.grade} user_id={self.user_id} task_id={self.task_id}>'
    
    def __str__(self) -> str:
        return f'Grade {self.grade} | Manager {self.manager_id} | User {self.user_id} | Task {self.task_id}'
