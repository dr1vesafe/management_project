import pytest
from fastapi import status
from fastapi.security import OAuth2PasswordRequestForm

from src.app.main import app
from src.app.config import settings
from src.app.models.user import User
from src.app.auth.dependencies import get_current_user
from src.app.auth.user_manager import get_user_manager


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


@pytest.mark.asyncio
async def test_update_profile(client, session):
    """Тест изменения данных пользователя"""
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

    response = await client.post(
        '/users/profile/edit',
        data={'first_name': 'New', 'last_name': 'User', 'email': 'newuser@email.com'}
    )
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers['location'].startswith('/users/profile?message=')

    await session.refresh(test_user)
    assert test_user.first_name == 'New'
    assert test_user.email == 'newuser@email.com'

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_user(client, session):
    """Тест удаления пользователя"""
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

    response = await client.post('/users/delete')
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers['location'].startswith('/?message=')

    user_in_db = await session.get(User, test_user.id)
    assert user_in_db is None

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_change_password(client, session, monkeypatch):
    """Тест изменения пароля"""
    test_user = User(
        first_name='Test',
        last_name='User',
        email="testuser@email.com",
        hashed_password='oldhashed'
    )
    session.add(test_user)
    await session.commit()
    await session.refresh(test_user)

    class FakePasswordHelper:
        def hash(self, pwd: str) -> str:
            return f"hashed-{pwd}"

    class FakeUserManager:
        password_helper = FakePasswordHelper()
        async def authenticate(self, credentials: OAuth2PasswordRequestForm):
            return test_user if credentials.password == "oldpass" else None
        
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_user_manager] = lambda: FakeUserManager()

    response = await client.post(
        '/users/profile/change-password',
        data={'current_password': 'oldpass', 'new_password': 'Newpass123', 'confirm_password': 'Newpass123'}   
    )
    
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers['location'].startswith('/users/profile?message=')

    updated_user = await session.get(User, test_user.id)
    assert updated_user.hashed_password.startswith('hashed-')

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_admin_page_and_upgrade(client, session):
    """Тест получения роли admin"""
    test_user = User(
        first_name='Test',
        last_name='User',
        email="testuser@email.com",
        hashed_password='oldhashed',
        role='user'
    )
    session.add(test_user)
    await session.commit()
    await session.refresh(test_user)

    app.dependency_overrides[get_current_user] = lambda: test_user

    response = await client.get('/users/admin')
    assert response.status_code == status.HTTP_200_OK

    response = await client.post('/users/admin', data={'key': settings.SECRET})
    assert response.status_code == status.HTTP_303_SEE_OTHER
    await session.refresh(test_user)
    assert test_user.role == 'admin'

    app.dependency_overrides.clear()
