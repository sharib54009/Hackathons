import os


class Config:
    """Application settings shared by development and future environments."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DEBUG = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "saferoute.db"))
    CORS_ORIGINS = tuple(
        origin.strip()
        for origin in os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174").split(",")
        if origin.strip()
    )
    HIGH_RISK = int(os.environ.get("HIGH_RISK", "75"))
    SIMULATION_STEP_SECONDS = float(os.environ.get("SIMULATION_STEP_SECONDS", "2.5"))
    LOCAL_API_BASE_URL = os.environ.get("LOCAL_API_BASE_URL", "http://127.0.0.1:5000")
