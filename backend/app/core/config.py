import os
from pathlib import Path
from dotenv import load_dotenv

# Root project paths
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BACKEND_DIR.parent / ".env", override=False)
DATA_DIR = Path(os.getenv("KRITAM_DATA_DIR", str(BACKEND_DIR / "data"))).expanduser()
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_DB_PATH = DATA_DIR / "kritam.db"

class Settings:
    """Application settings with environment variable overrides."""
    PROJECT_NAME: str = "KRITAM AI"
    VERSION: str = "1.0.0"
    HOST: str = os.getenv("KRITAM_BACKEND_HOST", "127.0.0.1")
    PORT: int = int(os.getenv("KRITAM_BACKEND_PORT", "8765"))
    ENVIRONMENT: str = os.getenv("KRITAM_ENV", "development")
    
    # Security handshake token
    AUTH_TOKEN: str = os.getenv("KRITAM_AUTH_TOKEN", "")
    
    # SQLite Database URI
    DATABASE_URL: str = os.getenv("KRITAM_DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")
    
    # Default AI settings
    DEFAULT_PROVIDER: str = os.getenv("DEFAULT_AI_PROVIDER", "offline")
    KRITAM_GATEWAY_URL: str = os.getenv("KRITAM_GATEWAY_URL", "https://api.kritam.ai").rstrip("/")
    KRITAM_GATEWAY_ENABLED: bool = os.getenv("KRITAM_GATEWAY_ENABLED", "true").lower() in ("true", "1", "yes")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:latest")
    
    # Cloud AI keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    DEFAULT_CLOUD_MODEL: str = os.getenv("DEFAULT_CLOUD_MODEL", "gpt-4o-mini")

settings = Settings()
