from datetime import date as date_type, timedelta

from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.models import MovieStatusEnum


class CountrySchema(BaseModel):
    id: int
    code: str
    name: str | None = None


class GenreSchema(BaseModel):
    id: int
    name: str


class ActorSchema(BaseModel):
    id: int
    name: str


class LanguageSchema(BaseModel):
    id: int
    name: str


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date_type
    score: float
    overview: str

    model_config = ConfigDict(from_attributes=True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None = None
    next_page: str | None = None
    total_pages: int
    total_items: int

    model_config = ConfigDict(from_attributes=True)


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: date_type
    score: float = Field(..., ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    country: str = Field(..., max_length=3, description="ISO 3166-1 alpha-3 country code")
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @field_validator("date")
    @classmethod
    def validate_date(cls, value):
        if value > date_type.today() + timedelta(days=365):
            raise ValueError("Date must not be more than one year in the future")
        return value

    model_config = ConfigDict(from_attributes=True)


class MovieCreateResponseSchema(BaseModel):
    id: int
    name: str
    date: date_type
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date_type
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]

    model_config = ConfigDict(from_attributes=True)


class MovieUpdateSchema(BaseModel):
    name: str | None = None
    date: date_type | None = None
    score: float | None = Field(None, ge=0, le=100)
    overview: str | None = None
    status: MovieStatusEnum | None = None
    budget: float | None = Field(None, ge=0)
    revenue: float | None = Field(None, ge=0)

    model_config = ConfigDict(from_attributes=True)
