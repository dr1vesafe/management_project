from enum import Enum

from sqlalchemy import String, Boolean, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.database import Base


class UserRole(str, Enum):
    user = 'user'
    manager = 'manager'
    admin = 'admin'


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.user, nullable=False)

    team_id: Mapped[int] = mapped_column(Integer, ForeignKey('teams.id', ondelete='SET NULL'), nullable=True)
    team = relationship('Team', back_populates='members')

    meetings = relationship('MeetingParticipant', back_populates='user', cascade='all, delete-orphan')

    given_evaluations = relationship('Evaluation', back_populates='manager', foreign_keys='Evaluation.manager_id')

    received_evaluations = relationship('Evaluation', back_populates='user', foreign_keys='Evaluation.user_id')
    
    def __repr__(self):
        return f'<Use id={self.id} email={self.email} role={self.role}>'
