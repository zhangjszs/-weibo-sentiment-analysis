import os
from urllib.parse import urlparse

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def _parse_csv_env(name: str) -> list[str]:
    raw = os.getenv(name, "")
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _parse_bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _get_secret_key() -> str | None:
    value = os.getenv("SECRET_KEY")
    if value:
        return value
    env = os.getenv("FLASK_ENV", "development")
    if env != "production":
        return os.urandom(32).hex()
    return None


def _parse_redis_url(url: str) -> dict[str, str | int]:
    parsed = urlparse(url)
    db_raw = (parsed.path or "/0").lstrip("/") or "0"
    try:
        db = int(db_raw)
    except ValueError:
        db = 0
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 6379,
        "db": db,
        "password": parsed.password or "",
    }


class Config:
    # Flask Settings
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    SECRET_KEY = _get_secret_key()
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    IS_DEVELOPMENT = FLASK_ENV == "development"

    ALLOWED_ORIGINS = _parse_csv_env("ALLOWED_ORIGINS") or (
        ["http://localhost:3000", "http://127.0.0.1:3000"] if IS_DEVELOPMENT else []
    )
    ADMIN_USERS = set(_parse_csv_env("ADMIN_USERS"))
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or SECRET_KEY
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 24))
    AUTH_COOKIE_NAME = os.getenv("AUTH_COOKIE_NAME", "weibo_access_token")

    # Database Settings
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
    DB_NAME = os.getenv("DB_NAME", "weibo_analysis")
    DB_CHARSET = "utf8mb4"

    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 10))
    DB_POOL_RECYCLE = 3600
    DB_POOL_TIMEOUT = 30

    @classmethod
    def get_database_url(cls):
        return f"mysql+pymysql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}?charset={cls.DB_CHARSET}"

    @classmethod
    def get_redis_connection_params(cls) -> dict:
        return {
            "host": cls.REDIS_HOST,
            "port": cls.REDIS_PORT,
            "db": cls.REDIS_DB,
            "password": cls.REDIS_PASSWORD if cls.REDIS_PASSWORD else None,
            "decode_responses": True,
        }

    # Redis / Celery Settings
    REDIS_URL = (
        os.getenv("REDIS_URL")
        or os.getenv("CELERY_BROKER_URL")
        or "redis://localhost:6379/0"
    )
    _REDIS_PARSED = _parse_redis_url(REDIS_URL)
    REDIS_HOST = os.getenv("REDIS_HOST", str(_REDIS_PARSED["host"]))
    REDIS_PORT = int(os.getenv("REDIS_PORT", str(_REDIS_PARSED["port"])))
    REDIS_DB = int(os.getenv("REDIS_DB", str(_REDIS_PARSED["db"])))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", str(_REDIS_PARSED["password"]))

    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

    # LLM Settings
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_API_URL = os.getenv("LLM_API_URL", "https://api.deepseek.com/v1/chat/completions")
    LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", 30))
    LLM_CACHE_TTL = int(os.getenv("LLM_CACHE_TTL", 3600))

    # Spider Settings
    WEIBO_COOKIE = os.getenv("WEIBO_COOKIE", "")
    WEIBO_USER_AGENT = os.getenv(
        "WEIBO_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    )
    SPIDER_TIMEOUT = int(os.getenv("SPIDER_TIMEOUT", 45))
    SPIDER_DELAY = float(os.getenv("SPIDER_DELAY", 15))
    SPIDER_RETRIES = int(
        os.getenv("SPIDER_MAX_RETRIES", 3)
    )  # env var: SPIDER_MAX_RETRIES
    SPIDER_USE_PROXY = os.getenv("SPIDER_USE_PROXY", "True").lower() == "true"
    SPIDER_SERVICE_ENABLED = (
        os.getenv("SPIDER_SERVICE_ENABLED", "False").lower() == "true"
    )
    SPIDER_SERVICE_BASE_URL = os.getenv(
        "SPIDER_SERVICE_BASE_URL", "http://localhost:8090"
    ).rstrip("/")
    SPIDER_SERVICE_TIMEOUT = int(os.getenv("SPIDER_SERVICE_TIMEOUT", 15))
    SPIDER_SERVICE_TOKEN = os.getenv("SPIDER_SERVICE_TOKEN", "")
    SPIDER_SERVICE_FALLBACK_LOCAL = (
        os.getenv("SPIDER_SERVICE_FALLBACK_LOCAL", "True").lower() == "true"
    )

    NLP_SERVICE_ENABLED = os.getenv("NLP_SERVICE_ENABLED", "False").lower() == "true"
    NLP_SERVICE_BASE_URL = os.getenv(
        "NLP_SERVICE_BASE_URL", "http://localhost:8091"
    ).rstrip("/")
    NLP_SERVICE_TIMEOUT = int(os.getenv("NLP_SERVICE_TIMEOUT", 20))
    NLP_SERVICE_TOKEN = os.getenv("NLP_SERVICE_TOKEN", "")
    NLP_SERVICE_FALLBACK_LOCAL = (
        os.getenv("NLP_SERVICE_FALLBACK_LOCAL", "True").lower() == "true"
    )

    # Path Settings
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    DATA_DIR = os.path.join(BASE_DIR, "data")
    STATIC_DIR = os.path.join(BASE_DIR, "static")
    CACHE_DIR = os.path.join(BASE_DIR, "cache")
    MODEL_DIR = os.path.join(BASE_DIR, "model")
    SPIDER_DIR = os.path.join(BASE_DIR, "spider")

    # App Settings
    JSON_AS_ASCII = False
    SEND_FILE_MAX_AGE_DEFAULT = 0 if IS_DEVELOPMENT else 43200
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    PERMANENT_SESSION_LIFETIME = 86400 * 7  # 7 days

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Demo / Bootstrap
    DEMO_ADMIN_USERNAME = os.getenv("DEMO_ADMIN_USERNAME", "admin")
    DEMO_ADMIN_PASSWORD = os.getenv("DEMO_ADMIN_PASSWORD", "Admin123!")
    AUTO_CREATE_DEMO_ADMIN = _parse_bool_env(
        "AUTO_CREATE_DEMO_ADMIN", default=False
    )
    DEMO_ADMIN_RESET_PASSWORD = _parse_bool_env(
        "DEMO_ADMIN_RESET_PASSWORD", default=False
    )
    ENABLE_STARTUP_WARMUP = _parse_bool_env(
        "ENABLE_STARTUP_WARMUP", default=IS_DEVELOPMENT
    )
    STARTUP_WARMUP_DELAY = float(os.getenv("STARTUP_WARMUP_DELAY", "0.5"))

    @classmethod
    def validate(cls) -> None:
        if cls.FLASK_ENV == "production":
            if not cls.SECRET_KEY:
                raise RuntimeError("SECRET_KEY must be set in production")
            if not cls.JWT_SECRET_KEY:
                raise RuntimeError(
                    "JWT_SECRET_KEY must be set in production (or reuse SECRET_KEY)"
                )
            if not cls.ALLOWED_ORIGINS:
                raise RuntimeError("ALLOWED_ORIGINS must be set in production")
            if not cls.ADMIN_USERS:
                raise RuntimeError("ADMIN_USERS must be set in production")


# Late binding for properties that depend on class variables
Config.SQLALCHEMY_DATABASE_URI = Config.get_database_url()
Config.SQLALCHEMY_TRACK_MODIFICATIONS = False
Config.SQLALCHEMY_ECHO = Config.IS_DEVELOPMENT

# Backward compatibility aliases
BASE_DIR = Config.BASE_DIR
LOG_DIR = Config.LOG_DIR
DATA_DIR = Config.DATA_DIR
STATIC_DIR = Config.STATIC_DIR
CACHE_DIR = Config.CACHE_DIR
MODEL_DIR = Config.MODEL_DIR
