from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, UniqueConstraint

from src.app.database import Base


class MeetingParticipant(Base):
    """Промежуточная таблица для связи User и Meeting"""
    __tablename__ = 'meeting_participants'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    meeting_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('meetings.id', ondelete='CASCADE'),
        nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )

    __table_args__ = (UniqueConstraint(
        'meeting_id',
        'user_id',
        name='uq_meeting_user'),
    )

    user = relationship('User', back_populates='meetings')
    meeting = relationship('Meeting', back_populates='participants')

    def __repr__(self) -> str:
        return (
            f'<Meeting id = {self.meeting_id}, '
            f'participant id = {self.user_id}>'
        )

    def __str__(self) -> str:
        return f'Meeting {self.meeting_id} | User {self.user_id}'
