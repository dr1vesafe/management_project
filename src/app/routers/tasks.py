from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from src.app.schemas.task import TaskRead, TaskCreate, TaskUpdate
from src.app.database import get_db
from src.app.auth.dependencies import get_current_user, require_role
from src.app.models.user import User
from src.app.models.task import TaskStatus, Task
from src.app.services import task_crud, task_service

router = APIRouter(prefix='/tasks', tags=['tasks'])
templates = Jinja2Templates(directory='src/app/templates')


async def check_task(
        db: AsyncSession,
        task_id: int,
        user: User
):
    task = await task_crud.get_task(db, task_id)

    if task.team_id != user.team_id and user.role != 'admin':
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = 'Недостаточно прав'
        )
    
    if not task:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = 'Задача не найдена'
        )
    
    return task


# Маршруты для пользователей
@router.get('/')
async def tasks_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    status: Optional[str] = Query(None),
    my_tasks: bool = Query(False)
):
    """Страница со списком задач"""
    limit = 10
    offset = (page - 1) * limit
    query = select(Task).where(Task.team_id == user.team_id).options(selectinload(Task.performer))
    count_query = select(func.count(Task.id)).where(Task.team_id == user.team_id)
    status_enum = None
    if status:
        try:
            status_enum = TaskStatus(status)
        except ValueError:
            status_enum = None
    
    if status_enum:
        query = query.where(Task.status == status_enum)
        count_query = count_query.where(Task.status == status_enum)
    
    if my_tasks:
        query = query.where(Task.performer_id == user.id)
        count_query = count_query.where(Task.performer_id == user.id)

    total_tasks = await db.scalar(count_query)
    total_pages = max((total_tasks + limit - 1) // limit, 1)

    query = query.offset(offset).limit(limit)
    tasks = (await db.execute(query)).scalars().all()

    return templates.TemplateResponse(
        request,
        'task/tasks.html',
        {
            'tasks': tasks,
            'page': page,
            'total_pages': total_pages,
            'status': status or '',
            'my_tasks': my_tasks,
            'user': user
        }
    )


@router.get('/create')
async def create_task_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin'))
):
    """Страница создания задачи"""
    performers = (await db.execute(select(User).where(User.team_id == user.team_id))).scalars().all()
    return templates.TemplateResponse(
        request,
        'task/create_task.html',
        {'performers': performers, 'user': user}
    )

@router.post('/create')
async def create_task_submit(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    performer_id: int = Form(...),
    deadline: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('manager', 'admin'))
    ):
    """Создание задачи"""
    deadline_date = None
    if deadline:
        try:
            deadline_date = datetime.strptime(deadline, '%Y-%m-%dT%H:%M')
        except ValueError:
            pass

    task_data = TaskCreate(
        title=title,
        description=description,
        performer_id=performer_id,
        status='open',
        deadline_date=deadline_date,
        team_id=user.team_id
    )
    await task_crud.create_task(db, task_data)
    
    return RedirectResponse(url='/tasks', status_code=status.HTTP_303_SEE_OTHER)


@router.get('/{task_id}')
async def task_detail_page(
    task_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Детальная страница задачи"""
    result = await db.execute(
        select(Task)
        .where(Task.id == task_id)
        .options(selectinload(Task.performer))
    )
    task = result.scalars().first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Задача не найдена'
        )
    
    if user.team_id != task.team_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Задача не найдена'
        )
    
    can_change_status = (
        user.id == task.performer_id
        or user.role in ('manager', 'admin')
    )

    return templates.TemplateResponse(
        request,
        'task/task_detail.html',
        {
            'task': task,
            'can_change_status': can_change_status,
            'user': user
        }
    )


@router.post('/{task_id}/status')
async def update_task_status(
    task_id: int,
    request: Request,
    new_status: TaskStatus = Form(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Изменение статуса задачи"""
    result = await db.execute(
        select(Task)
        .where(Task.id == task_id)
        .options(selectinload(Task.performer))
    )
    task = result.scalars().first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Задача не найдена'
        )
    
    if user.team_id != task.team_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Задача не найдена'
        )

    if not (
        user.id == task.performer_id
        or user.role in ('manager', 'admin')
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            deatil='Недостаточно прав'
        )
    
    task.status = new_status
    db.add(task)
    await db.commit()
    await db.refresh(task)

    return templates.TemplateResponse(
        request,
        'task/task_detail.html',
        {
            'task': task,
            'can_change_status': True,
            'message': 'Статус задачи обновлен',
            'user': user
        }
    )


# Маршруты для администраторов
@router.post('/admin/create', response_model=TaskRead)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('admin')),
):
    """
    Создание задачи
    (доступно только админам)
    """
    return await task_crud.create_task(db, task_data)


@router.get('/admin/{team_id}', response_model=list[TaskRead])
async def get_tasks_by_team(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('admin')),
    task_status: Optional[TaskStatus] = Query(None, description='Фильтраци по статусу задачи'),
    performer_id: Optional[int] = Query(None, description='Фильтрация по пользователю'),
    deadline_before: Optional[datetime] = Query(None, description='Дедлайн до даты'),
    deadline_after: Optional[datetime] = Query(None, description='Дедлайн после даты'),
    limit: int = Query(10, ge=1, le=100, description='Количество записей'),
    offset: int = Query(0, ge=0, description='Смещение'),
):
    """
    Получить задачи для команды
    (доступно только админам)
    """
    stmt = select(Task).where(Task.team_id == team_id)

    if task_status:
        stmt = stmt.where(Task.status == task_status)
    if performer_id:
        stmt = stmt.where(Task.performer_id == performer_id)
    if deadline_before:
        stmt = stmt.where(Task.deadline_date <= deadline_before)
    if deadline_after:
        stmt = stmt.where(Task.deadline_date >= deadline_after)

    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get('/admin/all', response_model=list[TaskRead])
async def get_all_tasks(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role('admin')),
    task_status: Optional[TaskStatus] = Query(None, description='Фильтраци по статусу задачи'),
    performer_id: Optional[int] = Query(None, description='Фильтрация по пользователю'),
    team_id: Optional[int] = Query(None, description='Фильрация по команде'),
    deadline_before: Optional[datetime] = Query(None, description='Дедлайн до даты'),
    deadline_after: Optional[datetime] = Query(None, description='Дедлайн после даты'),
    limit: int = Query(10, ge=1, le=100, description='Количество записей'),
    offset: int = Query(0, ge=0, description='Смещение'),
):
    """
    Получить список всех задач
    (доступно только админам)
    """
    stmt = select(Task)

    if task_status:
        stmt = stmt.where(Task.status == task_status)
    if performer_id:
        stmt = stmt.where(Task.performer_id == performer_id)
    if team_id:
        stmt = stmt.where(Task.team_id == team_id)
    if deadline_before:
        stmt = stmt.where(Task.deadline_date <= deadline_before)
    if deadline_after:
        stmt = stmt.where(Task.deadline_date >= deadline_after)

    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get('/admin/{task_id}', response_model=TaskRead)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('admin')),
):
    """
    Получить задачу по id
    (доступно только админам)
    """
    task = await check_task(db, task_id, user)
    
    return task


@router.put('/admin/{task_id}', response_model=TaskRead)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('admin')),
):
    """
    Изменить задачу по id
    (доступно только админам)
    """
    task = await check_task(db, task_id, user)
    
    return await task_crud.update_task(db, task=task, task_data=task_data)


@router.delete('/admin/{task_id}')
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role('admin')),
):
    """
    Удалить задачу по id
    (доступно только админам)
    """
    task = await check_task(db, task_id, user)
    
    await task_crud.delete_task(db, task)
    return {'detail': f'Задача {task_id} удалена'}
