import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", str(BASE_DIR / "generated_notes")))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LIBRARY_HISTORY_FILE = BASE_DIR / "library_history.json"

def validate_keys() -> tuple[bool, list[str]]:
    """Check if required API keys are populated."""
    missing = []
    if not OPENROUTER_API_KEY or "your_" in OPENROUTER_API_KEY:
        missing.append("OPENROUTER_API_KEY")
    if not SERPER_API_KEY or "your_" in SERPER_API_KEY:
        missing.append("SERPER_API_KEY")
    return len(missing) == 0, missing
