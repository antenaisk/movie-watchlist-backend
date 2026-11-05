from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str

    watchlists: List["Watchlist"] = Relationship(back_populates="user")
    reviews: List["Review"] = Relationship(back_populates="user")

class Movie(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    genre: Optional[str] = "Unknown"
    synopsis: Optional[str] = "No description available."
    release_year: Optional[int] = 2024
    poster_url: Optional[str] = None

    watchlists: List["Watchlist"] = Relationship(back_populates="movie")
    reviews: List["Review"] = Relationship(back_populates="movie")

class Watchlist(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    movie_id: int = Field(foreign_key="movie.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="watchlists")
    movie: Optional[Movie] = Relationship(back_populates="watchlists")

class Review(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    movie_id: int = Field(foreign_key="movie.id")
    rating: int  # 1 to 5 stars
    opinion: str
    watched_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="reviews")
    movie: Optional[Movie] = Relationship(back_populates="reviews")