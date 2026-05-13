import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from starlette import status

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas import MovieListResponseSchema
from schemas.movies import MovieCreateResponseSchema, MovieCreateSchema, MovieDetailSchema, MovieUpdateSchema

from utils.utils import get_or_create, movie_with_relations

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def list_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(ge=1, default=1),
    per_page: int = Query(ge=1, le=20, default=10),
):
    total_items = (await db.execute(select(func.count()).select_from(MovieModel))).scalar()
    total_pages = 1 if total_items == 0 else math.ceil(total_items / per_page)
    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    queryset = (
        select(MovieModel).order_by(MovieModel.id.desc()).offset((page - 1) * per_page).limit(per_page)
    )
    result = await db.execute(queryset)
    movies = result.scalars().all()
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")
    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post("/movies/", response_model=MovieCreateResponseSchema, status_code=201)
async def add_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=await get_or_create(db=db, model=CountryModel, code=movie.country),
        genres=[await get_or_create(db=db, model=GenreModel, name=genre) for genre in movie.genres],
        actors=[await get_or_create(db=db, model=ActorModel, name=actor) for actor in movie.actors],
        languages=[await get_or_create(db=db, model=LanguageModel, name=language) for language in movie.languages],
    )
    try:
        db.add(new_movie)
        await db.commit()
        result = await db.execute(
            select(MovieModel)
            .where(MovieModel.id == new_movie.id)
            .options(*movie_with_relations())
        )
        new_movie = result.scalar_one()
        return new_movie
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' and "
                   f"release date '{movie.date}' already exists."
        )


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    queryset = await db.execute(
        select(MovieModel)
        .where(MovieModel.id == movie_id)
        .options(*movie_with_relations())
    )
    movie = queryset.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    queryset = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = queryset.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/")
async def update_movie(movie_id: int, movie: MovieUpdateSchema, db: AsyncSession = Depends(get_db)):
    queryset = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    updated_movie = queryset.scalar_one_or_none()
    if not updated_movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    for field, value in movie.model_dump(exclude_unset=True).items():
        setattr(updated_movie, field, value)
    await db.commit()
    return {"detail": "Movie updated successfully."}
