"""Report contract definitions.

Every generated report must include provenance information so consumers
can answer: where did this data come from, when was it generated, and
what are its limitations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ReportMeta:
    """Metadata attached to every generated report.

    Serialised as a dict via :meth:`to_dict` for JSON responses.
    """

    topic: str
    time_range: tuple[datetime | None, datetime | None]
    source: str = "weibo"
    data_count: int = 0
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    model_version: str = "1.0"
    limitations: list[str] = field(default_factory=list)
    audit_event_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        start, end = self.time_range
        return {
            "topic": self.topic,
            "time_range": {
                "start": start.isoformat() if start else None,
                "end": end.isoformat() if end else None,
            },
            "source": self.source,
            "data_count": self.data_count,
            "generated_at": self.generated_at.isoformat(),
            "model_version": self.model_version,
            "limitations": list(self.limitations),
            "audit_event_id": self.audit_event_id,
        }


def build_report_meta(
    topic: str,
    data_count: int,
    time_range: tuple[datetime | None, datetime | None] | None = None,
    *,
    source: str = "weibo",
    is_demo: bool = False,
) -> ReportMeta:
    """Build :class:`ReportMeta` with sensible defaults.

    Demo reports automatically include a disclaimer.
    """
    limitations = []
    if is_demo:
        limitations.append("演示数据：此报告数据为模拟生成，不代表真实分析结果。")
    if data_count == 0:
        limitations.append("所选话题在时间范围内没有采集到数据，报告内容为空。")

    return ReportMeta(
        topic=topic,
        time_range=time_range or (None, None),
        source=source,
        data_count=data_count,
        limitations=limitations,
    )