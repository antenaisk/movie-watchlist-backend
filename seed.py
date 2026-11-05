import json
from sqlmodel import SQLModel, Session, create_engine, select
from models import Movie

DATABASE_URL = "sqlite:///./watchlist.db"
engine = create_engine(DATABASE_URL, echo=False)

def init_db_and_seed():
    print("Initializing database tables...")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        existing_movies = session.exec(select(Movie)).first()
        if existing_movies:
            print("Database already contains movie data!")
            return

        print("Reading movies.json...")
        with open("movies.json", "r") as file:
            movies_data = json.load(file)

        print(f"Found {len(movies_data)} movies. Inserting into database...")
        for item in movies_data:
            movie = Movie(
                id=item.get("id"),
                title=item.get("title", "Untitled"),
                genre=item.get("genre") or item.get("category") or "General",
                synopsis=item.get("synopsis") or item.get("description") or "No description provided.",
                release_year=item.get("releaseYear") or item.get("year") or 2024,
                poster_url=item.get("posterUrl") or item.get("poster") or item.get("image")
            )
            session.add(movie)
        
        session.commit()
        print("Successfully seeded movies into SQLite database!")

if __name__ == "__main__":
    init_db_and_seed()