from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.app.schemas.meeting import MeetingCreate, MeetingUpdate
from src.app.models.meeting import Meeting
from src.app.models.meeting_participants import MeetingParticipant


async def create_meeting(db: AsyncSession, meeting_data: MeetingCreate) -> Meeting:
    """Создать встречу"""
    participants_id = meeting_data.participants_id or []
    meeting_dict = meeting_data.dict(exclude={'participants_id'})
    meeting = Meeting(**meeting_dict)

    db.add(meeting)
    await db.commit()
    await db.refresh(meeting)

    for participant_id in participants_id:
        participant_obj = MeetingParticipant(
            meeting_id=meeting.id,
            user_id=participant_id
        )
        db.add(participant_obj)

    await db.commit()

    result = await db.execute(
        select(Meeting)
        .options(selectinload(Meeting.participants))
        .where(Meeting.id == meeting.id)
    )
    meeting = result.scalar_one()

    return meeting


async def get_meeting(db: AsyncSession, meeting_id: int) -> Meeting | None:
    """Получить встречу по id"""
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    return result.scalars().first()


async def get_all_meetings(db: AsyncSession) -> list[Meeting]:
    """Получить список всех встреч"""
    result = await db.execute(select(Meeting))
    return result.scalars().all()


async def update_meeting(
        db: AsyncSession,
        meeting: Meeting,
        meeting_data: MeetingUpdate
) -> Meeting:
    """Изменение встречи"""
    data = meeting_data.dict(exclude_unset=True)

    if 'participants' in data:
        participants_data = data.pop('participants')
        await db.execute(
            select(MeetingParticipant).where(MeetingParticipant.meeting_id == meeting.id)
        )

        await db.execute(
            MeetingParticipant.__table__.delete().where(MeetingParticipant.meeting_id == meeting.id)
        )

        if participants_data:
            for p in participants_data:
                participant_obj = MeetingParticipant(
                    meeting_id=meeting.id,
                    user_id=p.user_id
                )
                db.add(participant_obj)

    for field, value in data.items():
        setattr(meeting, field, value)

    await db.commit()
    await db.refresh(meeting)
    return meeting


async def delete_meeting(db: AsyncSession, meeting: Meeting) -> None:
    """Удалить встречу"""
    await db.delete(meeting)
    await db.commit()
