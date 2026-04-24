import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LIBRARY_ROOT = PROJECT_ROOT / "backend-library"


def _load_env_file() -> None:
    env_candidates = [PROJECT_ROOT / ".env", LIBRARY_ROOT / ".env"]
    for env_path in env_candidates:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


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
    books_path: Path
    data_path: Path
    host: str
    port: int
    debug: bool
    tesseract_path: str
    jwt_secret: str


settings = Settings(
    mongo_uri=os.environ.get("MONGO_URI", "mongodb://localhost:27017/"),
    db_name=os.environ.get("LIBRARY_DB_NAME", "library_system"),
    books_path=_resolve_path(os.environ.get("LIBRARY_BOOKS_PATH", ""), "backend-library/books"),
    data_path=_resolve_path(os.environ.get("LIBRARY_DATA_PATH", ""), "backend-library/data"),
    host=os.environ.get("LIBRARY_SERVER_HOST", "0.0.0.0"),
    port=_to_int(os.environ.get("LIBRARY_SERVER_PORT"), default=5100),
    debug=_to_bool(os.environ.get("LIBRARY_SERVER_DEBUG"), default=True),
    tesseract_path=os.environ.get("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    jwt_secret=os.environ.get("JWT_SECRET", "change-me"),
)
