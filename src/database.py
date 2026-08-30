"""Database engine and session management.

Engine and session are **lazily initialised** — they are not created until
first access.  This allows unit tests to import modules without requiring a
running MySQL instance.

Usage::

    from database import engine, db_session, Base, init_db

``engine`` and ``db_session`` resolve on first attribute access, so
``from database import engine`` works transparently.

To force a different URL (e.g. SQLite in tests), call ``init_db(url=...)``
before any code that triggers a connection.
"""

from __future__ import annotations

import logging
import os
import threading
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker

from config.settings import Config

logger = logging.getLogger(__name__)

# Module-level state — initialised on demand.
_engine = None
_db_session = None
_engine_lock = threading.Lock()
_session_lock = threading.Lock()


def _build_database_url() -> str:
    """Build database URL with proper escaping for credentials."""
    # TEST_DATABASE_URL takes precedence and is assumed already escaped (e.g. sqlite://)
    test_url = os.environ.get("TEST_DATABASE_URL")
    if test_url:
        return test_url
    # Quote credentials to handle special chars like @ / : ? in passwords
    user = quote_plus(Config.DB_USER)
    password = quote_plus(Config.DB_PASSWORD)
    host = Config.DB_HOST
    port = Config.DB_PORT
    name = Config.DB_NAME
    charset = Config.DB_CHARSET
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset={charset}"


def get_engine():
    """Return the global SQLAlchemy engine, creating it lazily on first call."""
    global _engine
    if _engine is not None:
        return _engine
    with _engine_lock:
        if _engine is None:
            url = _build_database_url()
            connect_args: dict = {}

            if url.startswith("sqlite"):
                connect_args["check_same_thread"] = False
                _engine = create_engine(url, connect_args=connect_args)
            else:
                connect_args["connect_timeout"] = 5
                _engine = create_engine(
                    url,
                    pool_size=Config.DB_POOL_SIZE,
                    max_overflow=20,
                    pool_recycle=Config.DB_POOL_RECYCLE,
                    pool_pre_ping=True,
                    connect_args=connect_args,
                )
    return _engine


def get_db_session():
    """Return the global scoped session, creating lazily on first call."""
    global _db_session
    if _db_session is not None:
        return _db_session
    with _session_lock:
        if _db_session is None:
            _db_session = scoped_session(
                sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
            )
    return _db_session


class Base(DeclarativeBase):
    """Declarative base for all ORM models.  Always available, no DB needed."""


def init_db(url: str | None = None):
    """Create all tables against *url* (or the configured database)."""
    global _engine, _db_session
    with _engine_lock, _session_lock:
        if url:
            connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
            _engine = create_engine(url, connect_args=connect_args)
            _db_session = scoped_session(
                sessionmaker(autocommit=False, autoflush=False, bind=_engine)
            )
    Base.metadata.create_all(bind=get_engine())


def reset():
    """Reset cached engine and session to ``None``.

    Call this in test teardown or before importing the app with a different
    database URL so that the next ``get_engine()`` / ``get_db_session()``
    call creates fresh connections.
    """
    global _engine, _db_session
    with _engine_lock, _session_lock:
        if _db_session is not None:
            try:
                _db_session.remove()
            except Exception:
                pass
            _db_session = None
        if _engine is not None:
            try:
                _engine.dispose()
            except Exception:
                pass
            _engine = None


# ---- Lazy module-level accessors ----
# ``from database import engine`` triggers __getattr__ on first import;
# subsequent accesses read the local binding directly.

def __getattr__(name):
    if name == "engine":
        return get_engine()
    if name == "db_session":
        return get_db_session()
    raise AttributeError(f"module 'database' has no attribute {name!r}")


__all__ = ["engine", "db_session", "Base", "init_db", "reset", "get_engine", "get_db_session"]  # noqa: F822
