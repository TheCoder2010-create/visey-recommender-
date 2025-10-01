from __future__ import annotations
import os
from typing import Optional

class Settings:
    """Configuration for the Visey Recommendation Service.

    Reads from environment variables with safe defaults.
    """

    # WordPress API Configuration
    WP_BASE_URL: str = os.getenv("WP_BASE_URL", "")
    WP_AUTH_TYPE: str = os.getenv("WP_AUTH_TYPE", "none")  # none|basic|jwt|application_password
    WP_USERNAME: Optional[str] = os.getenv("WP_USERNAME")
    WP_PASSWORD: Optional[str] = os.getenv("WP_PASSWORD")
    WP_JWT_TOKEN: Optional[str] = os.getenv("WP_JWT_TOKEN")
    WP_APP_PASSWORD: Optional[str] = os.getenv("WP_APP_PASSWORD")  # WordPress Application Password
    WP_RATE_LIMIT: int = int(os.getenv("WP_RATE_LIMIT", "60"))  # Requests per minute
    WP_TIMEOUT: int = int(os.getenv("WP_TIMEOUT", "30"))  # Request timeout in seconds
    WP_BATCH_SIZE: int = int(os.getenv("WP_BATCH_SIZE", "100"))  # Default batch size for pagination
    WP_SYNC_INTERVAL: int = int(os.getenv("WP_SYNC_INTERVAL", "30"))  # Background sync interval in minutes
    WP_CACHE_FALLBACK: bool = os.getenv("WP_CACHE_FALLBACK", "true").lower() == "true"  # Use cache-first approach

    # Cache
    CACHE_BACKEND: str = os.getenv("CACHE_BACKEND", "auto")  # auto|redis|sqlite
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")

    # Service
    TOP_N: int = int(os.getenv("TOP_N", "10"))

    # Storage locations
    DATA_DIR: str = os.getenv("DATA_DIR", os.path.join(os.getcwd(), "data"))
    SQLITE_CACHE_PATH: str = os.getenv("SQLITE_CACHE_PATH", os.path.join(DATA_DIR, "cache.db"))
    SQLITE_FEEDBACK_PATH: str = os.getenv("SQLITE_FEEDBACK_PATH", os.path.join(DATA_DIR, "feedback.db"))

    # Recommendations
    CONTENT_WEIGHT: float = float(os.getenv("CONTENT_WEIGHT", "0.6"))
    COLLAB_WEIGHT: float = float(os.getenv("COLLAB_WEIGHT", "0.3"))
    POP_WEIGHT: float = float(os.getenv("POP_WEIGHT", "0.1"))
    EMB_WEIGHT: float = float(os.getenv("EMB_WEIGHT", "0.0"))  # set > 0 if embeddings installed

settings = Settings()

# Ensure data directory exists
os.makedirs(settings.DATA_DIR, exist_ok=True)
