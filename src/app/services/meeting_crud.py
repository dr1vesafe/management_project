from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.app.schemas.meeting import MeetingCreate, MeetingUpdate
from src.app.models.meeting import Meeting
from src.app.models.meeting_participants import MeetingParticipant
from src.app.models.user import User


async def create_meeting(
        db: AsyncSession,
        meeting_data: MeetingCreate,
        user: User
) -> Meeting:
    """Создать встречу"""
    participants_id = set(meeting_data.participants_id or [])

    if not meeting_data.organizer_id:
        meeting_data.organizer_id = user.id

    if not meeting_data.team_id:
        meeting_data.team_id = user.team_id

    if participants_id:
        valid_ids = await db.scalars(
            select(User.id)
            .where(
                User.id.in_(participants_id),
                User.team_id == meeting_data.team_id
            )
        )
        valid_ids = set(valid_ids.all())
        invalid_ids = participants_id - valid_ids
        if invalid_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f'Пользователи {invalid_ids} '
                    f'не состоят в команде {meeting_data.team_id}'
                )
            )

    if meeting_data.add_team_members:
        team_users = await db.execute(
            select(User.id).where(User.team_id == meeting_data.team_id)
        )
        team_user_ids = {user_id for (user_id,) in team_users.all()}
        participants_id.update(team_user_ids)

    meeting_dict = meeting_data.model_dump(
        exclude={
            'participants_id',
            'add_team_members'
        }
    )
    meeting = Meeting(**meeting_dict)
    db.add(meeting)
    await db.flush()

    participant_objs = [
        MeetingParticipant(meeting_id=meeting.id, user_id=pid)
        for pid in participants_id
    ]
    db.add_all(participant_objs)

    await db.commit()
    await db.refresh(meeting)

    result = await db.execute(
        select(Meeting)
        .options(selectinload(Meeting.participants))
        .where(Meeting.id == meeting.id)
    )

    return result.scalar_one()


async def get_meeting(db: AsyncSession, meeting_id: int) -> Meeting | None:
    """Получить встречу по id"""
    result = await db.execute(select(Meeting).where(Meeting.id == meeting_id))
    return result.scalars().first()


async def update_meeting(
        db: AsyncSession,
        meeting: Meeting,
        meeting_data: MeetingUpdate
) -> Meeting:
    """Изменение встречи"""
    data = meeting_data.model_dump(exclude_unset=True)

    if 'participants' in data:
        participants_data = data.pop('participants')
        await db.execute(
            select(MeetingParticipant)
            .where(MeetingParticipant.meeting_id == meeting.id)
        )

        await db.execute(
            MeetingParticipant.__table__.delete().
            where(MeetingParticipant.meeting_id == meeting.id)
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
