"""Tests for report provenance and contracts.

Covers report metadata structure, demo/empty data handling, and
integration with the report generator.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from services.report_contracts import ReportMeta, build_report_meta


class TestReportMeta:
    def test_basic_meta_includes_all_fields(self):
        meta = build_report_meta(
            topic="AI",
            data_count=100,
            time_range=(
                datetime(2026, 7, 1, tzinfo=timezone.utc),
                datetime(2026, 8, 1, tzinfo=timezone.utc),
            ),
        )
        d = meta.to_dict()
        assert d["topic"] == "AI"
        assert d["source"] == "weibo"
        assert d["data_count"] == 100
        assert d["time_range"]["start"] is not None
        assert d["time_range"]["end"] is not None
        assert isinstance(d["generated_at"], str)
        assert isinstance(d["model_version"], str)

    def test_demo_report_has_limitations(self):
        meta = build_report_meta(
            topic="demo",
            data_count=50,
            is_demo=True,
        )
        assert len(meta.limitations) > 0
        assert any("演示" in lim for lim in meta.limitations)

    def test_zero_data_report_has_limitations(self):
        meta = build_report_meta(
            topic="empty",
            data_count=0,
        )
        assert len(meta.limitations) > 0
        assert any("空" in lim or "没有" in lim for lim in meta.limitations)

    def test_meta_tracks_audit_event_id(self):
        meta = build_report_meta(topic="test", data_count=10)
        meta.audit_event_id = 42
        d = meta.to_dict()
        assert d["audit_event_id"] == 42

    def test_meta_without_time_range(self):
        meta = build_report_meta(topic="test", data_count=0)
        d = meta.to_dict()
        assert d["time_range"]["start"] is None
        assert d["time_range"]["end"] is None


class TestReportContentContract:
    """Reports must never include 'conclusion' sections when data_count is 0."""

    def test_empty_report_has_no_analysis_conclusion(self):
        """When there is no data, the report must not fabricate conclusions."""
        meta = build_report_meta(topic="empty", data_count=0)
        assert meta.data_count == 0
        # The calling code should check data_count before writing conclusions
        # This test validates the meta correctly flags the empty state.
        assert any("空" in lim or "没有" in lim for lim in meta.limitations)


class TestReportMetaSerialization:
    def test_to_dict_contains_expected_keys(self):
        meta = build_report_meta(topic="x", data_count=1)
        keys = {"topic", "time_range", "source", "data_count", "generated_at", "model_version", "limitations", "audit_event_id"}
        assert set(meta.to_dict().keys()) == keys

    def test_to_dict_time_range_structure(self):
        meta = build_report_meta(topic="x", data_count=1)
        tr = meta.to_dict()["time_range"]
        assert "start" in tr
        assert "end" in tr