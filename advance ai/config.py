import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CONFIG_FILE = DATA_DIR / "config.json"
DB_FILE = DATA_DIR / "nexus_memory.db"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_CONFIG = {
    "active_provider": os.getenv("ACTIVE_PROVIDER", "local"),  # "local", "gemini", "openai", "groq", "ollama"
    "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "groq_api_key": os.getenv("GROQ_API_KEY", ""),
    "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    "groq_model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
    "ollama_model": os.getenv("OLLAMA_MODEL", "llama3"),
    "temperature": float(os.getenv("TEMPERATURE", "0.7")),
    "system_persona": (
        "You are Nexus-AI, an advanced autonomous AI assistant. "
        "You have access to tools including Python code execution, live web search, "
        "file workspace operations, and exact mathematical calculation. "
        "Always be helpful, precise, analytical, and structured in your explanations."
    ),
    "enabled_tools": ["code_runner", "web_search", "file_manager", "calculator", "system_info", "weather_info", "datetime_info"]
}


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
        except Exception:
            pass
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = DEFAULT_CONFIG.copy()
            merged.update(data)
            for k in ["gemini_api_key", "openai_api_key", "groq_api_key"]:
                env_val = os.getenv(k.upper(), "")
                if env_val and not merged.get(k):
                    merged[k] = env_val
            return merged
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(new_config: dict) -> dict:
    current = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                current.update(json.load(f))
        except Exception:
            pass
    current.update(new_config)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)
    return current

