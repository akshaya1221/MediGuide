import os
import tempfile
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_mediguide.db"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["STORAGE_PATH"] = tempfile.mkdtemp(prefix="mediguide-tests-")

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    yield TestClient(app)


@pytest.fixture
def auth_headers(client: TestClient):
    response = client.post("/api/v1/auth/register", json={"full_name": "Test Patient", "email": "patient@example.com", "password": "strong-pass-123"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

