"""Rust accelerator bridge with Python fallback (#97, #98).

This package optionally exposes helpers from the compiled ``weibo_core``
extension. By default it probes for the extension and falls back to a
pure-Python implementation when it is missing or disabled via
``WEIBO_CORE_RUST=0``. Production code should call helpers from here
rather than importing ``weibo_core`` directly.

The ``*_py`` functions are the canonical pure-Python references; the
public names try Rust first and fall back on any error, so both backends
are contract-equal (parity is covered by ``tests/test_rust_dedup.py``).

Batch entry points materialize a one-shot iterable exactly once, before
handing it to the extension, so a failing FFI call can still fall back on
the same items instead of an exhausted iterator (#104).

Known bounded divergence: case mapping is Unicode-data-version bound. The
Rust crate's tables are newer than CPython 3.12's, so 55 code points that
CPython still treats as unassigned (``Cn``) have a lowercase mapping on the
Rust side. Every code point Python knows a rule for is equivalent.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterable

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


def _rust_fn(name: str):
    """Return the compiled ``weibo_core.<name>`` callable or None."""
    if _rust is None:
        return None
    return getattr(_rust, name, None)


def rust_available() -> bool:
    """Return True when the compiled extension is usable."""
    return _rust is not None


# ---------------------------------------------------------------------------
# Pure-Python references (canonical semantics)
# ---------------------------------------------------------------------------


def normalize_lower_py(text: str) -> str:
    """Unicode-lowercase ``text``."""
    return str(text).lower()


def normalize_post_py(text: str) -> str:
    """Lowercase + trim + collapse every whitespace run to one space."""
    return " ".join(str(text).lower().split())


def generate_article_key_py(article_id: str, content_hash: str | None = None) -> str:
    """Mirror ``ArticleDeduplicator.generate_key``."""
    aid = str(article_id)
    if content_hash:
        return f"{aid}:{str(content_hash)[:16]}"
    return aid


def generate_comment_key_py(comment_id: str, article_id: str) -> str:
    """Mirror ``CommentDeduplicator.generate_key`` (``"{aid}:{cid}"``)."""
    return f"{str(article_id)}:{str(comment_id)}"


def dedup_keys_py(keys: Iterable[str]) -> list[str]:
    """Order-preserving dedup; first occurrence wins."""
    seen: set[str] = set()
    out: list[str] = []
    for key in keys:
        ks = str(key)
        if ks not in seen:
            seen.add(ks)
            out.append(ks)
    return out


# ---------------------------------------------------------------------------
# Public API (Rust first, Python fallback)
# ---------------------------------------------------------------------------


def normalize_lower(text: str) -> str:
    """Lower-case *text* (Rust if available, else Python)."""
    fn = _rust_fn("normalize_lower")
    if fn is not None:
        try:
            return str(fn(text))
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("weibo_core.normalize_lower failed, falling back: %s", exc)
    return normalize_lower_py(text)


def normalize_post(text: str) -> str:
    """Canonical post normalization (Rust if available, else Python)."""
    fn = _rust_fn("normalize_post")
    if fn is not None:
        try:
            return str(fn(text))
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("weibo_core.normalize_post failed, falling back: %s", exc)
    return normalize_post_py(text)


def generate_article_key(article_id: str, content_hash: str | None = None) -> str:
    """Article dedup key (Rust if available, else Python)."""
    fn = _rust_fn("generate_article_key")
    if fn is not None:
        try:
            return str(fn(str(article_id), str(content_hash) if content_hash else None))
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("weibo_core.generate_article_key failed, falling back: %s", exc)
    return generate_article_key_py(article_id, content_hash)


def generate_comment_key(comment_id: str, article_id: str) -> str:
    """Comment dedup key (Rust if available, else Python)."""
    fn = _rust_fn("generate_comment_key")
    if fn is not None:
        try:
            return str(fn(str(comment_id), str(article_id)))
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("weibo_core.generate_comment_key failed, falling back: %s", exc)
    return generate_comment_key_py(comment_id, article_id)


def _materialize(values: Iterable[str]) -> list[str]:
    """Return *values* as a list, consuming a one-shot iterable only once.

    Batch entry points must materialize their input **before** handing it to
    the extension, because a failure part-way through (e.g. PyO3 rejecting a
    lone surrogate with ``UnicodeEncodeError``) forces the Python fallback --
    and the fallback needs the very same items. Consuming inside the ``try``
    meant the fallback re-read an already-exhausted iterator and silently
    returned ``[]``, losing the whole batch (#104).

    A ``list`` is passed through untouched: the extension takes it by value
    anyway, so copying would only add cost on the hot path.
    """
    return values if isinstance(values, list) else list(values)


def dedup_keys(keys: Iterable[str]) -> list[str]:
    """Order-preserving batch dedup (Rust if available, else Python)."""
    items = _materialize(keys)
    fn = _rust_fn("dedup_keys")
    if fn is not None:
        try:
            return fn(items)
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("weibo_core.dedup_keys failed, falling back: %s", exc)
    return dedup_keys_py(items)


def normalize_posts_py(texts: Iterable[str]) -> list[str]:
    """Batch post normalization (reference)."""
    return [normalize_post_py(t) for t in texts]


def normalize_posts(texts: Iterable[str]) -> list[str]:
    """Batch post normalization: one FFI call (Rust if available, else Python)."""
    items = _materialize(texts)
    fn = _rust_fn("normalize_posts")
    if fn is not None:
        try:
            return fn(items)
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("weibo_core.normalize_posts failed, falling back: %s", exc)
    return normalize_posts_py(items)


def version() -> str | None:
    """Compiled extension version, or None when unavailable."""
    if _rust is not None:
        try:
            return str(_rust.version())
        except Exception:  # pragma: no cover
            return None
    return None
