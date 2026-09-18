import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.core.security import create_access_token
from app.db.base_class import Base
from app.db.session import get_db
from app.models.user import User, UserRole


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add_all([
        User(user_id="blog-admin", email="admin@blogs.test", full_name="Blog Admin", role=UserRole.SYSTEM_ADMIN, is_active=True),
        User(user_id="blog-user", email="user@blogs.test", role=UserRole.BENEFICIARY, is_active=True),
    ])
    session.commit()
    app.dependency_overrides[get_db] = lambda: iter([session])
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    session.close()


def headers(user_id, role):
    return {"Authorization": f"Bearer {create_access_token(user_id=user_id, role=role)}"}


def test_public_blog_read_and_admin_only_crud(client):
    data = {"title": "Understanding your EMI", "summary": "A concise guide to EMI and repayment planning.", "content": "Learn how principal, interest and tenure affect every monthly payment."}
    assert client.get("/api/v1/blogs").status_code == 200
    assert client.post("/api/v1/admin/blogs", json=data).status_code == 401
    assert client.post("/api/v1/admin/blogs", json=data, headers=headers("blog-user", "BENEFICIARY")).status_code == 403

    created = client.post("/api/v1/admin/blogs", json=data, headers=headers("blog-admin", "SYSTEM_ADMIN"))
    assert created.status_code == 201
    blog = created.json()
    assert blog["author_name"] == "Blog Admin"
    assert client.get("/api/v1/blogs").json()[0]["title"] == data["title"]

    data["title"] = "Planning your EMI"
    assert client.put(f"/api/v1/admin/blogs/{blog['blog_id']}", json=data, headers=headers("blog-admin", "SYSTEM_ADMIN")).status_code == 200
    assert client.delete(f"/api/v1/admin/blogs/{blog['blog_id']}", headers=headers("blog-admin", "SYSTEM_ADMIN")).status_code == 204
