import sys
from pathlib import Path

LIBRARY_ROOT = Path(__file__).resolve().parent
if str(LIBRARY_ROOT) not in sys.path:
    sys.path.insert(0, str(LIBRARY_ROOT))

from app import create_app
from app.config.settings import settings

app = create_app()

if __name__ == "__main__":
    app.run(
        host=settings.host,
        port=settings.port,
        debug=settings.debug,
        use_reloader=False,
        load_dotenv=False,
    )
