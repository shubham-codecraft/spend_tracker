import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")

from app.main import app  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app import otp as otp_service  # noqa: E402

TEST_DB_URL = "sqlite:///:memory:"

# StaticPool keeps a single underlying connection alive for the whole
# engine, which is required for SQLite ":memory:" - otherwise every new
# connection gets its own throwaway in-memory database and tables
# "disappear" between operations.
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def otp_sender(monkeypatch):
    captured = {}

    def capture_otp(**kwargs):
        captured["otp"] = kwargs["otp"]

    monkeypatch.setattr(otp_service, "send_otp_email", capture_otp)
    return captured


@pytest.fixture()
def auth_headers(client, otp_sender):
    response = client.post(
        "/auth/request-otp",
        json={
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
        },
    )
    assert response.status_code == 202
    response = client.post(
        "/auth/verify-otp",
        json={"email": "test@example.com", "otp": otp_sender["otp"]},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
