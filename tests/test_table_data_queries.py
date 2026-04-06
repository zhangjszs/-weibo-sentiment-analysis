#!/usr/bin/env python3
"""
表格数据查询优化测试
"""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_article_table_sentiment_rows_do_not_full_scan(monkeypatch):
    import utils.getPublicData as public_data
    import utils.getTableData as table_data
    from services.sentiment_service import SentimentService

    monkeypatch.setattr(
        public_data,
        "getAllData",
        lambda: (_ for _ in ()).throw(AssertionError("should not load full article rows")),
    )
    monkeypatch.setattr(
        table_data,
        "SnowNLP",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not analyze row by row")),
    )

    monkeypatch.setattr(
        table_data,
        "query_dataframe",
        lambda sql, params=None: pd.DataFrame(
            [
                {
                    "id": "a1",
                    "likeNum": 10,
                    "commentsLen": 2,
                    "reposts_count": 1,
                    "region": "北京",
                    "content": "很好",
                    "content_len": 2,
                    "created_at": "2026-03-20 10:00:00",
                    "type": "news",
                    "detailUrl": "https://example.com/1",
                    "authorName": "作者A",
                    "authorDetail": "详情A",
                    "isVip": 1,
                    "vipLevel": 3,
                },
                {
                    "id": "a2",
                    "likeNum": 5,
                    "commentsLen": 1,
                    "reposts_count": 0,
                    "region": "上海",
                    "content": "一般",
                    "content_len": 2,
                    "created_at": "2026-03-19 09:00:00",
                    "type": "blog",
                    "detailUrl": "https://example.com/2",
                    "authorName": "作者B",
                    "authorDetail": "详情B",
                    "isVip": 0,
                    "vipLevel": 0,
                },
            ]
        ),
    )
    monkeypatch.setattr(
        SentimentService,
        "analyze_batch",
        lambda texts, mode="simple": [
            {"label": "positive", "score": 0.9},
            {"label": "neutral", "score": 0.5},
        ],
    )

    rows = table_data.getTableDataArticle(True)

    assert rows[0][0] == "a1"
    assert rows[0][-1] == "正面"
    assert rows[1][-1] == "中性"
