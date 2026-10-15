"""Rust accelerator bridge with Python fallback (#97).

This package optionally exposes helpers from the compiled ``weibo_core``
extension. By default it probes for the extension and falls back to a
pure-Python implementation when it is missing or disabled via
``WEIBO_CORE_RUST=0``. Production code should call helpers from here
rather than importing ``weibo_core`` directly.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_ENABLED = os.getenv("WEIBO_CORE_RUST", "1").strip().lower() not in ("0", "false", "no", "off")

try:
    if _ENABLED:
        import weibo_core as _rust  # type: ignore[import-untyped]
    else:
        _rust = None
except Exception as exc:  # pragma: no cover - best effort detection at import time
    _rust = None
    logger.warning("weibo_core extension unavailable, falling back to Python: %s", exc)


def rust_available() -> bool:
    """Return True when the compiled extension is usable."""
    return _rust is not None


def normalize_lower(text: str) -> str:
    """Lower-case *text* (Rust if available, else Python)."""
    if _rust is not None:
        try:
            return str(_rust.normalize_lower(text))
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("weibo_core.normalize_lower failed, falling back: %s", exc)
    return str(text).lower()


def version() -> str | None:
    """Compiled extension version, or None when unavailable."""
    if _rust is not None:
        try:
            return str(_rust.version())
        except Exception:  # pragma: no cover
            return None
    return None
