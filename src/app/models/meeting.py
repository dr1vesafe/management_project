from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey

from src.app.database import Base


class Meeting(Base):
    """Модель для организации встреч"""
    __tablename__ = 'meetings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    organizer_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    organizer = relationship('User', back_populates='organized_meetings')
    
    team_id: Mapped[int] = mapped_column(ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)
    team = relationship('Team', backref='meetings')

    participants = relationship('MeetingParticipant', back_populates='meeting', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f'<Meeting id={self.id} title={self.title} sheduled_at={self.scheduled_at}>'

    def __str__(self) -> str:
        return f'{self.title} | Team {self.team_id}'
    