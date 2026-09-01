import os
import shutil
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings, DEFAULT_DB_FILE

db_url = settings.get_database_url()

# If using a custom SQLite path, ensure directory and file initialization with fallback
if db_url.startswith("sqlite:///"):
    target_path = db_url.replace("sqlite:///", "")
    target_dir = os.path.dirname(target_path)
    try:
        if target_dir and not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
        if not os.path.exists(target_path) and os.path.exists(DEFAULT_DB_FILE) and target_path != DEFAULT_DB_FILE:
            shutil.copyfile(DEFAULT_DB_FILE, target_path)
    except Exception as e:
        # Fallback to bundled database file if custom path is read-only or inaccessible
        db_url = f"sqlite:///{DEFAULT_DB_FILE}"

connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

engine = create_engine(
    db_url,
    connect_args=connect_args,
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

