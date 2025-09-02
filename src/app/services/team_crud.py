from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.app.models.team import Team
from src.app.schemas.team import TeamCreate


async def create_team(db: AsyncSession, team_data: TeamCreate) -> Team:
    """Создать команду"""
    team = Team(**team_data.dict())
    db.add(team)
    await db.commit()
    await db.refresh(team)
    return team


async def get_team(db: AsyncSession, team_id: int) -> Team | None:
    """Получить команду по id"""
    result = await db.execute(select(Team).where(Team.id == team_id))
    return result.scalars().first()
