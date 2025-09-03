from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class MeetingParticipantBase(BaseModel):
    """Базовая схема участника встречи"""
    user_id: int


class MeetingParticipantCreate(MeetingParticipantBase):
    """Схема для добавления участника встречи"""
    pass


class MeetingParticipantRead(MeetingParticipantBase):
    """Схема для получения данных участника встречи"""
    id: int

    class Config:
        from_attributes = True


class MeetingBase(BaseModel):
    """Базовая схема встречи"""
    title: str
    description: Optional[str] = None
    scheduled_at: datetime
    organizer_id: int
    team_id: int
    participants: Optional[List[MeetingParticipantRead]] = []


class MeetingCreate(MeetingBase):
    """Схема для создания встречи"""
    participants_id: Optional[List[int]] = []


class MeetingRead(MeetingBase):
    """Схема для получения данных встречи"""
    id: int
    created_at: datetime
    participants: list[MeetingParticipantRead] = []

    class Config:
        from_attributes = True


class MeetingUpdate(MeetingBase):
    """Схема для обновления данных встречи"""
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    participants: Optional[List[MeetingParticipantCreate]] = None
