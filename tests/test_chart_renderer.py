import pytest

from utils.chart_renderer import ChartRenderer


@pytest.fixture
def renderer():
    return ChartRenderer()


@pytest.fixture
def sample_data():
    return {
        "summary": {"positive_count": 100, "neutral_count": 50, "negative_count": 30},
        "hot_topics": [{"name": f"话题{i}", "heat": 100 - i * 10} for i in range(5)],
        "alerts": [
            {"level": "danger"},
            {"level": "warning"},
            {"level": "warning"},
            {"level": "info"},
        ],
        "trend": [
            {"date": "2026-02-01", "count": 120},
            {"date": "2026-02-02", "count": 150},
            {"date": "2026-02-03", "count": 90},
        ],
    }


def test_render_sentiment_pie_returns_bytes(renderer, sample_data):
    result = renderer.render_sentiment_pie(sample_data)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_render_topics_bar_returns_bytes(renderer, sample_data):
    result = renderer.render_topics_bar(sample_data)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_render_trend_line_returns_bytes(renderer, sample_data):
    result = renderer.render_trend_line(sample_data)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_render_trend_line_no_data_returns_none(renderer):
    result = renderer.render_trend_line({})
    assert result is None


def test_render_alert_bar_returns_bytes(renderer, sample_data):
    result = renderer.render_alert_bar(sample_data)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_render_alert_bar_no_alerts_returns_none(renderer):
    result = renderer.render_alert_bar({})
    assert result is None
