from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.models import Chunk, Document, EvalCase, EvalResult, QueryLog
from app.routers import chat, documents, eval


Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=settings.uploads_dir), name="uploads")

app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(eval.router)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
