#!/usr/bin/env python3
"""
旧版模板页面回归测试
"""

import os
import sys

import pytest
from flask import Flask

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture
def page_client():
    from views.page.page import pb

    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.register_blueprint(pb)
    client = app.test_client()
    with client.session_transaction() as session:
        session["username"] = "tester"
    return client


def test_page_table_data_uses_sentiment_service(page_client, monkeypatch):
    import services.sentiment_service as sentiment_service
    import views.page.page as page_module

    monkeypatch.setattr(page_module.getTableData, "getTableDataPageData", lambda: [["微博", 3]])
    monkeypatch.setattr(page_module.getTableData, "getTableData", lambda hot_word: [])
    monkeypatch.setattr(page_module.getTableData, "getTableDataEchartsData", lambda hot_word: ([], []))
    monkeypatch.setattr(
        sentiment_service.SentimentService,
        "analyze",
        lambda text, mode="simple": {"label": "positive", "score": 0.9},
    )

    response = page_client.get("/page/tableData")

    assert response.status_code == 200
    assert "热词情感：正面" in response.get_data(as_text=True)


def test_page_table_data_article_parses_false_flag(page_client, monkeypatch):
    import views.page.page as page_module

    seen_flags = []
    monkeypatch.setattr(
        page_module.getTableData,
        "getTableDataArticle",
        lambda flag: seen_flags.append(flag) or [],
    )

    response = page_client.get("/page/tableDataArticle?flag=false")

    assert response.status_code == 200
    assert seen_flags == [False]
