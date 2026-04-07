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
    books_path: Path
    index_path: Path
    host: str
    port: int
    debug: bool
    tesseract_path: str
    process_clear_existing_data: bool


settings = Settings(
    mongo_uri=os.environ.get("MONGO_URI", "mongodb://localhost:27017/"),
    db_name=os.environ.get("DB_NAME", "book_search_system"),
    jwt_secret=os.environ.get("JWT_SECRET", "change-me"),
    books_path=_resolve_path(os.environ.get("BOOKS_PATH", ""), "backend/books"),
    index_path=_resolve_path(os.environ.get("INDEX_PATH", ""), "backend/data/search_index.pkl"),
    host=os.environ.get("SERVER_HOST", "0.0.0.0"),
    port=_to_int(os.environ.get("SERVER_PORT"), default=5000),
    debug=_to_bool(os.environ.get("SERVER_DEBUG"), default=True),
    tesseract_path=os.environ.get("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    process_clear_existing_data=_to_bool(os.environ.get("PROCESS_CLEAR_EXISTING_DATA"), default=False),
)
