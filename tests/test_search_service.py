#!/usr/bin/env python3
"""
search_service.py 单元测试

search_service 是高级搜索服务模块，提供 FTS5 全文检索、LIKE 回退搜索、
搜索建议、拼音搜索能力，被多处 API 调用。

原 test_search_service.py 仅 19 个用例，覆盖率 81%，且存在两个问题：
1. **使用默认 db_path（生产 data/search.db），测试污染真实数据**
2. 多处弱断言（`assert len(results) >= 0` 永真）+ 未覆盖路径
   （clear_index / _fallback_search / to_dict / order_by=date /
   FTS 失败回退 / 高亮边界 / 作者建议分支）

测试策略：
- 用 tmp_path 隔离 SQLite 数据库，不触碰生产 search.db
- 覆盖所有公开方法 + 关键私有方法（_build_fts_query / _fallback_search
  / _extract_highlights）
- 触发 FTS 失败回退路径、拼音/数字/ASCII/标点混合输入、高亮边界
"""

import pytest

pytestmark = pytest.mark.unit

import os
import sqlite3
import sys
from datetime import datetime
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from services.search_service import (
    AdvancedSearchEngine,
    PinyinConverter,
    SearchResult,
    SearchSuggestion,
    advanced_search,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def engine(tmp_path):
    """每个测试用独立的临时 SQLite 数据库，隔离生产 data/search.db"""
    db_path = str(tmp_path / "test_search.db")
    return AdvancedSearchEngine(db_path=db_path)


@pytest.fixture
def populated_engine(engine):
    """预置 5 篇文档的搜索引擎，含不同 source_type / created_at"""
    engine.batch_index(
        [
            {
                "id": "1",
                "source_type": "article",
                "title": "人工智能发展趋势",
                "content": "深度学习和大模型推动AI快速发展",
                "author": "科技博主",
                "created_at": "2024-01-05T10:00:00",
            },
            {
                "id": "2",
                "source_type": "article",
                "title": "新能源汽车市场分析",
                "content": "电动汽车销量持续增长，市场份额扩大",
                "author": "汽车专家",
                "created_at": "2024-03-10T12:00:00",
            },
            {
                "id": "3",
                "source_type": "article",
                "title": "数字经济政策解读",
                "content": "国家出台多项政策支持数字经济发展",
                "author": "政策研究员",
                "created_at": "2024-02-15T08:30:00",
            },
            {
                "id": "4",
                "source_type": "alert",
                "title": "负面舆情预警",
                "content": "检测到大量负面评论，情感分数骤降",
                "author": "系统",
                "created_at": "2024-04-01T09:00:00",
            },
            {
                "id": "5",
                "source_type": "article",
                "title": "绿色发展与碳中和",
                "content": "碳排放目标推动绿色能源转型",
                "author": "环保专家",
                "created_at": "2024-01-20T14:00:00",
            },
        ]
    )
    return engine


@pytest.fixture
def multi_result_engine(engine):
    """预置 5 篇同前缀文档，用于分页/排序/过滤测试。

    FTS5 unicode61 不分词中文，prefix 查询 `"发展"*` 仅匹配以 "发展" 开头
    的 token，故用 "发展报告X" 统一前缀，搜索 "发展" 命中全部 5 篇。
    其中 r5 为 alert 类型，用于 source_type 过滤测试。
    """
    engine.batch_index(
        [
            {"id": "r1", "title": "发展报告甲", "content": "内容", "author": "a", "source_type": "article", "created_at": "2024-03-01T10:00:00"},
            {"id": "r2", "title": "发展报告乙", "content": "内容", "author": "b", "source_type": "article", "created_at": "2024-01-01T10:00:00"},
            {"id": "r3", "title": "发展报告丙", "content": "内容", "author": "c", "source_type": "article", "created_at": "2024-02-01T10:00:00"},
            {"id": "r4", "title": "发展报告丁", "content": "内容", "author": "d", "source_type": "article", "created_at": "2024-04-01T10:00:00"},
            {"id": "r5", "title": "发展报告戊", "content": "内容", "author": "e", "source_type": "alert", "created_at": "2024-05-01T10:00:00"},
        ]
    )
    return engine


# ---------------------------------------------------------------------------
# SearchResult.to_dict
# ---------------------------------------------------------------------------


class TestSearchResultToDict:
    """SearchResult.to_dict 序列化"""

    def test_short_content_preserved(self):
        """短内容（<=200）原样返回，不带省略号"""
        r = SearchResult(
            id="1", title="t", content="short", source_type="article",
            author="a", created_at="2024", score=1.0,
        )
        d = r.to_dict()
        assert d["content"] == "short"
        assert d["id"] == "1"
        assert d["title"] == "t"
        assert d["source_type"] == "article"
        assert d["author"] == "a"
        assert d["created_at"] == "2024"
        assert d["score"] == 1.0
        assert d["highlights"] == []

    def test_long_content_truncated_with_ellipsis(self):
        """长内容（>200）截断到 200 字符并加 '...' 后缀"""
        long_content = "x" * 300
        r = SearchResult(
            id="1", title="t", content=long_content, source_type="article",
            author="a", created_at="2024", score=0.5,
        )
        d = r.to_dict()
        assert len(d["content"]) == 203  # 200 + "..."
        assert d["content"].endswith("...")
        assert d["content"][:200] == "x" * 200

    def test_content_exactly_200_not_truncated(self):
        """恰好 200 字符不截断、不加省略号"""
        content = "y" * 200
        r = SearchResult(
            id="1", title="t", content=content, source_type="article",
            author="a", created_at="2024", score=1.0,
        )
        d = r.to_dict()
        assert d["content"] == content
        assert "..." not in d["content"]

    def test_highlights_serialized(self):
        """highlights 列表应原样序列化"""
        r = SearchResult(
            id="1", title="t", content="c", source_type="article",
            author="a", created_at="2024", score=1.0,
            highlights=["片段1", "片段2"],
        )
        assert r.to_dict()["highlights"] == ["片段1", "片段2"]


# ---------------------------------------------------------------------------
# SearchSuggestion.to_dict
# ---------------------------------------------------------------------------


class TestSearchSuggestionToDict:
    def test_to_dict_returns_all_fields(self):
        s = SearchSuggestion(text="AI", type="title", count=5)
        assert s.to_dict() == {"text": "AI", "type": "title", "count": 5}


# ---------------------------------------------------------------------------
# PinyinConverter.to_pinyin
# ---------------------------------------------------------------------------


class TestPinyinConverterToPinyin:
    """to_pinyin 取首字母"""

    def test_chinese_in_map_returns_first_letter(self):
        """映射表内的中文字符返回拼音首字母"""
        # 微=wei→w, 博=bo→b
        assert PinyinConverter().to_pinyin("微博") == "wb"

    def test_ascii_letters_lowercased(self):
        """ASCII 字母转小写"""
        assert PinyinConverter().to_pinyin("AI") == "ai"

    def test_digits_preserved(self):
        """数字字符原样保留"""
        assert PinyinConverter().to_pinyin("123") == "123"

    def test_mixed_chinese_ascii_digits(self):
        """中文+字母+数字混合"""
        # 微=w, A=a, I=i, 1=1, 2=2, 3=3
        assert PinyinConverter().to_pinyin("微AI123") == "wai123"

    def test_punctuation_skipped(self):
        """标点/空白等非字母非数字字符应被跳过"""
        assert PinyinConverter().to_pinyin("微, 博!") == "wb"

    def test_empty_string_returns_empty(self):
        assert PinyinConverter().to_pinyin("") == ""

    def test_unmapped_chinese_passed_through(self):
        """映射表外的中文字符（如'工'）因 isalpha() 为真，原样保留。

        注意：Python str.isalpha() 对中文字符返回 True，所以未映射的
        中文会走 elif char.isalpha() 分支，append char.lower()（对中文
        lower() 是 no-op）。这是一个容易误解的行为，本测试记录实际行为。
        """
        assert PinyinConverter().to_pinyin("工") == "工"


# ---------------------------------------------------------------------------
# PinyinConverter.to_full_pinyin
# ---------------------------------------------------------------------------


class TestPinyinConverterToFullPinyin:
    """to_full_pinyin 取完整拼音，空格分隔"""

    def test_chinese_in_map_returns_full_pinyin(self):
        assert PinyinConverter().to_full_pinyin("微博") == "wei bo"

    def test_ascii_letters_lowercased_and_space_joined(self):
        """ASCII 字母逐字符转小写，空格分隔"""
        # A→a, I→i → "a i"
        assert PinyinConverter().to_full_pinyin("AI") == "a i"

    def test_digits_preserved_and_space_joined(self):
        """数字逐字符保留，空格分隔"""
        assert PinyinConverter().to_full_pinyin("123") == "1 2 3"

    def test_mixed_chinese_ascii(self):
        """中文+字母混合"""
        # 微=wei, 博=bo, A=a, I=i → "wei bo a i"
        assert PinyinConverter().to_full_pinyin("微博AI") == "wei bo a i"

    def test_punctuation_skipped(self):
        """标点应被跳过"""
        assert PinyinConverter().to_full_pinyin("微!博?") == "wei bo"

    def test_empty_string_returns_empty(self):
        assert PinyinConverter().to_full_pinyin("") == ""


# ---------------------------------------------------------------------------
# PinyinConverter 映射表
# ---------------------------------------------------------------------------


class TestPinyinConverterMap:
    """_init_pinyin_map 映射表完整性"""

    def test_map_contains_known_entries(self):
        m = PinyinConverter()._pinyin_map
        assert m["微"] == "wei"
        assert m["博"] == "bo"
        assert m["舆"] == "yu"
        assert m["情"] == "qing"
        assert m["测"] == "ce"
        assert m["试"] == "shi"

    def test_map_values_are_lowercase_ascii(self):
        """所有拼音值应为小写 ASCII 字符串"""
        m = PinyinConverter()._pinyin_map
        for char, pinyin in m.items():
            assert pinyin.isascii(), f"{char!r} -> {pinyin!r} 不是 ASCII"
            assert pinyin.islower(), f"{char!r} -> {pinyin!r} 不是小写"
            assert len(pinyin) >= 1


# ---------------------------------------------------------------------------
# AdvancedSearchEngine 初始化
# ---------------------------------------------------------------------------


class TestInitDb:
    """_init_db 数据库初始化"""

    def test_creates_search_index_table(self, engine):
        with sqlite3.connect(engine.db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='search_index'"
            )
            assert cursor.fetchone() is not None

    def test_creates_search_fts_virtual_table(self, engine):
        with sqlite3.connect(engine.db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='search_fts'"
            )
            assert cursor.fetchone() is not None

    def test_creates_parent_directory(self, tmp_path):
        """db_path 的父目录不存在时应自动创建"""
        db_path = str(tmp_path / "nested" / "deep" / "test.db")
        eng = AdvancedSearchEngine(db_path=db_path)
        assert os.path.exists(os.path.dirname(db_path))
        # 验证引擎可用
        eng.index_document("d1", "title", "content")
        assert eng.get_stats()["total_documents"] == 1


# ---------------------------------------------------------------------------
# index_document
# ---------------------------------------------------------------------------


class TestIndexDocument:
    """单文档索引"""

    def test_index_single_document_searchable(self, engine):
        engine.index_document(
            doc_id="d1", title="测试标题", content="测试内容",
            source_type="article", author="作者",
        )
        results = engine.search("测试标题")
        assert any(r.id == "d1" for r in results)

    def test_default_source_type_is_article(self, engine):
        """source_type 默认 'article'"""
        engine.index_document("d1", "标题", "内容")
        results = engine.search("标题")
        assert results[0].source_type == "article"

    def test_default_created_at_is_now(self, engine):
        """created_at=None 时应使用当前 ISO 时间"""
        before = datetime.now().isoformat()
        engine.index_document("d1", "标题", "内容")
        with sqlite3.connect(engine.db_path) as conn:
            row = conn.execute(
                "SELECT created_at FROM search_index WHERE id=?", ("d1",)
            ).fetchone()
        assert row is not None
        assert row[0] >= before

    def test_replace_existing_document(self, engine):
        """相同 doc_id 应同时替换 search_index 与 search_fts。

        历史 bug：FTS5 虚拟表以 rowid 为主键，id 只是普通列，原 `INSERT OR
        REPLACE INTO search_fts` 按 rowid 匹配而非 id，重复插入会追加新条目，
        导致替换文档后旧标题仍可通过 FTS 搜到。修复方式：INSERT 前先
        `DELETE FROM search_fts WHERE id = ?`。本测试验证修复后旧标题不再可搜。
        """
        engine.index_document("d1", "旧标题", "旧内容")
        engine.index_document("d1", "新标题", "新内容")
        stats = engine.get_stats()
        # search_index 表正确替换（id 是 PRIMARY KEY）
        assert stats["total_documents"] == 1
        # 新标题可搜到
        results = engine.search("新标题")
        assert any(r.id == "d1" for r in results)
        # 修复后：旧标题不应再被搜到
        old_results = engine.search("旧标题")
        assert not any(r.id == "d1" for r in old_results)

    def test_replace_in_batch_index_clears_stale_fts(self, engine):
        """batch_index 重复索引相同 doc_id 也应清除旧 FTS 条目（同 index_document 修复）"""
        engine.index_document("d1", "批量旧标题", "旧内容")
        engine.batch_index(
            [{"id": "d1", "title": "批量新标题", "content": "新内容"}]
        )
        new_results = engine.search("批量新标题")
        assert any(r.id == "d1" for r in new_results)
        old_results = engine.search("批量旧标题")
        assert not any(r.id == "d1" for r in old_results)

    def test_pinyin_columns_populated(self, engine):
        """索引时应填充 pinyin_title / pinyin_content 列"""
        engine.index_document(
            "d1", title="微博", content="舆情分析", author="a"
        )
        with sqlite3.connect(engine.db_path) as conn:
            row = conn.execute(
                "SELECT pinyin_title, pinyin_content FROM search_index WHERE id=?",
                ("d1",),
            ).fetchone()
        assert row[0] == "wei bo"
        assert row[1] == "yu qing fen xi"


# ---------------------------------------------------------------------------
# batch_index
# ---------------------------------------------------------------------------


class TestBatchIndex:
    """批量索引"""

    def test_indexes_multiple_documents(self, engine):
        engine.batch_index([
            {"id": "1", "title": "标题一", "content": "内容一", "author": "a"},
            {"id": "2", "title": "标题二", "content": "内容二", "author": "b"},
        ])
        assert engine.get_stats()["total_documents"] == 2

    def test_defaults_for_missing_fields(self, engine):
        """缺少 source_type / author / created_at 时应使用默认值"""
        engine.batch_index([{"id": "1", "title": "t", "content": "c"}])
        with sqlite3.connect(engine.db_path) as conn:
            row = conn.execute(
                "SELECT source_type, author, created_at FROM search_index WHERE id=?",
                ("1",),
            ).fetchone()
        assert row[0] == "article"
        assert row[1] == ""
        assert row[2] is not None  # ISO 时间戳

    def test_logs_completion(self, engine, caplog):
        """批量索引完成应记 info 日志"""
        import logging

        with caplog.at_level(logging.INFO, logger="services.search_service"):
            engine.batch_index([{"id": "1", "title": "t", "content": "c"}])
        assert any(
            "批量索引完成" in r.getMessage() and "1 条" in r.getMessage()
            for r in caplog.records
        )

    def test_empty_batch_no_error(self, engine):
        """空列表不应抛错"""
        engine.batch_index([])
        assert engine.get_stats()["total_documents"] == 0


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


class TestSearch:
    """FTS5 全文检索"""

    def test_search_returns_results(self, populated_engine):
        results = populated_engine.search("人工智能")
        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)

    def test_search_matches_title(self, populated_engine):
        results = populated_engine.search("新能源")
        ids = [r.id for r in results]
        assert "2" in ids

    def test_search_matches_content(self, populated_engine):
        results = populated_engine.search("深度学习")
        ids = [r.id for r in results]
        assert "1" in ids

    def test_search_no_match_returns_empty(self, populated_engine):
        results = populated_engine.search("量子计算机芯片不存在")
        assert results == []

    def test_search_filter_by_source_type(self, multi_result_engine):
        """source_type 过滤应只返回匹配类型（排除 alert）"""
        results = multi_result_engine.search("发展", source_type="article")
        assert len(results) > 0
        assert all(r.source_type == "article" for r in results)
        assert all(r.id != "r5" for r in results)  # r5 是 alert

    def test_search_result_has_non_negative_score(self, populated_engine):
        results = populated_engine.search("人工智能")
        assert all(r.score >= 0 for r in results)

    def test_search_limit(self, multi_result_engine):
        results = multi_result_engine.search("发展", limit=2)
        assert len(results) == 2

    def test_search_offset_pagination(self, multi_result_engine):
        """offset 分页：第二页应与第一页不重叠"""
        page1 = multi_result_engine.search("发展", limit=2, offset=0)
        page2 = multi_result_engine.search("发展", limit=2, offset=2)
        assert len(page1) == 2
        ids1 = {r.id for r in page1}
        ids2 = {r.id for r in page2}
        assert ids1.isdisjoint(ids2)

    def test_search_order_by_relevance(self, multi_result_engine):
        """order_by='relevance' 应按 FTS rank 排序"""
        results = multi_result_engine.search("发展", order_by="relevance")
        assert len(results) > 0
        scores = [r.score for r in results]
        # relevance 模式下 score 来自 FTS rank，按升序（更负 = 更相关）
        assert scores == sorted(scores)

    def test_search_order_by_date_desc(self, multi_result_engine):
        """order_by='date' 应按 created_at 降序"""
        results = multi_result_engine.search("发展", order_by="date")
        assert len(results) > 0
        dates = [r.created_at for r in results]
        assert dates == sorted(dates, reverse=True)

    def test_search_unknown_order_by_no_ordering(self, multi_result_engine):
        """未知 order_by 值不追加 ORDER BY（不抛错即可）"""
        results = multi_result_engine.search("发展", order_by="unknown")
        assert len(results) > 0  # 结果返回正常

    def test_search_includes_highlights(self, populated_engine):
        """搜索结果应包含高亮片段（当查询词长度 >= 2 时）"""
        results = populated_engine.search("深度学习")
        # 至少有一个结果带高亮
        assert any(len(r.highlights) > 0 for r in results)

    def test_search_falls_back_when_fts_table_missing(self, populated_engine):
        """FTS 表缺失触发 OperationalError → 回退到 LIKE 搜索"""
        with sqlite3.connect(populated_engine.db_path) as conn:
            conn.execute("DROP TABLE search_fts")
            conn.commit()

        with patch.object(
            populated_engine, "_fallback_search", wraps=populated_engine._fallback_search
        ) as mock_fb:
            results = populated_engine.search("人工智能")

        mock_fb.assert_called_once()
        assert any(r.id == "1" for r in results)
        # 回退搜索的 score 固定为 1.0
        assert all(r.score == 1.0 for r in results)


# ---------------------------------------------------------------------------
# _build_fts_query
# ---------------------------------------------------------------------------


class TestBuildFtsQuery:
    """FTS 查询构造"""

    def test_empty_query_returns_star(self, engine):
        assert engine._build_fts_query("") == "*"

    def test_whitespace_query_returns_star(self, engine):
        assert engine._build_fts_query("   ") == "*"

    def test_single_word_quoted_with_prefix_wildcard(self, engine):
        assert engine._build_fts_query("hello") == '"hello"*'

    def test_multiple_words_joined_by_or(self, engine):
        result = engine._build_fts_query("hello world")
        assert result == '"hello"* OR "world"*'

    def test_chinese_single_word(self, engine):
        assert engine._build_fts_query("人工智能") == '"人工智能"*'


# ---------------------------------------------------------------------------
# _fallback_search
# ---------------------------------------------------------------------------


class TestFallbackSearch:
    """LIKE 回退搜索"""

    def test_fallback_matches_title(self, populated_engine):
        results = populated_engine._fallback_search("人工智能", 20, 0)
        assert any(r.id == "1" for r in results)

    def test_fallback_matches_content(self, populated_engine):
        results = populated_engine._fallback_search("深度学习", 20, 0)
        assert any(r.id == "1" for r in results)

    def test_fallback_filter_by_source_type(self, populated_engine):
        results = populated_engine._fallback_search("发展", 20, 0, source_type="article")
        assert all(r.source_type == "article" for r in results)

    def test_fallback_no_match_returns_empty(self, populated_engine):
        results = populated_engine._fallback_search("不存在的词xyz", 20, 0)
        assert results == []

    def test_fallback_score_always_one(self, populated_engine):
        """回退搜索的 score 固定为 1.0"""
        results = populated_engine._fallback_search("发展", 20, 0)
        assert all(r.score == 1.0 for r in results)

    def test_fallback_respects_limit_and_offset(self, populated_engine):
        page1 = populated_engine._fallback_search("发展", 2, 0)
        page2 = populated_engine._fallback_search("发展", 2, 2)
        assert len(page1) <= 2
        ids1 = {r.id for r in page1}
        ids2 = {r.id for r in page2}
        assert ids1.isdisjoint(ids2)

    def test_fallback_matches_pinyin_column(self, populated_engine):
        """LIKE 回退应匹配 pinyin_title / pinyin_content 列"""
        # doc 1 title="人工智能发展趋势", pinyin 含 "ren"
        results = populated_engine._fallback_search("ren", 20, 0)
        assert any(r.id == "1" for r in results)


# ---------------------------------------------------------------------------
# _extract_highlights
# ---------------------------------------------------------------------------


class TestExtractHighlights:
    """高亮片段提取"""

    def test_word_found_at_start_no_prefix_ellipsis(self, engine):
        """词在内容开头：不加前缀省略号"""
        content = "深度学习很重要"
        highlights = engine._extract_highlights(content, "深度学习")
        assert len(highlights) == 1
        assert "深度学习" in highlights[0]
        # start=0，不加 "..." 前缀
        assert not highlights[0].startswith("...")

    def test_word_found_in_middle_adds_both_ellipsis(self, engine):
        """词在内容中间：加前后省略号"""
        content = "x" * 100 + "深度学习" + "y" * 100
        highlights = engine._extract_highlights(content, "深度学习")
        assert len(highlights) == 1
        assert highlights[0].startswith("...")
        assert highlights[0].endswith("...")
        assert "深度学习" in highlights[0]

    def test_short_word_skipped(self, engine):
        """长度 < 2 的词应被跳过"""
        highlights = engine._extract_highlights("a 在内容中", "a")
        assert highlights == []

    def test_word_not_found_no_highlight(self, engine):
        """未命中的词不产生高亮"""
        highlights = engine._extract_highlights("这是内容", "不存在的词")
        assert highlights == []

    def test_max_three_highlights(self, engine):
        """最多 3 条高亮（3 条后 break）"""
        content = "apple banana cherry date"
        highlights = engine._extract_highlights(
            content, "apple banana cherry date"
        )
        assert len(highlights) == 3

    def test_empty_query_no_highlights(self, engine):
        highlights = engine._extract_highlights("内容", "")
        assert highlights == []

    def test_multiple_words_multiple_highlights(self, engine):
        """多个词各产生一条高亮"""
        content = "apple orange banana"
        highlights = engine._extract_highlights(content, "apple orange")
        assert len(highlights) == 2


# ---------------------------------------------------------------------------
# get_suggestions
# ---------------------------------------------------------------------------


class TestGetSuggestions:
    """搜索建议"""

    def test_title_prefix_matches(self, populated_engine):
        suggestions = populated_engine.get_suggestions("人工")
        texts = [s.text for s in suggestions]
        assert any("人工智能" in t for t in texts)
        assert all(isinstance(s, SearchSuggestion) for s in suggestions)

    def test_empty_prefix_returns_empty(self, populated_engine):
        suggestions = populated_engine.get_suggestions("")
        assert suggestions == []

    def test_respects_limit(self, populated_engine):
        suggestions = populated_engine.get_suggestions("发", limit=2)
        assert len(suggestions) <= 2

    def test_title_suggestions_have_correct_type(self, populated_engine):
        suggestions = populated_engine.get_suggestions("人工")
        title_suggestions = [s for s in suggestions if s.type == "title"]
        assert len(title_suggestions) > 0

    def test_author_suggestion_branch_when_title_misses(self, populated_engine):
        """当 title 前缀无匹配、author 前缀有匹配时，应返回 author 建议。

        前缀 '科' 不匹配任何 title，但匹配 author '科技博主'。
        """
        suggestions = populated_engine.get_suggestions("科")
        authors = [s for s in suggestions if s.type == "author"]
        assert any(s.text == "科技博主" for s in authors)

    def test_author_branch_skipped_when_title_fills_limit(self, populated_engine):
        """limit=1 且 title 已匹配 1 条时，author 分支不执行（1 < 1 为 False）"""
        suggestions = populated_engine.get_suggestions("新", limit=1)
        # 只应有 title 建议，无 author 建议
        assert all(s.type == "title" for s in suggestions)
        assert len(suggestions) <= 1

    def test_suggestion_to_dict(self, populated_engine):
        """建议对象应可正确序列化"""
        suggestions = populated_engine.get_suggestions("人工")
        for s in suggestions:
            d = s.to_dict()
            assert "text" in d and "type" in d and "count" in d


# ---------------------------------------------------------------------------
# search_by_pinyin
# ---------------------------------------------------------------------------


class TestSearchByPinyin:
    """拼音搜索"""

    @pytest.fixture
    def pinyin_engine(self, engine):
        """预置拼音可预测的文档（全映射字符）"""
        engine.index_document(
            doc_id="p1",
            title="微博舆情分析",
            content="系统测试用户",
            source_type="article",
            author="测试员",
        )
        # pinyin_title = "wei bo yu qing fen xi"
        # pinyin_content = "xi tong ce shi yong hu"
        return engine

    def test_search_by_pinyin_title_substring(self, pinyin_engine):
        """拼音子串匹配 title"""
        results = pinyin_engine.search_by_pinyin("wei")
        assert any(r.id == "p1" for r in results)

    def test_search_by_pinyin_content_substring(self, pinyin_engine):
        """拼音子串匹配 content"""
        results = pinyin_engine.search_by_pinyin("ce shi")
        assert any(r.id == "p1" for r in results)

    def test_search_by_pinyin_no_match(self, pinyin_engine):
        results = pinyin_engine.search_by_pinyin("xyz")
        assert results == []

    def test_search_by_pinyin_respects_limit(self, pinyin_engine):
        results = pinyin_engine.search_by_pinyin("wei", limit=0)
        assert len(results) == 0

    def test_search_by_pinyin_returns_search_result_instances(self, pinyin_engine):
        results = pinyin_engine.search_by_pinyin("wei")
        assert all(isinstance(r, SearchResult) for r in results)
        assert all(r.score == 1.0 for r in results)


# ---------------------------------------------------------------------------
# get_stats
# ---------------------------------------------------------------------------


class TestGetStats:
    """索引统计"""

    def test_empty_index_stats(self, engine):
        stats = engine.get_stats()
        assert stats == {
            "total_documents": 0,
            "source_types": 0,
            "unique_authors": 0,
        }

    def test_populated_stats(self, populated_engine):
        stats = populated_engine.get_stats()
        assert stats["total_documents"] == 5
        # source_type: article + alert = 2
        assert stats["source_types"] == 2
        # 5 个不同作者
        assert stats["unique_authors"] == 5


# ---------------------------------------------------------------------------
# clear_index
# ---------------------------------------------------------------------------


class TestClearIndex:
    """清空索引"""

    def test_clear_removes_all_documents(self, populated_engine):
        assert populated_engine.get_stats()["total_documents"] == 5
        populated_engine.clear_index()
        assert populated_engine.get_stats()["total_documents"] == 0

    def test_clear_removes_from_fts_table(self, populated_engine):
        """清空后 FTS 表也应清空，搜索无结果"""
        populated_engine.clear_index()
        results = populated_engine.search("人工智能")
        assert results == []

    def test_clear_then_reindex(self, populated_engine):
        """清空后可重新索引"""
        populated_engine.clear_index()
        populated_engine.index_document("new", "新标题", "新内容")
        assert populated_engine.get_stats()["total_documents"] == 1
        assert any(r.id == "new" for r in populated_engine.search("新标题"))


# ---------------------------------------------------------------------------
# remove_document
# ---------------------------------------------------------------------------


class TestRemoveDocument:
    """删除单个文档"""

    def test_remove_makes_unsearchable(self, populated_engine):
        populated_engine.remove_document("1")
        results = populated_engine.search("人工智能")
        assert not any(r.id == "1" for r in results)

    def test_remove_decrements_count(self, populated_engine):
        assert populated_engine.get_stats()["total_documents"] == 5
        populated_engine.remove_document("1")
        assert populated_engine.get_stats()["total_documents"] == 4

    def test_remove_nonexistent_id_no_error(self, populated_engine):
        """删除不存在的 id 不应抛错"""
        populated_engine.remove_document("nonexistent")
        assert populated_engine.get_stats()["total_documents"] == 5

    def test_remove_from_fts_table(self, populated_engine):
        """删除应同时从 FTS 表移除"""
        populated_engine.remove_document("1")
        with sqlite3.connect(populated_engine.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM search_fts WHERE id=?", ("1",)
            )
            assert cursor.fetchone()[0] == 0


# ---------------------------------------------------------------------------
# 模块级单例
# ---------------------------------------------------------------------------


class TestModuleSingleton:
    """advanced_search 单例"""

    def test_singleton_is_engine_instance(self):
        assert isinstance(advanced_search, AdvancedSearchEngine)

    def test_singleton_has_pinyin_converter(self):
        assert isinstance(advanced_search.pinyin, PinyinConverter)
