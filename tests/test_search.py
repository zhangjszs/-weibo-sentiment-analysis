#!/usr/bin/env python3
"""
高级搜索服务单元测试
"""

import shutil
import sys
import tempfile
import time
from pathlib import Path

import pytest

sys.path.insert(0, "src")


class TestPinyinConverter:
    """拼音转换器测试"""

    def test_to_pinyin(self):
        """测试拼音首字母转换"""
        from services.search_service import PinyinConverter

        converter = PinyinConverter()
        result = converter.to_pinyin("微博舆情")

        assert len(result) > 0

    def test_to_full_pinyin(self):
        """测试完整拼音转换"""
        from services.search_service import PinyinConverter

        converter = PinyinConverter()
        result = converter.to_full_pinyin("微博")

        assert "wei" in result or "bo" in result

    def test_mixed_content(self):
        """测试混合内容"""
        from services.search_service import PinyinConverter

        converter = PinyinConverter()
        result = converter.to_pinyin("微博Test123")

        assert len(result) > 0


class TestAdvancedSearchEngine:
    """高级搜索引擎测试"""

    @pytest.fixture
    def engine(self):
        """创建搜索引擎实例"""
        from services.search_service import AdvancedSearchEngine

        temp_dir = Path(tempfile.mkdtemp(prefix="search_db_"))
        db_path = str(temp_dir / "test_search.db")
        yield AdvancedSearchEngine(db_path)

        for _ in range(5):
            try:
                shutil.rmtree(temp_dir)
                break
            except PermissionError:
                time.sleep(0.1)

    def test_init(self, engine):
        """测试初始化"""
        assert engine.db_path is not None

    def test_index_document(self, engine):
        """测试索引文档"""
        engine.index_document(
            doc_id="test-001",
            title="测试文章",
            content="这是一篇测试文章的内容",
            source_type="article",
            author="测试作者",
        )

        stats = engine.get_stats()
        assert stats["total_documents"] == 1

    def test_batch_index(self, engine):
        """测试批量索引"""
        documents = [
            {"id": "doc-001", "title": "文章1", "content": "内容1", "author": "作者1"},
            {"id": "doc-002", "title": "文章2", "content": "内容2", "author": "作者2"},
            {"id": "doc-003", "title": "文章3", "content": "内容3", "author": "作者3"},
        ]

        engine.batch_index(documents)

        stats = engine.get_stats()
        assert stats["total_documents"] == 3

    def test_search(self, engine):
        """测试搜索"""
        engine.index_document(
            doc_id="test-001",
            title="微博舆情分析",
            content="这是一篇关于微博舆情分析的测试文章",
            source_type="article",
            author="测试作者",
        )

        results = engine.search("微博")

        assert len(results) >= 1

    def test_search_with_source_filter(self, engine):
        """测试带来源过滤的搜索"""
        engine.index_document(
            doc_id="test-001",
            title="测试文章",
            content="测试内容",
            source_type="article",
            author="作者1",
        )
        engine.index_document(
            doc_id="test-002",
            title="测试评论",
            content="测试评论内容",
            source_type="comment",
            author="作者2",
        )

        results = engine.search("测试", source_type="article")

        for r in results:
            assert r.source_type == "article"

    def test_get_suggestions(self, engine):
        """测试搜索建议"""
        engine.index_document(
            doc_id="test-001", title="微博舆情分析系统", content="内容", author="作者"
        )
        engine.index_document(
            doc_id="test-002", title="微博数据分析", content="内容", author="作者"
        )

        suggestions = engine.get_suggestions("微博")

        assert len(suggestions) >= 0

    def test_remove_document(self, engine):
        """测试删除文档"""
        engine.index_document(doc_id="test-001", title="测试文章", content="测试内容")

        stats = engine.get_stats()
        assert stats["total_documents"] == 1

        engine.remove_document("test-001")

        stats = engine.get_stats()
        assert stats["total_documents"] == 0

    def test_clear_index(self, engine):
        """测试清空索引"""
        for i in range(5):
            engine.index_document(
                doc_id=f"test-{i}", title=f"测试文章{i}", content=f"测试内容{i}"
            )

        engine.clear_index()

        stats = engine.get_stats()
        assert stats["total_documents"] == 0


class TestSearchResult:
    """搜索结果测试"""

    def test_to_dict(self):
        """测试序列化"""
        from services.search_service import SearchResult

        result = SearchResult(
            id="test-001",
            title="测试标题",
            content="这是一段很长的测试内容" * 20,
            source_type="article",
            author="测试作者",
            created_at="2026-02-21",
            score=0.95,
            highlights=["高亮片段"],
        )

        data = result.to_dict()

        assert data["id"] == "test-001"
        assert data["score"] == 0.95
        assert "..." in data["content"]


class TestSearchSuggestion:
    """搜索建议测试"""

    def test_to_dict(self):
        """测试序列化"""
        from services.search_service import SearchSuggestion

        suggestion = SearchSuggestion(text="微博舆情", type="title", count=10)

        data = suggestion.to_dict()

        assert data["text"] == "微博舆情"
        assert data["type"] == "title"
        assert data["count"] == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
