from enum import Enum

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

from src.app.database import Base


class UserRole(str, Enum):
    user = 'user'
    manager = 'manager'
    admin = 'admin'


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    role = Column(SQLEnum(UserRole), default=UserRole.user, nullable=False)

    def __repr__(self):
        return f'<Use id={self.id} email={self.email} role={self.role}>'
