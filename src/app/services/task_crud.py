from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.app.models.task import Task
from src.app.schemas.task import TaskCreate, TaskUpdate


async def create_task(db: AsyncSession, task_data: TaskCreate) -> Task:
    """Создать задачу"""
    task = Task(**task_data.dict())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def get_task(db: AsyncSession, task_id: int) -> Task | None:
    """Получить задачу по id"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    return result.scalars().first()


async def get_tasks(db: AsyncSession) -> list[Task]:
    """Получить все задачи"""
    result = await db.execute(select(Task))
    return result.scalars().all()


async def get_tasks_by_team(db: AsyncSession, team_id: int) -> list[Task]:
    """Получить список задач для команды"""
    result = await db.execute(select(Task).where(Task.team_id == team_id))
    return result.scalars().all()


async def update_task(db: AsyncSession, task: Task, task_data: TaskUpdate) -> Task:
    """Изменить задачу"""
    for field, value in task_data.dict(exclude_unset=True).items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task: Task) -> None:
    """Удалить задачу"""
    await db.delete(task)
    await db.commit()
