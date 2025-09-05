import secrets
import string

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.database import Base


def generate_team_code(length: int = 6) -> str:
    """Автоматическая генерация случайного кода команды"""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class Team(Base):
    """Модель для создания команд"""
    __tablename__ = 'teams'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    code: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, default=generate_team_code
    )
    
    members = relationship('User', back_populates='team', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f'<Team id={self.id} name={self.name} code={self.code}>'
    
    def __str__(self) -> str:
        return self.name
