from backend.app.config.settings import BACKEND_ROOT, settings

BOOKS_DIR = settings.books_path
DATA_DIR = BACKEND_ROOT / "data"
SEARCH_INDEX_FILE = settings.index_path
SEMANTIC_INDEX_FILE = settings.semantic_index_path
SEMANTIC_META_FILE = settings.semantic_meta_path
SEMANTIC_PAGE_MAP_FILE = settings.semantic_page_map_path
