from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.models.evaluation import Evaluation
from src.app.models.user import User

GRADE_TO_INT = {
    'ONE': 1,
    'TWO': 2,
    'THREE': 3,
    'FOUR': 4,
    'FIVE': 5
}


async def get_average_by_user(db: AsyncSession, user_id: int) -> float | None:
    """Вычисление средней оценки пользователя"""
    case_stmt = case(
        *(
            (Evaluation.grade == grade, value)
            for grade, value in GRADE_TO_INT.items()
        ),
        else_=0
    )
    result = await db.execute(
        select(func.avg(case_stmt)).where(Evaluation.user_id == user_id)
    )
    avg_grade = result.scalar()
    return float(avg_grade) if avg_grade is not None else None


async def get_average_grade_by_team(
        db: AsyncSession,
        team_id: int
) -> float | None:
    """Вычисление средней оценки по команде"""
    case_stmt = case(
        *(
            (Evaluation.grade == grade, value)
            for grade, value in GRADE_TO_INT.items()
            ),
        else_=0
    )
    result = await db.execute(
        select(func.avg(case_stmt))
        .join(User, Evaluation.user_id == User.id)
        .where(User.team_id == team_id)
    )
    avg_grade = result.scalar()
    return float(avg_grade) if avg_grade is not None else None
