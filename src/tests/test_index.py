from datetime import datetime, timedelta, UTC

import pytest
from fastapi import status

from src.app.main import app
from src.app.models.user import User
from src.app.models.team import Team
from src.app.models.task import Task
from src.app.models.meeting import Meeting
from src.app.auth.dependencies import get_current_user


@pytest.mark.asyncio
async def test_index_authenticated_user(client, session):
    """Тест главной страницы с аутентифицированным пользователем"""
    test_team = Team(name="Test Team")
    session.add(test_team)
    await session.commit()
    await session.refresh(test_team)

    test_user = User(
        first_name='test',
        last_name='user',
        email="testuser@email.com",
        hashed_password='password',
        team_id=test_team.id
    )
    session.add(test_user)
    await session.commit()
    await session.refresh(test_user)

    test_task = Task(
        title='Test Task',
        description='Test Desrciption',
        performer_id=test_user.id,
        status="open",
        team_id=test_team.id
    )
    session.add(test_task)

    test_meeting = Meeting(
        title='Test Meeting',
        scheduled_at=datetime.now(UTC) + timedelta(days=1),
        organizer_id=test_user.id,
        team_id=test_team.id
        )
    session.add(test_meeting)
    await session.commit()

    app.dependency_overrides[get_current_user] = lambda: test_user

    response = await client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert "testuser@email.com" in response.text
    assert "Test Team" in response.text


@pytest.mark.asyncio
async def test_index_anonymous_user(client):
    """Тест главной страницы для анонимного пользователя"""
    app.dependency_overrides[get_current_user] = lambda: None

    client.cookies.set('refresh_token', 'token')
    response = await client.get('/')
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers['location'] == '/auth/refresh?next=/'
