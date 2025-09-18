import pytest
from datetime import datetime, timezone, timedelta
from fastapi import status

from src.app.models.user import User
from src.app.models.meeting import Meeting
from src.app.services import meeting_crud
from src.app.main import app
from src.app.auth.dependencies import get_current_user


@pytest.mark.asyncio
async def test_create_meeting_submit(client, session, monkeypatch):
    """Тест создания встречи"""
    test_user = User(
        id=1,
        first_name='User',
        last_name='User',
        email='user@test.com',
        hashed_password='password',
        role='manager',
        team_id=1
    )
    session.add(test_user)
    await session.commit()
    await session.refresh(test_user)

    app.dependency_overrides[get_current_user] = lambda: test_user

    class DummyMeeting:
        id = 1

    async def dummy_create_meeting(db, data, u):
        return DummyMeeting()

    monkeypatch.setattr(meeting_crud, 'create_meeting', dummy_create_meeting)

    scheduled_at = datetime.now() + timedelta(hours=2)
    response = await client.post(
        '/meetings/create',
        data={
            'title': 'New Meeting',
            'description': 'Описание',
            'scheduled_at': scheduled_at,
            'team_id': 1,
            'organizer_id': test_user.id,
            'participant_ids': [],
            'add_all_team': False
        }
    )
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers['location'] == '/meetings/1'


@pytest.mark.asyncio
async def test_edit_meeting_submit(client, session, monkeypatch):
    """Тест изменеиня встречи"""
    test_user = User(
        id=1,
        first_name='User',
        last_name='User',
        email='user@test.com',
        hashed_password='password',
        role='manager',
        team_id=1
    )
    meeting = Meeting(
        title='Meeting 1',
        description='Описание',
        scheduled_at=datetime.now(timezone.utc),
        organizer_id=test_user.id,
        team_id=1
        )
    session.add_all([test_user, meeting])
    await session.commit()
    await session.refresh(test_user)
    await session.refresh(meeting)

    app.dependency_overrides[get_current_user] = lambda: test_user

    async def dummy_update_meeting(db, meeting_obj, data):
        return None

    monkeypatch.setattr(meeting_crud, 'update_meeting', dummy_update_meeting)

    scheduled_at = datetime.now() + timedelta(hours=2)
    response = await client.post(
        f'/meetings/{meeting.id}/edit',
        data={
            'title': 'Updated Meeting',
            'description': 'Новое описание',
            'scheduled_at': scheduled_at
        }
    )
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers['location'] == f'/meetings/{meeting.id}'


@pytest.mark.asyncio
async def test_delete_meeting_submit(client, session, monkeypatch):
    """Тест удаления встречи"""
    test_user = User(
        id=1,
        first_name='User',
        last_name='User',
        email='user@test.com',
        hashed_password='password',
        role='manager',
        team_id=1
    )
    meeting = Meeting(
        title='Meeting 1',
        description='Описание',
        scheduled_at=datetime.now(timezone.utc),
        organizer_id=test_user.id,
        team_id=1
        )
    session.add_all([test_user, meeting])
    await session.commit()
    await session.refresh(test_user)
    await session.refresh(meeting)

    app.dependency_overrides[get_current_user] = lambda: test_user

    async def dummy_delete_meeting(db, meeting_obj):
        return None

    monkeypatch.setattr(meeting_crud, 'delete_meeting', dummy_delete_meeting)

    response = await client.post(f'/meetings/{meeting.id}/delete')
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers['location'] == '/meetings'
