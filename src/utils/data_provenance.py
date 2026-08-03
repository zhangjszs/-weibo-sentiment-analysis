"""Data provenance utilities for analysis responses.

Provides structured metadata constructors (``real_meta``, ``demo_meta``,
``experimental_meta``) that every analysis API must include in its response
as a ``meta`` field.  This makes it possible for consumers to distinguish
production-grade real data from demo/simulated data and experimental
features at a glance.

Typical usage::

    from utils.data_provenance import real_meta

    @bp.route("/analysis")
    def analysis():
        data = {...}
        meta = real_meta(topic="test", data_count=42, time_range=(start, end))
        return ok({"data": data, "meta": meta.to_dict()})
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, List, Tuple

# Default model identity — populated from the running config or fallback.
_DEFAULT_MODEL_NAME = os.getenv("ANALYSIS_MODEL_NAME", "snownlp + rule-based")
_DEFAULT_MODEL_VERSION = os.getenv("ANALYSIS_MODEL_VERSION", "1.0")
_DEFAULT_SOURCE_NAME = os.getenv("ANALYSIS_SOURCE_NAME", "weibo")


class AnalysisMeta:
    """Immutable metadata attached to every analysis response.

    Fields are read-only once constructed; serialisation is handled by
    :meth:`to_dict`.
    """

    __slots__ = (
        "source_type",
        "source_name",
        "is_demo",
        "model_name",
        "model_version",
        "time_range",
        "data_count",
        "generated_at",
        "limitations",
    )

    def __init__(
        self,
        *,
        source_type: str,
        source_name: str,
        is_demo: bool,
        model_name: str,
        model_version: str,
        time_range: Tuple[datetime, datetime],
        data_count: int,
        generated_at: datetime,
        limitations: list[str],
    ) -> None:
        for k, v in {
            "source_type": source_type,
            "source_name": source_name,
            "model_name": model_name,
            "model_version": model_version,
            "time_range": time_range,
        }.items():
            object.__setattr__(self, k, v)

        object.__setattr__(self, "is_demo", is_demo)
        object.__setattr__(self, "data_count", data_count)
        object.__setattr__(self, "generated_at", generated_at)
        object.__setattr__(self, "limitations", limitations)

    def __setattr__(self, name, value):
        raise AttributeError(f"AnalysisMeta is immutable: cannot set {name}")

    def to_dict(self) -> dict:
        start, end = self.time_range
        return {
            "source_type": self.source_type,
            "source_name": self.source_name,
            "is_demo": self.is_demo,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "time_range": {
                "start": start.isoformat() if start else None,
                "end": end.isoformat() if end else None,
            },
            "data_count": self.data_count,
            "generated_at": self.generated_at.isoformat(),
            "limitations": list(self.limitations),
        }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _validate(
    *,
    data_count: int,
    time_range: tuple[datetime, datetime] | None,
) -> None:
    """Raise ``ValueError`` if the common provenance invariants are violated."""
    if data_count is not None and (not isinstance(data_count, int) or data_count < 0):
        raise ValueError(f"data_count must be a non-negative integer, got {data_count!r}")
    if time_range is not None:
        if not isinstance(time_range, (tuple, list)) or len(time_range) != 2:
            raise ValueError(
                f"time_range must be a (start, end) tuple, got {time_range!r}"
            )
    elif data_count is not None and data_count > 0:
        raise ValueError("time_range is required when data_count > 0")


# ---------------------------------------------------------------------------
# Public constructors
# ---------------------------------------------------------------------------


def real_meta(
    topic: str,
    data_count: int,
    time_range: tuple[datetime, datetime] | None = None,
    *,
    source_name: str = _DEFAULT_SOURCE_NAME,
    model_name: str = _DEFAULT_MODEL_NAME,
    model_version: str = _DEFAULT_MODEL_VERSION,
    limitations: list[str] | None = None,
    generated_at: datetime | None = None,
) -> AnalysisMeta:
    """Build provenance metadata for **real / production** data.

    *topic* is a human-readable label (not validated against any schema).
    *data_count* is the number of data points that contributed to the analysis.
    *time_range* is the (start, end) datetime window covered by the data.

    Real data never carries ``is_demo=True`` and has no default limitations.
    """
    _validate(data_count=data_count, time_range=time_range)
    return AnalysisMeta(
        source_type="real",
        source_name=source_name,
        is_demo=False,
        model_name=model_name,
        model_version=model_version,
        time_range=time_range or (None, None),
        data_count=data_count,
        generated_at=generated_at or _now(),
        limitations=limitations or [],
    )


def demo_meta(
    topic: str,
    data_count: int,
    time_range: tuple[datetime, datetime] | None = None,
    *,
    source_name: str = _DEFAULT_SOURCE_NAME,
    model_name: str = _DEFAULT_MODEL_NAME,
    model_version: str = _DEFAULT_MODEL_VERSION,
    limitations: list[str] | None = None,
    generated_at: datetime | None = None,
) -> AnalysisMeta:
    """Build provenance metadata for **demo / simulated** data.

    Demo data always carries ``is_demo=True`` and a default disclaimer in
    *limitations* unless overridden.
    """
    _validate(data_count=data_count, time_range=time_range)
    default_limitations = limitations or [
        "演示数据：此数据为模拟生成，不代表真实分析结果。"
    ]
    return AnalysisMeta(
        source_type="demo",
        source_name=source_name,
        is_demo=True,
        model_name=model_name,
        model_version=model_version,
        time_range=time_range or (None, None),
        data_count=data_count,
        generated_at=generated_at or _now(),
        limitations=default_limitations,
    )


def provenance_response(
    data: dict | None,
    meta: AnalysisMeta,
    *,
    msg: str = "success",
    code: int = 200,
) -> tuple:
    """Wrap ``ok()`` with provenance metadata.

    This is the recommended way to return analysis responses::

        from utils.data_provenance import real_meta, provenance_response

        meta = real_meta(topic="test", data_count=42, ...)
        return provenance_response({"articles": [...]}, meta)
    """
    # Late import to avoid circular dependency at module level.
    from utils.api_response import ok as _ok

    payload = {"meta": meta.to_dict()}
    if data is not None:
        payload["data"] = data
    return _ok(payload, msg=msg, code=code), code


def experimental_meta(
    topic: str,
    data_count: int,
    time_range: tuple[datetime, datetime] | None = None,
    *,
    source_name: str = _DEFAULT_SOURCE_NAME,
    model_name: str = _DEFAULT_MODEL_NAME,
    model_version: str = _DEFAULT_MODEL_VERSION,
    limitations: list[str] | None = None,
    generated_at: datetime | None = None,
) -> AnalysisMeta:
    """Build provenance metadata for **experimental** features.

    Experimental results carry ``source_type=experimental`` and a default
    disclaimer that the capability is not stable.  *source_name* should
    identify the experimental platform or model.
    """
    _validate(data_count=data_count, time_range=time_range)
    default_limitations = limitations or [
        "实验能力：此分析来自实验性功能，数据完整性和准确率不保证。"
    ]
    return AnalysisMeta(
        source_type="experimental",
        source_name=source_name,
        is_demo=False,
        model_name=model_name,
        model_version=model_version,
        time_range=time_range or (None, None),
        data_count=data_count,
        generated_at=generated_at or _now(),
        limitations=default_limitations,
    )