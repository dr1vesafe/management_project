import pytest
from fastapi import status
from sqlalchemy import select

from src.app.models.user import User
from src.app.models.task import Task, TaskStatus
from src.app.main import app
from src.app.auth.dependencies import get_current_user


@pytest.mark.asyncio
async def test_create_task_submit(client, session):
    """Тест создания задачи"""
    test_user = User(
        first_name='Manager',
        last_name='User',
        email='manager@test.com',
        hashed_password='password',
        role='manager',
        team_id=1
        )
    session.add(test_user)
    await session.commit()
    await session.refresh(test_user)

    app.dependency_overrides[get_current_user] = lambda: test_user

    response = await client.post(
        '/tasks/create',
        data={
            'title': 'Test Task',
            'description': 'Task description',
            'performer_id': test_user.id,
            'deadline': '2025-12-31T12:00'
        }
    )
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers['location'] == '/tasks'

    result = await session.execute(
        select(Task)
        .where(Task.title == 'Test Task')
    )
    task = result.scalars().first()
    assert task is not None
    assert task.performer_id == test_user.id
    assert task.status == TaskStatus.open


@pytest.mark.asyncio
async def test_update_task_status(client, session):
    """Тест изменения статуса задачи"""
    test_user = User(
        first_name='User',
        last_name='User',
        email='user@test.com',
        hashed_password='password',
        role='user',
        team_id=1
    )
    test_manager = User(
        first_name='Manager',
        last_name='Manager',
        email='manager@test.com',
        hashed_password='password',
        role='manager',
        team_id=1
    )
    session.add_all([test_user, test_manager])
    await session.commit()
    await session.refresh(test_user)
    await session.refresh(test_manager)
    test_task = Task(
        title='Status Task',
        description='Описание',
        performer_id=test_user.id,
        manager_id=test_manager.id,
        team_id=1,
        status='open'
    )
    session.add(test_task)
    await session.commit()
    await session.refresh(test_task)

    app.dependency_overrides[get_current_user] = lambda: test_user

    response = await client.post(
        f'/tasks/{test_task.id}/status',
        data={'new_status': 'done'}
    )
    assert response.status_code == status.HTTP_200_OK

    await session.refresh(test_task)
    assert test_task.status == TaskStatus.done
