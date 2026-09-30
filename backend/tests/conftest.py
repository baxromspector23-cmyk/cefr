import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["APP_ENV"] = "test"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.main import app
from app.models import Base, Role, User
from app.security import hash_password
from app.services import ratelimit

SUPER_PHONE, SUPER_PASS = "+998900000000", "SuperSecret123"


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    with Session() as db:
        db.add(
            User(center_id=None, role=Role.super_admin, full_name="Owner",
                 phone=SUPER_PHONE, password_hash=hash_password(SUPER_PASS))
        )
        db.commit()

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    ratelimit._fails.clear()
    # lifespan create_all real engine'da ishlamasligi uchun kontekstsiz client
    yield TestClient(app)
    app.dependency_overrides.clear()


def login(client, phone, password, slug=None):
    r = client.post("/auth/login", json={"phone": phone, "password": password, "center_slug": slug})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def make_center(client, slug, phone, password="AdminPass123"):
    h = login(client, SUPER_PHONE, SUPER_PASS)
    r = client.post("/centers", headers=h, json={
        "name": f"Center {slug}", "slug": slug, "phone": phone,
        "admin_full_name": f"Admin {slug}", "admin_password": password,
    })
    assert r.status_code == 201, r.text
    return login(client, phone, password, slug)
