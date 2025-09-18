from datetime import datetime, timedelta, timezone
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic_core import PydanticCustomError

MSK = timezone(timedelta(hours=3))


class MeetingParticipantBase(BaseModel):
    """Базовая схема участника встречи"""
    user_id: int


class MeetingParticipantCreate(MeetingParticipantBase):
    """Схема для добавления участника встречи"""
    pass


class MeetingParticipantRead(MeetingParticipantBase):
    """Схема для получения данных участника встречи"""
    id: int

    model_config = ConfigDict(from_attributes=True)


class MeetingBase(BaseModel):
    """Базовая схема встречи"""
    title: str
    description: Optional[str] = None
    scheduled_at: datetime
    organizer_id: Optional[int] = None
    team_id: Optional[int] = None
    participants: Optional[List[MeetingParticipantRead]] = []


class MeetingCreate(MeetingBase):
    """Схема для создания встречи"""
    participants_id: Optional[List[int]] = []
    add_team_members: bool = False

    @field_validator('scheduled_at')
    def validate_scheduled_at(cls, value: datetime) -> datetime:
        if value < datetime.now(MSK).replace(tzinfo=None):
            raise PydanticCustomError(
                'incorrect_date',
                'Дата встречи не может быть в прошлом'
            )
        return value


class MeetingRead(MeetingBase):
    """Схема для получения данных встречи"""
    id: int
    created_at: datetime
    participants: list[MeetingParticipantRead] = []

    model_config = ConfigDict(from_attributes=True)


class MeetingUpdate(MeetingBase):
    """Схема для обновления данных встречи"""
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    participants: Optional[List[MeetingParticipantCreate]] = None

    @field_validator('scheduled_at')
    def validate_scheduled_at(cls, value: datetime) -> datetime:
        if value < datetime.now(MSK).replace(tzinfo=None):
            raise PydanticCustomError(
                'incorrect_date',
                'Дата встречи не может быть в прошлом'
            )
        return value
