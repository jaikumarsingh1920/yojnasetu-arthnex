from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

engine = create_engine(
    settings.get_database_url(),
    pool_pre_ping=True,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency generator for SQLAlchemy database sessions.
    Provides connection per request and handles session cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
