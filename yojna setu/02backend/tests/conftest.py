import os
import shutil
import tempfile
import uuid
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# 1. Establish dedicated isolated test database in tempdir
_test_dir = tempfile.mkdtemp(prefix="yojnasetu_test_session_")
_test_db_path = os.path.join(_test_dir, "test_yojnasetu.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db_path}"
os.environ["TESTING"] = "true"

# 2. Locate persistent development database and seed isolated test copy
from app.core.config import DEFAULT_DB_FILE, settings

if os.path.exists(DEFAULT_DB_FILE):
    shutil.copyfile(DEFAULT_DB_FILE, _test_db_path)
    for suffix in ["-wal", "-shm"]:
        src_suffix = f"{DEFAULT_DB_FILE}{suffix}"
        if os.path.exists(src_suffix):
            try:
                shutil.copyfile(src_suffix, f"{_test_db_path}{suffix}")
            except Exception:
                pass

settings.DATABASE_URL = f"sqlite:///{_test_db_path}"

# 3. Configure app.db.session engine and SessionLocal to use isolated test DB
import app.db.session as app_session

if hasattr(app_session, "engine") and app_session.engine is not None:
    try:
        app_session.engine.dispose()
    except Exception:
        pass

app_session.db_url = f"sqlite:///{_test_db_path}"
app_session.is_sqlite = True
app_session.is_postgres = False
app_session.engine = create_engine(
    app_session.db_url,
    connect_args={"check_same_thread": False, "timeout": 15},
    pool_pre_ping=True,
    echo=False
)
if hasattr(app_session, "configure_dbapi_connection"):
    event.listen(app_session.engine, "connect", app_session.configure_dbapi_connection)

app_session.SessionLocal.configure(bind=app_session.engine)


@pytest.fixture(scope="session", autouse=True)
def test_db_session_isolation():
    """
    Session-scoped fixture guaranteeing zero mutation to the persistent development database.
    All tests execute against the isolated copy. Teardown disposes the engine and removes the temp file.
    """
    yield _test_db_path

    # Teardown
    try:
        app_session.engine.dispose()
    except Exception:
        pass

    for suffix in ["", "-wal", "-shm"]:
        target = f"{_test_db_path}{suffix}"
        if os.path.exists(target):
            try:
                os.remove(target)
            except Exception:
                pass

    try:
        shutil.rmtree(_test_dir, ignore_errors=True)
    except Exception:
        pass
