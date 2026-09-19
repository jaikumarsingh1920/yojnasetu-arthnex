import os
import shutil
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings, DEFAULT_DB_FILE

db_url = settings.get_database_url()
is_sqlite = db_url.startswith("sqlite")
is_postgres = db_url.startswith("postgresql") or db_url.startswith("postgres")

# If using a custom SQLite path, ensure directory and file initialization with fallback
if is_sqlite:
    target_path = db_url.replace("sqlite:///", "")
    target_dir = os.path.dirname(target_path)
    try:
        if target_dir and not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
        if not os.path.exists(target_path) and os.path.exists(DEFAULT_DB_FILE) and target_path != DEFAULT_DB_FILE:
            shutil.copyfile(DEFAULT_DB_FILE, target_path)
    except Exception as e:
        if os.environ.get("TESTING") == "true":
            raise RuntimeError(f"Failed to initialize isolated test database at {target_path}: {e}")
        db_url = f"sqlite:///{DEFAULT_DB_FILE}"

# Engine options based on dialect
engine_kwargs = {
    "echo": settings.DEBUG and getattr(settings, "DB_ECHO", False),
    "pool_pre_ping": True,
}

if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False, "timeout": 15}
elif is_postgres:
    engine_kwargs["poolclass"] = QueuePool
    engine_kwargs["pool_size"] = getattr(settings, "DB_POOL_SIZE", 20)
    engine_kwargs["max_overflow"] = getattr(settings, "DB_MAX_OVERFLOW", 10)
    engine_kwargs["pool_timeout"] = getattr(settings, "DB_POOL_TIMEOUT", 30)
    engine_kwargs["pool_recycle"] = getattr(settings, "DB_POOL_RECYCLE", 1800)

engine = create_engine(db_url, **engine_kwargs)


@event.listens_for(engine, "connect")
def configure_dbapi_connection(dbapi_connection, connection_record):
    """
    Applies performance and integrity PRAGMAs for SQLite connections.
    Enforces foreign keys, WAL mode, memory cache, and lock timeout.
    """
    if is_sqlite:
        cursor = dbapi_connection.cursor()
        try:
            if getattr(settings, "SQLITE_ENABLE_FOREIGN_KEYS", False):
                cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.execute("PRAGMA cache_size=-64000;")  # 64MB cache
            cursor.execute("PRAGMA busy_timeout=10000;")  # 10s busy wait
        except Exception:
            pass
        finally:
            cursor.close()


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

