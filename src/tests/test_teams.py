import pytest
from fastapi import status

from src.app.main import app
from src.app.models.user import User
from src.app.models.team import Team
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


@pytest.mark.asyncio
async def test_leave_team(client, session):
    """Тест выхода из команды"""
    test_team = Team(name='Team1')
    session.add(test_team)
    await session.commit()
    await session.refresh(test_team)

    test_user = User(
        first_name='Test',
        last_name='User',
        email='user@test.com',
        hashed_password='password',
        role='manager',
        team_id=test_team.id
    )
    session.add(test_user)
    await session.commit()
    await session.refresh(test_user)

    app.dependency_overrides[get_current_user] = lambda: test_user

    response = await client.post('/teams/leave-team')
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers['location'].startswith('/?message=')

    await session.refresh(test_user)
    assert test_user.team_id is None
    assert test_user.role == 'user'


@pytest.mark.asyncio
async def test_join_team(client, session):
    """Тест вступления в команду по коду"""
    test_team = Team(name='TeamJoin', code='TEAM123')
    session.add(test_team)
    await session.commit()
    await session.refresh(test_team)

    test_user = User(
        first_name='Test',
        last_name='User',
        email='user@test.com',
        hashed_password='password',
        role='user'
    )
    session.add(test_user)
    await session.commit()
    await session.refresh(test_user)

    app.dependency_overrides[get_current_user] = lambda: test_user

    response = await client.post('/teams/join-team', data={'team_code': 'TEAM123'})
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers['location'].startswith('/?message=')

    await session.refresh(test_user)
    assert test_user.team_id == test_team.id


@pytest.mark.asyncio
async def test_edit_team_submit(client, session):
    """Тест изменения команды"""
    test_team = Team(name='OldName')
    session.add(test_team)
    await session.commit()
    await session.refresh(test_team)

    test_user = User(
        first_name='Test',
        last_name='User',
        email='user@test.com',
        hashed_password='password',
        role='manager',
        team_id=test_team.id
    )
    session.add(test_user)
    await session.commit()
    await session.refresh(test_user)

    app.dependency_overrides[get_current_user] = lambda: test_user

    response = await client.post(f'/teams/{test_team.id}/edit', data={'name': 'NewName'})
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers['location'] == f'/teams/{test_team.id}'

    await session.refresh(test_team)
    assert test_team.name == 'NewName'
