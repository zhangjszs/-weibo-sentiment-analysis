# tests/test_report_charts.py
"""
TDD: 测试图表嵌入到 PDF/PPT 报告的功能
"""

import os
import tempfile

import pytest

from utils.report_generator import PDFReportGenerator, PPTReportGenerator, ReportConfig


@pytest.fixture
def sample_data():
    return {
        "summary": {
            "positive_count": 100,
            "neutral_count": 50,
            "negative_count": 30,
            "total_articles": 180,
            "total_comments": 500,
        },
        "hot_topics": [{"name": f"话题{i}", "heat": 100 - i * 10} for i in range(5)],
        "alerts": [
            {"level": "danger", "title": "严重预警", "message": "负面情感激增"},
            {"level": "warning", "title": "一般预警", "message": "热度上升"},
        ],
        "trend": [
            {"date": "2026-02-01", "count": 120},
            {"date": "2026-02-02", "count": 150},
            {"date": "2026-02-03", "count": 90},
        ],
    }


@pytest.fixture
def pdf_gen():
    return PDFReportGenerator()


@pytest.fixture
def ppt_gen():
    return PPTReportGenerator()


# --- PDF 图表嵌入测试 ---


def test_pdf_generate_with_charts_returns_path(pdf_gen, sample_data):
    """PDF 生成含图表时应返回文件路径"""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        out = f.name
    try:
        result = pdf_gen.generate(
            sample_data, output_path=out, config=ReportConfig(include_charts=True)
        )
        assert result == out
        assert os.path.exists(out)
        assert os.path.getsize(out) > 0
    finally:
        if os.path.exists(out):
            os.unlink(out)


def test_pdf_with_charts_larger_than_without(pdf_gen, sample_data):
    """含图表的 PDF 应比不含图表的更大"""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        out_with = f.name
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        out_without = f.name
    try:
        pdf_gen.generate(
            sample_data, output_path=out_with, config=ReportConfig(include_charts=True)
        )
        pdf_gen.generate(
            sample_data,
            output_path=out_without,
            config=ReportConfig(include_charts=False),
        )
        assert os.path.getsize(out_with) > os.path.getsize(out_without)
    finally:
        for p in (out_with, out_without):
            if os.path.exists(p):
                os.unlink(p)


def test_pdf_generate_without_charts_still_works(pdf_gen, sample_data):
    """include_charts=False 时 PDF 仍能正常生成"""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        out = f.name
    try:
        result = pdf_gen.generate(
            sample_data, output_path=out, config=ReportConfig(include_charts=False)
        )
        assert result == out
        assert os.path.exists(out)
    finally:
        if os.path.exists(out):
            os.unlink(out)


def test_pdf_charts_skipped_when_no_trend(pdf_gen):
    """无 trend 数据时趋势图不应导致崩溃"""
    data = {
        "summary": {
            "positive_count": 10,
            "neutral_count": 5,
            "negative_count": 2,
            "total_articles": 17,
            "total_comments": 30,
        }
    }
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        out = f.name
    try:
        result = pdf_gen.generate(
            data, output_path=out, config=ReportConfig(include_charts=True)
        )
        assert result == out
    finally:
        if os.path.exists(out):
            os.unlink(out)


# --- PPT 图表嵌入测试 ---


def test_ppt_generate_with_charts_returns_path(ppt_gen, sample_data):
    """PPT 生成含图表时应返回文件路径"""
    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as f:
        out = f.name
    try:
        result = ppt_gen.generate(
            sample_data, output_path=out, config=ReportConfig(include_charts=True)
        )
        assert result == out
        assert os.path.exists(out)
        assert os.path.getsize(out) > 0
    finally:
        if os.path.exists(out):
            os.unlink(out)


def test_ppt_with_charts_larger_than_without(ppt_gen, sample_data):
    """含图表的 PPT 应比不含图表的更大"""
    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as f:
        out_with = f.name
    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as f:
        out_without = f.name
    try:
        ppt_gen.generate(
            sample_data, output_path=out_with, config=ReportConfig(include_charts=True)
        )
        ppt_gen.generate(
            sample_data,
            output_path=out_without,
            config=ReportConfig(include_charts=False),
        )
        assert os.path.getsize(out_with) > os.path.getsize(out_without)
    finally:
        for p in (out_with, out_without):
            if os.path.exists(p):
                os.unlink(p)


def test_ppt_generate_without_charts_still_works(ppt_gen, sample_data):
    """include_charts=False 时 PPT 仍能正常生成"""
    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as f:
        out = f.name
    try:
        result = ppt_gen.generate(
            sample_data, output_path=out, config=ReportConfig(include_charts=False)
        )
        assert result == out
        assert os.path.exists(out)
    finally:
        if os.path.exists(out):
            os.unlink(out)


def test_ppt_charts_skipped_when_no_alerts(ppt_gen):
    """无 alerts 数据时预警图不应导致崩溃"""
    data = {
        "summary": {
            "positive_count": 10,
            "neutral_count": 5,
            "negative_count": 2,
            "total_articles": 17,
            "total_comments": 30,
        },
        "trend": [{"date": "2026-02-01", "count": 50}],
    }
    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as f:
        out = f.name
    try:
        result = ppt_gen.generate(
            data, output_path=out, config=ReportConfig(include_charts=True)
        )
        assert result == out
    finally:
        if os.path.exists(out):
            os.unlink(out)
