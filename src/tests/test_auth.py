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
        if (
            credentials.username == 'testuser@email.com'
            and credentials.password == 'password'
        ):
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
            raise Exception('Пользователь уже существует')
        user_dict = user_data.model_dump(
            exclude={
                'password',
                'password_confirm'
                }
            )
        user_dict['hashed_password'] = f'hashed-{user_data.password}'

        return User(id=1, **user_dict)


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


@pytest.mark.asyncio
async def test_register_submit_success(client):
    """Тест регистрации с верными данными"""
    response = await client.post(
        '/auth/register',
        data={
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'newuser@email.com',
            'password': 'Password123',
            'password_confirm': 'Password123'
        }
    )
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers['location'] == '/auth/login'


@pytest.mark.asyncio
async def test_register_submit_password_mismatch(client):
    """Тест регистрации с неправильным подтверждением пароля"""
    response = await client.post(
        '/auth/register',
        data={
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'newuser@email.com',
            'password': 'Password123',
            'password_confirm': 'Mismatch123'
        }
    )
    assert response.status_code == 200
    assert 'Пароли не совпадают' in response.text


@pytest.mark.asyncio
async def test_register_submit_existing_user(client):
    """Тест регистрации с email уже зарегистрированного пользователя"""
    response = await client.post(
        '/auth/register',
        data={
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'exists@email.com',
            'password': 'Password123',
            'password_confirm': 'Password123'
        }
    )
    assert response.status_code == 200
    assert 'Пользователь уже существует' in response.text


@pytest.mark.asyncio
async def test_logout(client):
    """Тест выхода из аккаунта"""
    response = await client.post('/auth/logout')
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers['location'] == '/'
