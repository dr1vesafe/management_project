from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.task import TaskStatus, Task
from src.app.models.user import User

STATUS_TRANSITIONS = {
    TaskStatus.open: TaskStatus.in_progress,
    TaskStatus.in_progress: TaskStatus.done,
    TaskStatus.done: None
}


async def change_task_status(
        db: AsyncSession,
        task: Task,
        new_status: TaskStatus,
        user: User
):
    """Изменить статус задачи"""
    if not task.performer_id or user.id != task.performer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Только исполнитель может менять статус задачи'
        )
    
    if task.status == new_status:
        return task
    
    allowed_next = STATUS_TRANSITIONS.get(task.status)
    if allowed_next != new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Невозможно изменение статуса {task.status} на {new_status}'
        )
    
    task.status = new_status
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task
