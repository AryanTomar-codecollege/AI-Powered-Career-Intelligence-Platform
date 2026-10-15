from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import Base, engine
from app import models  # noqa: F401 - registers SQLAlchemy models
from app.routers import profiles, resumes

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    description="Phase 1: Supabase authentication integration, user profiles, and NLP resume parsing.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "app": settings.app_name}


app.include_router(profiles.router)
app.include_router(resumes.router)
