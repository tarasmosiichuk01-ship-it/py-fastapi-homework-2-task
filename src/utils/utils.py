from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from database import MovieModel


async def get_or_create(db: AsyncSession, model, **kwargs):
    result = await db.execute(select(model).filter_by(**kwargs))
    instance = result.scalar_one_or_none()
    if not instance:
        instance = model(**kwargs)
        db.add(instance)
    return instance


def movie_with_relations():
    return (
        selectinload(MovieModel.country),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages),
    )
