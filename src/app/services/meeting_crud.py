from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.app.schemas.meeting import MeetingCreate
from src.app.models.meeting import Meeting
from src.app.models.meeting_participants import MeetingParticipant


async def create_meeting(db: AsyncSession, meeting_data: MeetingCreate) -> Meeting:
    """Создать встречу"""
    participants_data = meeting_data.participants or []
    meeting_dict = meeting_data.dict(exclude={'participants'})
    meeting = Meeting(**meeting_dict)

    db.add(meeting)
    await db.commit()
    await db.refresh(meeting)

    for participant in participants_data:
        participant_obj = MeetingParticipant(
            meeting_id=meeting.id,
            user_id=participant.user_id
        )
        db.add(participant_obj)

    await db.commit()
    await db.refresh(meeting)
    return meeting


async def get_meeting(db: AsyncSession, meeting_id: int) -> Meeting | None:
    """Получить встречу по id"""
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    return result.scalars().first()


async def get_all_meetings(db: AsyncSession) -> list[Meeting]:
    """Получить список всех встреч"""
    result = await db.execute(select(Meeting))
    return result.scalars().all()
