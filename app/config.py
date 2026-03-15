from pathlib import Path

APP_NAME = "Novel Downloader 2.0"
APP_GEOMETRY = "1380x900"
APP_MIN_SIZE = (1180, 760)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = DATA_DIR / "database"
EXPORT_DIR = BASE_DIR / "Novels"
ASSETS_DIR = BASE_DIR / "assets"
IMAGE_DIR = DATA_DIR / "images"
LOG_DIR = DATA_DIR / "logs"

PLACEHOLDER_IMAGE = str(ASSETS_DIR / "placeholder.png")
ICON_PATH = str(ASSETS_DIR / "icon.png")
LOADER_GIF = str(ASSETS_DIR / "loader.gif")

DEFAULT_TIMEOUT = 15
DEFAULT_RESTART_EVERY_PAGES = 300
DEFAULT_MAX_EXPORT_CHAPTERS = 300
DEFAULT_LOAD_DELAY = 1.0

for path in [DATA_DIR, DB_DIR, EXPORT_DIR, IMAGE_DIR, LOG_DIR]:
    path.mkdir(parents=True, exist_ok=True)
