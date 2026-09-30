#!/usr/bin/env python3
"""
表格数据查询优化测试

#14 重构后，utils.getTableData 不再经过 utils.query_dataframe 裸 SQL，
而是委托 ArticleRepository.find_with_filter（#30：旧测试 patch 的
query_dataframe 符号已不存在）。patch 点相应改为 Repository 方法，
测试意图不变：断言表格路径不做全表扫描、不做逐行情感分析。
"""

import pytest

pytestmark = pytest.mark.integration


def _forbid(monkeypatch, module, name, message):
    monkeypatch.setattr(
        module, name, lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError(message))
    )


def test_article_table_sentiment_rows_do_not_full_scan(monkeypatch):
    import utils.getPublicData as public_data
    import utils.getTableData as table_data
    from repositories.article_repository import ArticleRepository
    from services.sentiment_service import SentimentService

    # 双重守卫：public_data 命名空间的 getAllData，以及 getTableData 模块
    # 顶层 `from utils.getPublicData import getAllData` 带入的降级路径别名
    _forbid(monkeypatch, public_data, "getAllData", "should not load full article rows")
    _forbid(monkeypatch, table_data, "getAllData", "should not fallback to full article rows")
    _forbid(monkeypatch, table_data, "SnowNLP", "should not analyze row by row")

    monkeypatch.setattr(
        ArticleRepository,
        "find_with_filter",
        lambda self, **kwargs: (
            [
                {
                    "id": "a1",
                    "likeNum": 10,
                    "commentsLen": 2,
                    "reposts_count": 1,
                    "region": "北京",
                    "content": "很好",
                    "contentLen": 2,
                    "created_at": "2026-03-20 10:00:00",
                    "type": "news",
                    "detailUrl": "https://example.com/1",
                    "authorName": "作者A",
                    "authorDetail": "详情A",
                    "isVip": 1,
                },
                {
                    "id": "a2",
                    "likeNum": 5,
                    "commentsLen": 1,
                    "reposts_count": 0,
                    "region": "上海",
                    "content": "一般",
                    "contentLen": 2,
                    "created_at": "2026-03-19 09:00:00",
                    "type": "blog",
                    "detailUrl": "https://example.com/2",
                    "authorName": "作者B",
                    "authorDetail": "详情B",
                    "isVip": 0,
                },
            ],
            2,
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
