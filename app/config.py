import os
import secrets
import logging
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data")).resolve()
VECTORSTORE_DIR = Path(os.getenv("VECTORSTORE_DIR", BASE_DIR / "vectorstore")).resolve()

DEFAULT_DATABASE_URL = f"sqlite:///{(DATA_DIR / 'users.db').as_posix()}"


def _get_int_env(name: str, default: int, minimum: int | None = None, maximum: int | None = None) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        logger.warning("Invalid integer for %s=%r; using default %s.", name, raw_value, default)
        return default
    if minimum is not None and value < minimum:
        logger.warning("%s=%s is below minimum %s; using default %s.", name, value, minimum, default)
        return default
    if maximum is not None and value > maximum:
        logger.warning("%s=%s is above maximum %s; using default %s.", name, value, maximum, default)
        return default
    return value


def _normalize_origins(raw_value: str | None, environment: str) -> list[str]:
    if not raw_value:
        if environment.lower() == "production":
            logger.warning("CORS_ORIGINS is not set in production; browser clients will be blocked until explicit origins are configured.")
            return []
        return ["*"]
    origins = [origin.strip() for origin in raw_value.split(",") if origin.strip()]
    if environment.lower() == "production" and "*" in origins:
        logger.warning("Wildcard CORS_ORIGINS is not allowed in production; configure explicit frontend origins.")
        return [origin for origin in origins if origin != "*"]
    return origins


@lru_cache(maxsize=1)
def get_settings() -> dict[str, object]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

    environment = os.getenv("ENVIRONMENT", "development")
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        if environment.lower() == "production":
            raise RuntimeError("SECRET_KEY must be set when ENVIRONMENT=production.")
        secret_key = secrets.token_urlsafe(32)
    database_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    if environment.lower() == "production" and database_url.startswith("sqlite"):
        logger.warning("SQLite DATABASE_URL is configured in production; user data may not be durable on ephemeral services.")

    return {
        "app_name": os.getenv("APP_NAME", "CloudSec RAG Agent"),
        "environment": environment,
        "database_url": database_url,
        "secret_key": secret_key,
        "access_token_expire_minutes": _get_int_env("ACCESS_TOKEN_EXPIRE_MINUTES", 1440, minimum=1),
        "llm_provider": os.getenv("LLM_PROVIDER", "gemini").strip().lower(),
        "openai_api_key": os.getenv("OPENAI_API_KEY", "").strip(),
        "openai_base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        "openai_max_output_tokens": _get_int_env("OPENAI_MAX_OUTPUT_TOKENS", 400, minimum=1, maximum=8192),
        "gemini_api_key": os.getenv("GEMINI_API_KEY", "").strip(),
        "gemini_base_url": os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta").rstrip("/"),
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        "gemini_max_output_tokens": _get_int_env("GEMINI_MAX_OUTPUT_TOKENS", 800, minimum=1, maximum=8192),
        "ollama_url": os.getenv("OLLAMA_URL", "").strip(),
        "ollama_model": os.getenv("OLLAMA_MODEL", "phi3:mini"),
        "ollama_num_predict": _get_int_env("OLLAMA_NUM_PREDICT", 192, minimum=1, maximum=8192),
        "request_timeout_seconds": _get_int_env("REQUEST_TIMEOUT_SECONDS", 45, minimum=1, maximum=180),
        "backend_url": os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/"),
        "api_base_url": os.getenv("CLOUDSEC_API_URL", os.getenv("BACKEND_URL", "http://127.0.0.1:8000")).rstrip("/"),
        "port": _get_int_env("PORT", 8000, minimum=1, maximum=65535),
        "host": os.getenv("HOST", "0.0.0.0"),
        "cors_origins": _normalize_origins(os.getenv("CORS_ORIGINS"), environment),
        "max_query_chars": _get_int_env("MAX_QUERY_CHARS", 4000, minimum=1),
        "max_attachment_chars": _get_int_env("MAX_ATTACHMENT_CHARS", 12000, minimum=1),
        "max_attachment_count": _get_int_env("MAX_ATTACHMENT_COUNT", 5, minimum=0),
        "max_concurrent_ask_requests": _get_int_env("MAX_CONCURRENT_ASK_REQUESTS", 4, minimum=1, maximum=100),
        "data_dir": DATA_DIR,
        "vectorstore_dir": VECTORSTORE_DIR,
    }
