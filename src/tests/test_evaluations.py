import pytest
from fastapi import status
from sqlalchemy import select

from src.app.models.user import User
from src.app.models.task import Task
from src.app.models.evaluation import Evaluation, EvaluationGrade
from src.app.main import app
from src.app.auth.dependencies import get_current_user


@pytest.mark.asyncio
async def test_create_evaluation_submit(client, session):
    """Тест создания оценки"""
    test_user = User(
        first_name='User',
        last_name='User',
        email='user@test.com',
        hashed_password='password',
        role='manager',
        team_id=1
    )
    test_task = Task(
        title='Task 1',
        description='Описание',
        performer_id=1,
        team_id=1
    )
    session.add_all([test_user, test_task])
    await session.commit()
    await session.refresh(test_user)
    await session.refresh(test_task)

    app.dependency_overrides[get_current_user] = lambda: test_user

    response = await client.post(
        f'/evaluations/task/{test_task.id}/create',
        data={'grade': 5, 'comment': 'Хорошая работа'}
    )
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers['location'] == f'/evaluations/task/{test_task.id}'

    result = await session.execute(
        select(Evaluation)
        .where(Evaluation.task_id == test_task.id)
    )
    evaluation = result.scalars().first()
    assert evaluation is not None
    assert evaluation.grade.value == 5
    assert evaluation.comment == 'Хорошая работа'


@pytest.mark.asyncio
async def test_edit_evaluation_submit(client, session):
    """Тест изменения оценки"""
    test_user = User(
        first_name='User',
        last_name='User',
        email='user@test.com',
        hashed_password='password',
        role='manager',
        team_id=1
    )
    test_task = Task(
        title='Task 1',
        description='Описание',
        performer_id=1,
        team_id=1
    )
    test_evaluation = Evaluation(
        task_id=1,
        manager_id=1,
        user_id=1,
        grade=EvaluationGrade.THREE
    )
    session.add_all([test_user, test_task, test_evaluation])
    await session.commit()
    await session.refresh(test_user)
    await session.refresh(test_task)
    await session.refresh(test_evaluation)

    app.dependency_overrides[get_current_user] = lambda: test_user

    response = await client.post(
        f'/evaluations/{test_evaluation.id}/edit',
        data={
            'grade': EvaluationGrade.FIVE.value,
            'comment': 'Новый комментарий'
        }
    )
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers['location'] == f'/evaluations/task/{test_task.id}'

    await session.refresh(test_evaluation)
    assert test_evaluation.grade.value == EvaluationGrade.FIVE.value
    assert test_evaluation.comment == 'Новый комментарий'


@pytest.mark.asyncio
async def test_delete_evaluation_submit(client, session):
    """Тест удаления оценки"""
    test_user = User(
        first_name='User',
        last_name='User',
        email='user@test.com',
        hashed_password='password',
        role='manager',
        team_id=1
    )
    test_task = Task(
        title='Task 1',
        description='Описание',
        performer_id=1,
        team_id=1
    )
    test_evaluation = Evaluation(
        task_id=1,
        manager_id=1,
        user_id=1,
        grade=EvaluationGrade.THREE
    )
    session.add_all([test_user, test_task, test_evaluation])
    await session.commit()
    await session.refresh(test_user)
    await session.refresh(test_task)
    await session.refresh(test_evaluation)

    app.dependency_overrides[get_current_user] = lambda: test_user

    response = await client.post(f'/evaluations/{test_evaluation.id}/delete')
    assert response.status_code == status.HTTP_303_SEE_OTHER
    assert response.headers['location'] == f'/evaluations/task/{test_task.id}'

    result = await session.execute(
        select(Evaluation)
        .where(Evaluation.id == test_evaluation.id)
    )
    deleted_eval = result.scalars().first()
    assert deleted_eval is None
