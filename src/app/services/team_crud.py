from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.app.models.team import Team
from src.app.schemas.team import TeamCreate, TeamUpdate


async def create_team(db: AsyncSession, team_data: TeamCreate) -> Team:
    """Создать команду"""
    team = Team(**team_data.model_dump())
    db.add(team)
    await db.commit()
    await db.refresh(team)
    return team


async def get_team(db: AsyncSession, team_id: int) -> Team | None:
    """Получить команду по id"""
    result = await db.execute(select(Team).where(Team.id == team_id))
    return result.scalars().first()


async def update_team(db: AsyncSession, team: Team, team_data: TeamUpdate) -> Team:
    """Изменить команду"""
    for field, value in team_data.model_dump(exclude_unset=True).items():
        setattr(team, field, value)
    await db.commit()
    await db.refresh(team)
    return team


async def delete_team(db: AsyncSession, team: Team) -> None:
    """Удалить команду"""
    await db.delete(team)
    await db.commit()
