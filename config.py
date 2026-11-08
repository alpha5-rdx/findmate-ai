"""Central configuration for FindMate AI."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
DB_PATH = DATA_DIR / "findmate.db"

APP_NAME = "FindMate AI"
APP_TAGLINE = "Intelligent Lost & Found Matching"

# --- AI / matching -------------------------------------------------------
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Matches below this *semantic* similarity are never stored or shown,
# regardless of category/location. Keeps metadata from rescuing unrelated items.
MIN_SEMANTIC_SIMILARITY = 0.30
DEFAULT_THRESHOLD = 0.60          # default user-configurable display threshold
HIGH_CONFIDENCE = 0.75
MEDIUM_CONFIDENCE = 0.60

# Metadata bonuses are small, additive, and bounded (see ai/matcher.py).
CATEGORY_BONUS = 0.05
LOCATION_BONUS = 0.04

# --- Validation ----------------------------------------------------------
CATEGORIES = [
    "Electronics", "Wallets & Bags", "Keys", "Clothing & Accessories",
    "Documents & Cards", "Jewelry", "Pets", "Books & Stationery",
    "Sports & Toys", "Other",
]
MAX_NAME_LEN = 80
MAX_DESC_LEN = 1000
MAX_LOCATION_LEN = 120
MIN_DESC_LEN = 10
ALLOWED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}
MAX_IMAGE_MB = 5

# --- Admin ---------------------------------------------------------------
# Override with the FINDMATE_ADMIN_PASSWORD environment variable.
ADMIN_PASSWORD = os.environ.get("FINDMATE_ADMIN_PASSWORD", "admin123")
