from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.app.models.evaluation import Evaluation
from src.app.schemas.evaluation import EvaluationCreate, EvaluationUpdate


async def create_evaluation(db: AsyncSession, evaluation_data: EvaluationCreate) -> Evaluation:
    """Создать оценку"""
    evaluation = Evaluation(**evaluation_data.dict())
    db.add(evaluation)
    await db.commit()
    await db.refresh(evaluation)
    return evaluation


async def get_evaluation(db: AsyncSession, evaluation_id: int) -> Evaluation | None:
    """Получить оценку по id"""
    result = await db.execute(select(Evaluation).where(Evaluation.id == evaluation_id))
    return result.scalars().first()


async def update_evaluation(
        db: AsyncSession,
        evaluation: Evaluation,
        evaluation_data: EvaluationUpdate
) -> Evaluation:
    """Изменить оценку"""
    for field, value in evaluation_data.dict(exclude_unset=True).items():
        setattr(evaluation, field, value)
    await db.commit()
    await db.refresh(evaluation)
    return evaluation


async def delete_evaluation(db: AsyncSession, evaluation: Evaluation) -> None:
    """Удалить оценку"""
    await db.delete(evaluation)
    await db.commit()
