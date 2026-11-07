import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent      # backend/
load_dotenv(ROOT / ".env")

@dataclass(frozen=True)
class Settings:
    provider: str = os.getenv("LLM_PROVIDER", "gemini")
    model: str = os.getenv("LLM_MODEL", "")
    api_key: str = os.getenv("LLM_API_KEY", "")
    allowed_origins: tuple = tuple(os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","))
    allow_draft: bool = os.getenv("ALLOW_DRAFT", "true").lower() == "true"   # False = VERIFIED items only
    rate_limit_per_min: int = int(os.getenv("RATE_LIMIT_PER_MIN", "20"))
    library_dir: Path = ROOT / "library"
    playbooks_dir: Path = ROOT / "playbooks"

settings = Settings()
