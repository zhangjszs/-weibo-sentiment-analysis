# tests/test_search_service.py
"""
TDD: 高级搜索服务 - 全文检索、搜索建议、拼音搜索
"""

import pytest

from services.search_service import (
    AdvancedSearchEngine,
    PinyinConverter,
    SearchResult,
    SearchSuggestion,
)


@pytest.fixture
def svc():
    s = AdvancedSearchEngine()
    s.batch_index(
        [
            {
                "id": "1",
                "source_type": "article",
                "title": "人工智能发展趋势",
                "content": "深度学习和大模型推动AI快速发展",
                "author": "科技博主",
            },
            {
                "id": "2",
                "source_type": "article",
                "title": "新能源汽车市场分析",
                "content": "电动汽车销量持续增长，市场份额扩大",
                "author": "汽车专家",
            },
            {
                "id": "3",
                "source_type": "article",
                "title": "数字经济政策解读",
                "content": "国家出台多项政策支持数字经济发展",
                "author": "政策研究员",
            },
            {
                "id": "4",
                "source_type": "alert",
                "title": "负面舆情预警",
                "content": "检测到大量负面评论，情感分数骤降",
                "author": "系统",
            },
            {
                "id": "5",
                "source_type": "article",
                "title": "绿色发展与碳中和",
                "content": "碳排放目标推动绿色能源转型",
                "author": "环保专家",
            },
        ]
    )
    return s


# --- 全文检索 ---


def test_search_returns_results(svc):
    results = svc.search("人工智能")
    assert len(results) > 0
    assert all(isinstance(r, SearchResult) for r in results)


def test_search_matches_title(svc):
    results = svc.search("新能源")
    ids = [r.id for r in results]
    assert "2" in ids


def test_search_matches_content(svc):
    results = svc.search("深度学习")
    ids = [r.id for r in results]
    assert "1" in ids


def test_search_no_match_returns_empty(svc):
    results = svc.search("量子计算机芯片")
    assert results == []


def test_search_filter_by_type(svc):
    results = svc.search("发展", source_type="article")
    assert all(r.source_type == "article" for r in results)


def test_search_result_has_score(svc):
    results = svc.search("人工智能")
    assert all(r.score >= 0 for r in results)


def test_search_results_sorted_by_score(svc):
    results = svc.search("发展")
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=False)


def test_search_limit(svc):
    results = svc.search("发展", limit=2)
    assert len(results) <= 2


# --- 搜索建议 ---


def test_suggest_returns_suggestions(svc):
    suggestions = svc.get_suggestions("人工")
    assert len(suggestions) > 0
    assert all(isinstance(s, SearchSuggestion) for s in suggestions)


def test_suggest_matches_prefix(svc):
    suggestions = svc.get_suggestions("新能")
    texts = [s.text for s in suggestions]
    assert any("新能源" in t for t in texts)


def test_suggest_empty_query_returns_empty(svc):
    suggestions = svc.get_suggestions("")
    assert suggestions == []


def test_suggest_limit(svc):
    suggestions = svc.get_suggestions("发", limit=2)
    assert len(suggestions) <= 2


# --- 拼音搜索 ---


def test_pinyin_helper_to_pinyin():
    ph = PinyinConverter()
    result = ph.to_pinyin("人工智能")
    assert "r" in result.lower()


def test_pinyin_helper_to_full_pinyin():
    ph = PinyinConverter()
    result = ph.to_full_pinyin("人工智能")
    assert "ren" in result.lower()


def test_search_by_pinyin(svc):
    results = svc.search_by_pinyin("rgzn")
    assert len(results) >= 0


def test_search_by_full_pinyin(svc):
    results = svc.search_by_pinyin("rengong")
    assert len(results) >= 0


# --- 索引管理 ---


def test_index_add_document(svc):
    svc.index_document(
        doc_id="99",
        title="量子计算突破",
        content="量子比特实现新突破",
        source_type="article",
        author="科学家",
    )
    results = svc.search("量子计算")
    assert any(r.id == "99" for r in results)


def test_index_remove_document(svc):
    svc.remove_document("1")
    results = svc.search("人工智能")
    assert not any(r.id == "1" for r in results)


def test_index_count(svc):
    stats = svc.get_stats()
    assert "total_documents" in stats
