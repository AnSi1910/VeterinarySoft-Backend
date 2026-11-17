import os

# Keep the application's default engine in memory during tests.
os.environ["VET_DATABASE_URL"] = "sqlite://"
os.environ["VET_SECRET_KEY"] = "test-secret-only-do-not-use-in-production-with-more-than-32-characters"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import User
from app.security import hash_password


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def foreign_keys(conn, _record):
        conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, expire_on_commit=False)

    def override_db():
        with TestingSession() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        test_client.test_session = TestingSession
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def owner(client):
    body = {"email": "owner@example.com", "full_name": "Власник тварини", "password": "Passphrase!123"}
    response = client.post("/api/auth/register", json=body)
    assert response.status_code == 201, response.text
    token = client.post("/api/auth/login", data={"username": body["email"], "password": body["password"]})
    assert token.status_code == 200, token.text
    return {"id": response.json()["id"], "headers": {"Authorization": f"Bearer {token.json()['access_token']}"}}


@pytest.fixture
def other_owner(client):
    body = {"email": "other@example.com", "full_name": "Інший власник", "password": "AnotherPass!99"}
    response = client.post("/api/auth/register", json=body)
    assert response.status_code == 201, response.text
    token = client.post("/api/auth/login", data={"username": body["email"], "password": body["password"]})
    assert token.status_code == 200
    return {"id": response.json()["id"], "headers": {"Authorization": f"Bearer {token.json()['access_token']}"}}


@pytest.fixture
def admin(client):
    with client.test_session() as db:
        db.add(User(email="admin@example.com", full_name="Адміністратор", password_hash=hash_password("AdminPass!123"), role="admin"))
        db.commit()
    login = client.post("/api/auth/login", data={"username": "admin@example.com", "password": "AdminPass!123"})
    assert login.status_code == 200
    return {"headers": {"Authorization": f"Bearer {login.json()['access_token']}"}}


@pytest.fixture
def pet(client, owner):
    response = client.post("/api/pets", json={"name": "Барсик", "species": "кіт", "breed": "домашній"}, headers=owner["headers"])
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def vet(client, admin):
    response = client.post("/api/veterinarians", json={"full_name": "Марія Петренко", "specialization": "Терапевт"}, headers=admin["headers"])
    assert response.status_code == 201, response.text
    return response.json()
