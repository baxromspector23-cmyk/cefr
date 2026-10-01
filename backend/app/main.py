from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import engine
from .models import Base
from .routers import attendance, auth, centers, education, finance, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Faqat SQLite (lokal dev/test) uchun. PostgreSQL'da jadvallarni Alembic yaratadi: alembic upgrade head
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(engine)
    yield


app = FastAPI(title="English Platform API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(centers.router)
app.include_router(users.router)
app.include_router(education.router)
app.include_router(attendance.router)
app.include_router(finance.router)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}
