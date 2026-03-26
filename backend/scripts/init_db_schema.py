import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.models import ensure_schema_indexes, inspect_collections
from backend.app.config.settings import settings


if __name__ == "__main__":
    print(f"Using database: {settings.db_name}")
    ensure_schema_indexes()
    summary = inspect_collections()
    for name, details in sorted(summary.items()):
        print(f"{name}: count={details['count']}, indexes={details['indexes']}")
