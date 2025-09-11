import pytest
from fastapi import status

from src.app.main import app
from src.app.models.user import User
from src.app.auth.dependencies import get_current_user


@pytest.mark.asyncio
async def test_create_team_submit(client, session):
    """Тест создания команды"""
    test_user = User(
        first_name='Test',
        last_name='User',
        email="testuser@email.com",
        hashed_password='password',
        role='user'
    )
    session.add(test_user)
    await session.commit()
    await session.refresh(test_user)

    app.dependency_overrides[get_current_user] = lambda: test_user

    response = await client.post('/teams/create', data={'name': 'My Team'})
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers['location'].startswith('/?message=')

    await session.refresh(test_user)
    assert test_user.team_id is not None
    assert test_user.role == 'manager'
