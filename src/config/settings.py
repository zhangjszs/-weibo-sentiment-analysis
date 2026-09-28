import logging
import os
from urllib.parse import urlparse

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


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


def _parse_int_env(name: str, default: int) -> int:
    """import 期无异常整型解析：非法值回退 default，详情由 validate() 汇总报错。"""
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        return default


def _parse_float_env(name: str, default: float) -> float:
    """import 期无异常浮点解析：非法值回退 default，详情由 validate() 汇总报错。"""
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        return float(str(raw).strip())
    except (TypeError, ValueError):
        return default


def _inject_redis_password(url: str, password: str) -> str:
    """把 REDIS_PASSWORD 回填进 broker/backend URL（#23）。

    Celery 只认 URL 内密码，而直接 redis 客户端走
    ``get_redis_connection_params``（独立读取 REDIS_PASSWORD）。
    仅当 password 非空、URL 自身无密码、且 scheme 为 redis(s) 时注入；
    其余情况原样返回（显式密码优先，"disabled" 等非 URL 不动）。
    """
    if not url or not password:
        return url
    try:
        from urllib.parse import quote, urlunparse

        parsed = urlparse(url)
        if parsed.scheme not in ("redis", "rediss") or parsed.password:
            return url
        userinfo = f":{quote(password, safe='')}"
        if parsed.username:
            userinfo = f"{parsed.username}{userinfo}"
        netloc = f"{userinfo}@{parsed.hostname or 'localhost'}"
        if parsed.port:
            netloc += f":{parsed.port}"
        return urlunparse(
            (
                parsed.scheme,
                netloc,
                parsed.path or "",
                parsed.params,
                parsed.query,
                parsed.fragment,
            )
        )
    except (ValueError, TypeError):
        return url


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
    # 是否显式配置了 JWT_SECRET_KEY（用于生产环境密钥隔离校验）
    JWT_SECRET_KEY_EXPLICIT = bool(os.getenv("JWT_SECRET_KEY"))
    JWT_EXPIRATION_HOURS = _parse_int_env("JWT_EXPIRATION_HOURS", 24)
    AUTH_COOKIE_NAME = os.getenv("AUTH_COOKIE_NAME", "weibo_access_token")

    # Database Settings
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = _parse_int_env("DB_PORT", 3306)
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
    DB_NAME = os.getenv("DB_NAME", "weibo_analysis")
    DB_CHARSET = "utf8mb4"

    DB_POOL_SIZE = _parse_int_env("DB_POOL_SIZE", 10)
    DB_POOL_RECYCLE = 3600
    DB_POOL_TIMEOUT = 30

    @classmethod
    def get_database_url(cls):
        from urllib.parse import quote_plus

        user = quote_plus(cls.DB_USER)
        password = quote_plus(cls.DB_PASSWORD)
        return f"mysql+pymysql://{user}:{password}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}?charset={cls.DB_CHARSET}"

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
    REDIS_PORT = _parse_int_env("REDIS_PORT", int(_REDIS_PARSED["port"]))
    REDIS_DB = _parse_int_env("REDIS_DB", int(_REDIS_PARSED["db"]))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", str(_REDIS_PARSED["password"]))

    CELERY_BROKER_URL = _inject_redis_password(
        os.getenv("CELERY_BROKER_URL", REDIS_URL), REDIS_PASSWORD
    )
    CELERY_RESULT_BACKEND = _inject_redis_password(
        os.getenv("CELERY_RESULT_BACKEND", REDIS_URL), REDIS_PASSWORD
    )

    # LLM Settings
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_API_URL = os.getenv("LLM_API_URL", "https://api.deepseek.com/v1/chat/completions")
    LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
    LLM_TIMEOUT = _parse_int_env("LLM_TIMEOUT", 30)
    LLM_CACHE_TTL = _parse_int_env("LLM_CACHE_TTL", 3600)

    # Spider Settings
    WEIBO_COOKIE = os.getenv("WEIBO_COOKIE", "")
    WEIBO_USER_AGENT = os.getenv(
        "WEIBO_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    )
    SPIDER_TIMEOUT = _parse_int_env("SPIDER_TIMEOUT", 45)
    SPIDER_DELAY = _parse_float_env("SPIDER_DELAY", 15.0)
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
    SPIDER_SERVICE_TIMEOUT = _parse_int_env("SPIDER_SERVICE_TIMEOUT", 15)
    SPIDER_SERVICE_TOKEN = os.getenv("SPIDER_SERVICE_TOKEN", "")
    SPIDER_SERVICE_FALLBACK_LOCAL = (
        os.getenv("SPIDER_SERVICE_FALLBACK_LOCAL", "True").lower() == "true"
    )

    NLP_SERVICE_ENABLED = os.getenv("NLP_SERVICE_ENABLED", "False").lower() == "true"
    NLP_SERVICE_BASE_URL = os.getenv(
        "NLP_SERVICE_BASE_URL", "http://localhost:8091"
    ).rstrip("/")
    NLP_SERVICE_TIMEOUT = _parse_int_env("NLP_SERVICE_TIMEOUT", 20)
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

    # Sentiment Backend Settings（Phase 3 BERT 升级）
    # 取值：bert / sklearn / snownlp / auto（auto=优先 bert，按链路降级）
    SENTIMENT_BACKEND = os.getenv("SENTIMENT_BACKEND", "auto")
    BERT_MODEL_NAME = os.getenv(
        "BERT_MODEL_NAME", "IDEA-CCNL/Erlangshen-Roberta-110M-Sentiment"
    )
    BERT_MODEL_PATH = os.getenv(
        "BERT_MODEL_PATH", os.path.join(MODEL_DIR, "bert_sentiment_onnx")
    )
    BERT_MAX_LENGTH = _parse_int_env("BERT_MAX_LENGTH", 128)
    BERT_BATCH_SIZE = _parse_int_env("BERT_BATCH_SIZE", 32)
    BERT_DEVICE = os.getenv("BERT_DEVICE", "cpu")  # cpu / cuda
    BERT_FALLBACK_TO_SKLEARN = (
        os.getenv("BERT_FALLBACK_TO_SKLEARN", "True").lower() == "true"
    )
    BERT_INFERENCE_TIMEOUT = _parse_float_env("BERT_INFERENCE_TIMEOUT", 2.0)

    # App Settings
    JSON_AS_ASCII = False
    SEND_FILE_MAX_AGE_DEFAULT = 0 if IS_DEVELOPMENT else 43200
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    PERMANENT_SESSION_LIFETIME = 86400 * 7  # 7 days

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_SANITIZE_ENABLED = os.getenv("LOG_SANITIZE_ENABLED", "True").lower() in {"1", "true", "yes", "on"}

    # Data Governance
    AUDIT_LOG_RETENTION_DAYS = _parse_int_env("AUDIT_LOG_RETENTION_DAYS", 90)
    REPORT_TEMP_CLEANUP_HOURS = _parse_int_env("REPORT_TEMP_CLEANUP_HOURS", 1)

    # Demo / Bootstrap
    # 注意：DEMO_ADMIN_PASSWORD 默认留空，避免误开 AUTO_CREATE_DEMO_ADMIN 时落入弱口令后门；
    # 需要演示账号时请显式配置足够强度的密码。
    DEMO_ADMIN_USERNAME = os.getenv("DEMO_ADMIN_USERNAME", "admin")
    DEMO_ADMIN_PASSWORD = os.getenv("DEMO_ADMIN_PASSWORD", "")
    AUTO_CREATE_DEMO_ADMIN = _parse_bool_env(
        "AUTO_CREATE_DEMO_ADMIN", default=False
    )
    DEMO_ADMIN_RESET_PASSWORD = _parse_bool_env(
        "DEMO_ADMIN_RESET_PASSWORD", default=False
    )
    ENABLE_STARTUP_WARMUP = _parse_bool_env(
        "ENABLE_STARTUP_WARMUP", default=IS_DEVELOPMENT
    )
    STARTUP_WARMUP_DELAY = _parse_float_env("STARTUP_WARMUP_DELAY", 0.5)

    # 需要生产级保护的环境（development/testing 走开发默认，不阻断）
    PROTECTED_ENVS = frozenset({"production", "staging"})

    # 数值型配置：(env 名, 解析器)，validate() 汇总校验
    _NUMERIC_ENVS: tuple = (
        ("JWT_EXPIRATION_HOURS", int),
        ("DB_PORT", int),
        ("DB_POOL_SIZE", int),
        ("REDIS_PORT", int),
        ("REDIS_DB", int),
        ("LLM_TIMEOUT", int),
        ("LLM_CACHE_TTL", int),
        ("SPIDER_TIMEOUT", int),
        ("SPIDER_DELAY", float),
        ("SPIDER_SERVICE_TIMEOUT", int),
        ("NLP_SERVICE_TIMEOUT", int),
        ("BERT_MAX_LENGTH", int),
        ("BERT_BATCH_SIZE", int),
        ("BERT_INFERENCE_TIMEOUT", float),
        ("AUDIT_LOG_RETENTION_DAYS", int),
        ("REPORT_TEMP_CLEANUP_HOURS", int),
        ("STARTUP_WARMUP_DELAY", float),
    )

    @classmethod
    def validate(cls) -> None:
        errors: list[str] = []
        for name, parser in cls._NUMERIC_ENVS:
            raw = os.getenv(name)
            if raw is None or not str(raw).strip():
                continue
            try:
                parser(str(raw).strip())
            except (TypeError, ValueError):
                errors.append(f"{name} 不是有效数字: {raw!r}（已回退默认值）")
        if cls.FLASK_ENV in cls.PROTECTED_ENVS:
            if not cls.SECRET_KEY:
                errors.append("SECRET_KEY must be set in production")
            if not cls.JWT_SECRET_KEY_EXPLICIT or not cls.JWT_SECRET_KEY:
                errors.append(
                    "JWT_SECRET_KEY must be set in production (key isolation: "
                    "it must differ from SECRET_KEY)"
                )
            elif cls.JWT_SECRET_KEY == cls.SECRET_KEY:
                errors.append("JWT_SECRET_KEY must differ from SECRET_KEY in production")
            if not cls.ALLOWED_ORIGINS:
                errors.append("ALLOWED_ORIGINS must be set in production")
            if not cls.ADMIN_USERS:
                errors.append("ADMIN_USERS must be set in production")
            if errors:
                raise RuntimeError("; ".join(errors))
        elif errors:
            for message in errors:
                logger.warning("配置数值无效: %s", message)


# Backward compatibility aliases
BASE_DIR = Config.BASE_DIR
LOG_DIR = Config.LOG_DIR
DATA_DIR = Config.DATA_DIR
STATIC_DIR = Config.STATIC_DIR
CACHE_DIR = Config.CACHE_DIR
MODEL_DIR = Config.MODEL_DIR
