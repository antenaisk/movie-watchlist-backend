from sqlmodel import create_engine, Session, SQLModel

DATABASE_URL = "sqlite:///./watchlist.db"
engine = create_engine(DATABASE_URL, echo=False)

def get_session():
    with Session(engine) as session:
        yield session