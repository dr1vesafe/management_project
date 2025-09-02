from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.app.models.task import Task
from src.app.schemas.task import TaskCreate


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
