import sys
from pathlib import Path

# Ensure project root is on sys.path so `backend.*` imports work
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import create_app
from backend.app.config.settings import settings
    
app = create_app()

if __name__ == "__main__":
    # On Windows, Werkzeug's debug reloader can occasionally throw WinError 10038.
    # Keep debug=True for better tracebacks, but disable reloader and dotenv loading
    # to avoid noisy socket/dotenv tips.
    app.run(
        host=settings.host,
        port=settings.port,
        debug=settings.debug,
        use_reloader=False,
        load_dotenv=False,
    )
