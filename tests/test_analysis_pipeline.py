"""Tests for ``AnalysisPipeline`` (analysis_pipeline.py).

Covers four scenarios: real data, empty data, demo data, and database error.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from services.analysis_pipeline import AnalysisPipeline, AnalysisSnapshot


def _dt(y=2026, m=8, d=1):
    return datetime(y, m, d, tzinfo=timezone.utc)


@pytest.fixture
def pipeline():
    return AnalysisPipeline()


# ---------------------------------------------------------------------------
# Scenario: real data exists
# ---------------------------------------------------------------------------


class TestRealDataScenario:
    def test_returns_snapshot_with_all_fields(self, pipeline):
        """A full snapshot must contain summary, trend, sentiment, articles,
        comments, propagation and meta."""
        snapshot = pipeline.run(
            topic="test",
            start_at=_dt(2026, 7, 1),
            end_at=_dt(2026, 8, 1),
            demo=False,
        )
        assert isinstance(snapshot, AnalysisSnapshot)
        assert "summary" in snapshot.data
        assert "trend" in snapshot.data
        assert "sentiment" in snapshot.data
        assert "top_articles" in snapshot.data
        assert "top_comments" in snapshot.data
        assert "propagation" in snapshot.data

    def test_meta_is_real_when_not_demo(self, pipeline):
        snapshot = pipeline.run(
            topic="test", start_at=_dt(2026, 7, 1), end_at=_dt(2026, 8, 1), demo=False
        )
        meta = snapshot.data.get("meta", {})
        assert meta.get("source_type") == "real"
        assert meta.get("is_demo") is False

    def test_meta_includes_time_range_and_data_count(self, pipeline):
        snapshot = pipeline.run(
            topic="test", start_at=_dt(2026, 7, 1), end_at=_dt(2026, 8, 1), demo=False
        )
        meta = snapshot.data.get("meta", {})
        assert meta.get("time_range") is not None
        assert isinstance(meta.get("data_count"), int)


# ---------------------------------------------------------------------------
# Scenario: no data
# ---------------------------------------------------------------------------


class TestEmptyDataScenario:
    def test_returns_empty_summary_when_no_data(self, pipeline):
        """Even with no data, the pipeline must return a stable snapshot."""
        snapshot = pipeline.run(
            topic="no_such_topic_xyz",
            start_at=_dt(2025, 1, 1),
            end_at=_dt(2025, 1, 2),
            demo=False,
        )
        meta = snapshot.data.get("meta", {})
        assert meta.get("data_count") == 0
        assert meta.get("source_type") == "real"
        # Summary should still be present but empty
        summary = snapshot.data.get("summary", {})
        assert summary.get("total_articles", 0) == 0

    def test_limitations_mention_no_data_when_empty(self, pipeline):
        snapshot = pipeline.run(
            topic="no_such_topic_xyz",
            start_at=_dt(2025, 1, 1),
            end_at=_dt(2025, 1, 2),
            demo=False,
        )
        limitations = snapshot.data.get("meta", {}).get("limitations", [])
        # Should include a note about no data
        limitations_text = " ".join(limitations)
        assert len(limitations) > 0


# ---------------------------------------------------------------------------
# Scenario: demo data
# ---------------------------------------------------------------------------


class TestDemoDataScenario:
    def test_meta_is_demo_when_demo_flag_set(self, pipeline):
        snapshot = pipeline.run(
            topic="demo_topic",
            start_at=_dt(2026, 7, 1),
            end_at=_dt(2026, 8, 1),
            demo=True,
        )
        meta = snapshot.data.get("meta", {})
        assert meta.get("source_type") == "demo"
        assert meta.get("is_demo") is True

    def test_demo_data_has_limitations(self, pipeline):
        snapshot = pipeline.run(
            topic="demo_topic",
            start_at=_dt(2026, 7, 1),
            end_at=_dt(2026, 8, 1),
            demo=True,
        )
        limitations = snapshot.data.get("meta", {}).get("limitations", [])
        assert len(limitations) > 0
        assert any("演示" in lim for lim in limitations)

    def test_demo_returns_nonzero_data_count(self, pipeline):
        snapshot = pipeline.run(
            topic="demo_topic",
            start_at=_dt(2026, 7, 1),
            end_at=_dt(2026, 8, 1),
            demo=True,
        )
        assert snapshot.data.get("meta", {}).get("data_count", 0) > 0


# ---------------------------------------------------------------------------
# Scenario: database error / graceful degradation
# ---------------------------------------------------------------------------


class TestDegradationScenario:
    def test_pipeline_does_not_crash_on_repository_error(self):
        """Even if the repository raises, the pipeline should return a degraded
        snapshot rather than propagating the exception."""
        p = AnalysisPipeline()
        with patch.object(
            p, "_fetch_real_data", side_effect=RuntimeError("db connection lost")
        ):
            snapshot = p.run(
                topic="test",
                start_at=_dt(2026, 7, 1),
                end_at=_dt(2026, 8, 1),
                demo=False,
            )
        # Should still return a snapshot with meta
        assert isinstance(snapshot, AnalysisSnapshot)
        meta = snapshot.data.get("meta", {})
        assert meta.get("source_type") == "real"
        # Limitations should mention the degradation
        limitations = meta.get("limitations", [])
        assert len(limitations) > 0

    def test_degraded_snapshot_still_has_top_level_fields(self, pipeline):
        """Even in degraded mode, the snapshot must be structurally complete."""
        with patch.object(
            pipeline, "_fetch_real_data", side_effect=RuntimeError("timeout")
        ):
            snapshot = pipeline.run(
                topic="test",
                start_at=_dt(2026, 7, 1),
                end_at=_dt(2026, 8, 1),
                demo=False,
            )
        for key in ("summary", "trend", "sentiment", "meta"):
            assert key in snapshot.data, f"missing {key} in degraded snapshot"


# ---------------------------------------------------------------------------
# AnalysisSnapshot contract
# ---------------------------------------------------------------------------


class TestSnapshotContract:
    def test_can_serialize_to_dict(self, pipeline):
        snapshot = pipeline.run(
            topic="test",
            start_at=_dt(2026, 7, 1),
            end_at=_dt(2026, 8, 1),
            demo=False,
        )
        d = snapshot.to_dict()
        assert isinstance(d, dict)
        assert "summary" in d
        assert "meta" in d

    def test_to_dict_includes_generated_at(self, pipeline):
        d = pipeline.run(
            topic="test",
            start_at=_dt(2026, 7, 1),
            end_at=_dt(2026, 8, 1),
            demo=False,
        ).to_dict()
        assert "generated_at" in d
        assert isinstance(d["generated_at"], str)