from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, UniqueConstraint

from src.app.database import Base


class MeetingParticipant(Base):
    __tablename__ = 'meeting_participants'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    meeting_id: Mapped[int] = mapped_column(Integer, ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    __table_args__ = (UniqueConstraint('meeting_id', 'user_id', name='uq_meeting_user'),)

    user = relationship('User', back_populates='meetings')
    meeting = relationship('Meeting', back_populates='participants')
