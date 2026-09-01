import os
import shutil
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings, DEFAULT_DB_FILE

db_url = settings.get_database_url()

# If using a custom SQLite path (e.g. Render Persistent Disk at /data/yojnasetu.db)
if db_url.startswith("sqlite:///"):
    target_path = db_url.replace("sqlite:///", "")
    target_dir = os.path.dirname(target_path)
    if target_dir and not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir, exist_ok=True)
        except Exception:
            pass
    # If the target DB does not exist yet, copy initial canonical database
    if not os.path.exists(target_path) and os.path.exists(DEFAULT_DB_FILE) and target_path != DEFAULT_DB_FILE:
        try:
            shutil.copyfile(DEFAULT_DB_FILE, target_path)
        except Exception:
            pass

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

