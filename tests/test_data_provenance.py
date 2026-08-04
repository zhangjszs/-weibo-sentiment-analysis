"""Tests for data provenance (data_provenance.py).

Covers the three constructors (real, demo, experimental), validation rules,
and response-level integration with AnalysisMeta.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from utils.data_provenance import (
    AnalysisMeta,
    demo_meta,
    experimental_meta,
    real_meta,
)


def _ts(year=2026, month=8, day=3) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# real_meta
# ---------------------------------------------------------------------------


class TestRealMeta:
    def test_real_meta_has_correct_source_type(self):
        meta = real_meta(
            topic="test",
            data_count=100,
            time_range=(_ts(6), _ts(7)),
        )
        assert meta.source_type == "real"
        assert meta.is_demo is False

    def test_real_meta_requires_data_count(self):
        with pytest.raises(ValueError, match="data_count"):
            real_meta(topic="test", data_count=-1, time_range=(_ts(6), _ts(7)))

    def test_real_meta_requires_time_range(self):
        with pytest.raises(ValueError, match="time_range"):
            real_meta(topic="test", data_count=100, time_range=None)

    def test_real_meta_includes_generated_at(self):
        meta = real_meta(
            topic="test",
            data_count=100,
            time_range=(_ts(6), _ts(7)),
        )
        assert isinstance(meta.generated_at, datetime)

    def test_real_meta_limitations_is_empty_by_default(self):
        meta = real_meta(
            topic="test",
            data_count=100,
            time_range=(_ts(6), _ts(7)),
        )
        assert meta.limitations == []


# ---------------------------------------------------------------------------
# demo_meta
# ---------------------------------------------------------------------------


class TestDemoMeta:
    def test_demo_meta_has_correct_source_type(self):
        meta = demo_meta(
            topic="test",
            data_count=50,
            time_range=(_ts(6), _ts(7)),
        )
        assert meta.source_type == "demo"
        assert meta.is_demo is True

    def test_demo_meta_must_have_limitations(self):
        """Demo data must always carry a limitations disclaimer."""
        meta = demo_meta(
            topic="test",
            data_count=50,
            time_range=(_ts(6), _ts(7)),
        )
        assert len(meta.limitations) > 0
        assert any("演示" in lim for lim in meta.limitations)

    def test_demo_meta_requires_data_count(self):
        with pytest.raises(ValueError, match="data_count"):
            demo_meta(topic="test", data_count=-1, time_range=(_ts(6), _ts(7)))


# ---------------------------------------------------------------------------
# experimental_meta
# ---------------------------------------------------------------------------


class TestExperimentalMeta:
    def test_experimental_meta_has_correct_source_type(self):
        meta = experimental_meta(
            topic="test",
            data_count=10,
            time_range=(_ts(6), _ts(7)),
            source_name="zhihu",
        )
        assert meta.source_type == "experimental"
        assert meta.is_demo is False

    def test_experimental_meta_includes_source_name(self):
        meta = experimental_meta(
            topic="test",
            data_count=10,
            time_range=(_ts(6), _ts(7)),
            source_name="douyin",
        )
        assert meta.source_name == "douyin"

    def test_experimental_meta_must_have_limitations(self):
        meta = experimental_meta(
            topic="test",
            data_count=10,
            time_range=(_ts(6), _ts(7)),
            source_name="bilibili",
        )
        assert len(meta.limitations) > 0
        assert any("实验" in lim for lim in meta.limitations)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestMetaValidation:
    def test_negative_data_count_raises(self):
        with pytest.raises(ValueError):
            real_meta(topic="test", data_count=-5, time_range=(_ts(6), _ts(7)))

    @pytest.mark.parametrize("bad_range", [None, (), (_ts(6),), (_ts(6), _ts(7), _ts(8))])
    def test_invalid_time_range_raises(self, bad_range):
        with pytest.raises(ValueError):
            real_meta(topic="test", data_count=100, time_range=bad_range)

    def test_to_dict_contains_all_expected_keys(self):
        meta = real_meta(
            topic="test",
            data_count=100,
            time_range=(_ts(6), _ts(7)),
            source_name="weibo",
            model_name="snownlp",
            model_version="1.0",
        )
        d = meta.to_dict()
        expected_keys = {
            "source_type",
            "source_name",
            "is_demo",
            "model_name",
            "model_version",
            "time_range",
            "data_count",
            "generated_at",
            "limitations",
        }
        assert set(d.keys()) == expected_keys

    def test_to_dict_time_range_format(self):
        start = _ts(2026, 6, 1)
        end = _ts(2026, 7, 30)
        meta = real_meta(topic="test", data_count=100, time_range=(start, end))
        d = meta.to_dict()
        assert d["time_range"]["start"] == start.isoformat()
        assert d["time_range"]["end"] == end.isoformat()