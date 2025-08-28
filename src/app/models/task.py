from enum import Enum
from datetime import datetime

from sqlalchemy import Integer, String, Text, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.database import Base


class TaskStatus(str, Enum):
    """Варианты статуса задачи"""
    open = 'open'
    in_progress = 'in_progress'
    done = 'done'


class Task(Base):
    """Модель для создания задач"""
    __tablename__ = 'tasks'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=False)
    status: Mapped[TaskStatus] = mapped_column(SQLEnum(TaskStatus), default=TaskStatus.open, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deadline_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    performer_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    performer = relationship('User', backref='tasks')

    team_id: Mapped[int] = mapped_column(Integer, ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)
    team = relationship('Team', backref='tasks')

    evaluations = relationship('Evaluation', back_populates='task', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f'<Task id={self.id} title={self.title} status={self.status}>'
