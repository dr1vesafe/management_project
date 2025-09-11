import pytest
from fastapi import status
from fastapi.security import OAuth2PasswordRequestForm

from src.app.main import app
from src.app.models.user import User
from src.app.auth.user_manager import get_user_manager


class FakePasswordHelper:
    def hash(self, pwd: str) -> str:
        return f'hashed-{pwd}'

class FakeUserManager:
    password_helper = FakePasswordHelper()

    async def authenticate(self, credentials: OAuth2PasswordRequestForm):
        if credentials.username == 'testuser@email.com' and credentials.password == 'password':
            return User(
                id=1,
                email='testuser@email.com',
                first_name='Test',
                last_name='User',
                hashed_password='oldhashed'
            )
        return None

    async def create(self, user_data):
        if user_data.email == 'exists@email.com':
            raise Exception('User already exists')
        return User(id=1, **user_data.dict(), hashed_password=f'hashed-{user_data.password}')
    

@pytest.fixture(autouse=True)
def override_dependencies():
    app.dependency_overrides[get_user_manager] = lambda: FakeUserManager()
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_login_submit_success(client):
    """Тест входа с верными данными"""
    response = await client.post(
        '/auth/login',
        data={'username': 'testuser@email.com', 'password': 'password'}
    )
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers['location'] == '/'


@pytest.mark.asyncio
async def test_login_submit_fail(client):
    """Тест входа с неверными данными"""
    response = await client.post(
        '/auth/login',
        data={'username': 'wrong@email.com', 'password': 'wrong'}
    )
    assert response.status_code == 200
    assert 'Неверный email или пароль' in response.text
