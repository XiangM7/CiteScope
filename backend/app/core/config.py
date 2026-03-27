from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env", override=False)


@dataclass
class Settings:
    app_name: str = "CiteScope API"
    api_prefix: str = ""
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            f"sqlite:///{(BACKEND_DIR / 'data' / 'citescope.db').as_posix()}",
        )
    )
    uploads_dir: Path = field(
        default_factory=lambda: Path(os.getenv("UPLOADS_DIR", BACKEND_DIR / "data" / "uploads"))
    )
    chroma_dir: Path = field(
        default_factory=lambda: Path(os.getenv("CHROMA_DIR", BACKEND_DIR / "data" / "chroma"))
    )
    cors_origins: list[str] = field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
            if origin.strip()
        ]
    )
    chunk_size_chars: int = int(os.getenv("CHUNK_SIZE_CHARS", "900"))
    chunk_overlap_chars: int = int(os.getenv("CHUNK_OVERLAP_CHARS", "150"))
    retrieval_top_k: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))
    request_timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "45"))
    hashing_dimensions: int = int(os.getenv("HASHING_DIMENSIONS", "1024"))

    llm_provider: str = os.getenv("LLM_PROVIDER", "local")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "")

    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "local")
    embedding_base_url: str = os.getenv("EMBEDDING_BASE_URL", "https://api.openai.com/v1")
    embedding_api_key: str = os.getenv("EMBEDDING_API_KEY", "")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "")

    def ensure_directories(self) -> None:
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
