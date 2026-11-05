import os
import json
import random
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select
from google import genai
from google.genai import types

from database import get_session
from models import User, Movie, Watchlist, Review
from auth import hash_password, verify_password, create_access_token, get_current_user_id

load_dotenv()

app = FastAPI(title="GDGoC Movie Watchlist API")

# Enable CORS for Companion Frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- REQUEST SCHEMAS -----------------

class RegisterSchema(BaseModel):
    email: EmailStr
    password: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class AddWatchlistSchema(BaseModel):
    movie_id: int

class AddReviewSchema(BaseModel):
    movie_id: int
    rating: int  # 1-5
    opinion: str

class RecommendSchema(BaseModel):
    prompt: str

# ----------------- HEALTH CHECK -----------------

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Movie Watchlist API is running!"}

# ----------------- AUTH ROUTES -----------------

@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterSchema, session: Session = Depends(get_session)):
    existing_user = session.exec(select(User).where(User.email == data.email)).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email is already registered")

    new_user = User(
        email=data.email,
        password_hash=hash_password(data.password)
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    token = create_access_token(new_user.id)
    return {"message": "User registered successfully", "token": token, "user": {"id": new_user.id, "email": new_user.email}}

@app.post("/api/auth/login")
def login(data: LoginSchema, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == data.email)).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user.id)
    return {"token": token, "user": {"id": user.id, "email": user.email}}

# ----------------- MOVIE ROUTES -----------------

@app.get("/api/movies")
def get_movies(shuffle: Optional[bool] = False, session: Session = Depends(get_session)):
    movies = session.exec(select(Movie)).all()
    movie_list = [movie.model_dump() for movie in movies]
    if shuffle:
        random.shuffle(movie_list)
    return movie_list

@app.get("/api/movies/{movie_id}")
def get_movie_detail(movie_id: int, session: Session = Depends(get_session)):
    movie = session.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie

# ----------------- WATCHLIST ROUTES (PROTECTED) -----------------

@app.get("/api/watchlist")
def get_watchlist(user_id: int = Depends(get_current_user_id), session: Session = Depends(get_session)):
    watchlists = session.exec(select(Watchlist).where(Watchlist.user_id == user_id)).all()
    result = []
    for item in watchlists:
        movie = session.get(Movie, item.movie_id)
        if movie:
            result.append({
                "id": item.id,
                "movie_id": movie.id,
                "title": movie.title,
                "genre": movie.genre,
                "poster_url": movie.poster_url,
                "created_at": item.created_at
            })
    return result

@app.post("/api/watchlist", status_code=status.HTTP_201_CREATED)
def add_to_watchlist(data: AddWatchlistSchema, user_id: int = Depends(get_current_user_id), session: Session = Depends(get_session)):
    movie = session.get(Movie, data.movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    existing = session.exec(select(Watchlist).where(Watchlist.user_id == user_id, Watchlist.movie_id == data.movie_id)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Movie is already in your watchlist")

    new_item = Watchlist(user_id=user_id, movie_id=data.movie_id)
    session.add(new_item)
    session.commit()
    session.refresh(new_item)
    return {"message": "Added to watchlist", "watchlist_item": new_item}

@app.delete("/api/watchlist/{movie_id}")
def remove_from_watchlist(movie_id: int, user_id: int = Depends(get_current_user_id), session: Session = Depends(get_session)):
    item = session.exec(select(Watchlist).where(Watchlist.user_id == user_id, Watchlist.movie_id == movie_id)).first()
    if not item:
        raise HTTPException(status_code=404, detail="Movie not found in your watchlist")

    session.delete(item)
    session.commit()
    return {"message": "Movie removed from watchlist"}

# ----------------- WATCHED & REVIEWS ROUTES (PROTECTED) -----------------

@app.get("/api/watched")
def get_watched_history(user_id: int = Depends(get_current_user_id), session: Session = Depends(get_session)):
    reviews = session.exec(select(Review).where(Review.user_id == user_id)).all()
    result = []
    for rev in reviews:
        movie = session.get(Movie, rev.movie_id)
        if movie:
            result.append({
                "id": rev.id,
                "movie_id": movie.id,
                "title": movie.title,
                "rating": rev.rating,
                "opinion": rev.opinion,
                "watched_at": rev.watched_at
            })
    return result

@app.post("/api/watched", status_code=status.HTTP_201_CREATED)
def log_watched_movie(data: AddReviewSchema, user_id: int = Depends(get_current_user_id), session: Session = Depends(get_session)):
    if data.rating < 1 or data.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    movie = session.get(Movie, data.movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    new_review = Review(
        user_id=user_id,
        movie_id=data.movie_id,
        rating=data.rating,
        opinion=data.opinion
    )
    session.add(new_review)
    session.commit()
    session.refresh(new_review)
    return {"message": "Logged as watched successfully", "review": new_review}

# ----------------- GEMINI AI RECOMMENDATION ROUTE -----------------

@app.post("/api/movies/recommend")
def recommend_movie(data: RecommendSchema, session: Session = Depends(get_session)):
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set in .env file")

    movies = session.exec(select(Movie)).all()
    if not movies:
        raise HTTPException(status_code=404, detail="No movies found in database")

    movie_catalog = [
        {
            "id": m.id,
            "title": m.title,
            "genre": m.genre,
            "synopsis": m.synopsis
        }
        for m in movies
    ]

    system_instruction = (
        "You are an expert movie recommendation engine. "
        "You MUST only recommend a movie from the provided LOCAL MOVIE CATALOG below. "
        "Do NOT recommend any movie outside of this catalog under any circumstances. "
        "Return your response ONLY as valid raw JSON with keys 'movie_id' (integer) and 'reasoning' (string).\n\n"
        f"LOCAL MOVIE CATALOG:\n{json.dumps(movie_catalog, indent=2)}"
    )

    try:
        client = genai.Client(api_key=gemini_key)

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=f"User mood / preference: '{data.prompt}'",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.3
            )
        )

        result = json.loads(response.text)
        recommended_movie_id = result.get("movie_id")
        reasoning = result.get("reasoning")

        recommended_movie = session.get(Movie, recommended_movie_id)
        if not recommended_movie:
            recommended_movie = movies[0]
            reasoning = "Recommended based on general popular preference."

        return {
            "movie": recommended_movie,
            "reasoning": reasoning
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recommendation: {str(e)}"
        )