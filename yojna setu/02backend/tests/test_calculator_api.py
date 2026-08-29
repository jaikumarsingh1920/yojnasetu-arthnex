import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(os.path.dirname(BACKEND_DIR), "04data")
SCRIPT_DIR = os.path.join(DATA_DIR, "scripts")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from app.main import app
from app.models import Base
from app.db.session import get_db
from seed_db import seed_database


@pytest.fixture(scope="module")
def calc_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSessionLocal()
    seed_database(session)
    session.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_calculator_api_endpoint(calc_client):
    payload = {
        "scheme_id": "SIH26092-052",
        "project_cost": 100000.0,
        "requested_loan_amount": 90000.0,
        "repayment_period_months": 36
    }
    response = calc_client.post("/api/v1/calculator/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["scheme_id"] == "SIH26092-052"
    assert data["status"] in ("CALCULATED", "SUCCESS", "PARTIAL")
    assert "resolved_parameters" in data
