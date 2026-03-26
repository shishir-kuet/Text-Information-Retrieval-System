from backend.app.config.database import get_database, get_mongo_client
from backend.app.config.paths import BOOKS_DIR, DATA_DIR, SEARCH_INDEX_FILE
from backend.app.config.settings import settings

__all__ = [
    "BOOKS_DIR",
    "DATA_DIR",
    "SEARCH_INDEX_FILE",
    "get_database",
    "get_mongo_client",
    "settings",
]
