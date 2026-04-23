import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = PROJECT_ROOT / "backend"


def _load_env_file() -> None:
    """Load environment variables from .env if present."""
    env_candidates = [PROJECT_ROOT / ".env", BACKEND_ROOT / ".env"]
    for env_path in env_candidates:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _to_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _resolve_path(path_value: str, default_relative: str) -> Path:
    raw = path_value or default_relative
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


_load_env_file()


@dataclass(frozen=True)
class Settings:
    mongo_uri: str
    db_name: str
    jwt_secret: str
    library_api_base_url: str
    books_path: Path
    index_path: Path
    semantic_index_path: Path
    semantic_meta_path: Path
    semantic_page_map_path: Path
    semantic_model_name: str
    chunk_min_words: int
    chunk_max_words: int
    chunk_target_words: int
    semantic_top_k: int
    host: str
    port: int
    debug: bool
    tesseract_path: str
    process_clear_existing_data: bool


settings = Settings(
    mongo_uri=os.environ.get("MONGO_URI", "mongodb://localhost:27017/"),
    db_name=os.environ.get("DB_NAME", "book_search_system"),
    jwt_secret=os.environ.get("JWT_SECRET", "change-me"),
    library_api_base_url=os.environ.get("LIBRARY_API_BASE_URL", "http://127.0.0.1:5100"),
    books_path=_resolve_path(os.environ.get("BOOKS_PATH", ""), "backend/books"),
    index_path=_resolve_path(os.environ.get("INDEX_PATH", ""), "backend/data/search_index.pkl"),
    semantic_index_path=_resolve_path(os.environ.get("SEMANTIC_INDEX_PATH", ""), "backend/data/semantic.index"),
    semantic_meta_path=_resolve_path(os.environ.get("SEMANTIC_META_PATH", ""), "backend/data/semantic_meta.pkl"),
    semantic_page_map_path=_resolve_path(os.environ.get("SEMANTIC_PAGE_MAP_PATH", ""), "backend/data/semantic_page_map.pkl"),
    semantic_model_name=os.environ.get("SEMANTIC_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"),
    chunk_min_words=_to_int(os.environ.get("CHUNK_MIN_WORDS"), default=200),
    chunk_max_words=_to_int(os.environ.get("CHUNK_MAX_WORDS"), default=300),
    chunk_target_words=_to_int(os.environ.get("CHUNK_TARGET_WORDS"), default=250),
    semantic_top_k=_to_int(os.environ.get("SEMANTIC_TOP_K"), default=200),
    host=os.environ.get("SERVER_HOST", "0.0.0.0"),
    port=_to_int(os.environ.get("SERVER_PORT"), default=5000),
    debug=_to_bool(os.environ.get("SERVER_DEBUG"), default=True),
    tesseract_path=os.environ.get("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    process_clear_existing_data=_to_bool(os.environ.get("PROCESS_CLEAR_EXISTING_DATA"), default=False),
)
