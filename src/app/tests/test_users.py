import pytest
from fastapi import status

from src.app.main import app
from src.app.models.user import User
from src.app.auth.dependencies import get_current_user


@pytest.mark.asyncio
async def test_profile_authenticated_user(client, session):
    """Тест профиля для аутентифицированного пользователя"""
    test_user = User(
        first_name='Test',
        last_name='User',
        email="testuser@email.com",
        hashed_password='password'
    )
    session.add(test_user)
    await session.commit()
    await session.refresh(test_user)

    app.dependency_overrides[get_current_user] = lambda: test_user

    response = await client.get('/users/profile')
    assert response.status_code == status.HTTP_200_OK
    assert 'Test' in response.text

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_profile_anonymous_user(client):
    """Тест профиля для анонимного пользователя"""
    response = await client.get('/users/profile')
    assert response.status_code == status.HTTP_200_OK
    assert 'Войдите в аккаунт' in response.text
