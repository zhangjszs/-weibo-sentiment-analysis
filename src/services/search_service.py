#!/usr/bin/env python3
"""
高级搜索服务模块
功能：全文检索、搜索建议、拼音搜索支持
"""

import logging
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """搜索结果"""

    id: str
    title: str
    content: str
    source_type: str
    author: str
    created_at: str
    score: float
    highlights: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content[:200] + "..."
            if len(self.content) > 200
            else self.content,
            "source_type": self.source_type,
            "author": self.author,
            "created_at": self.created_at,
            "score": self.score,
            "highlights": self.highlights,
        }


@dataclass
class SearchSuggestion:
    """搜索建议"""

    text: str
    type: str
    count: int

    def to_dict(self) -> Dict:
        return {"text": self.text, "type": self.type, "count": self.count}


class PinyinConverter:
    """拼音转换器（简化版）"""

    def __init__(self):
        self._pinyin_map = self._init_pinyin_map()

    def _init_pinyin_map(self) -> Dict[str, str]:
        """初始化拼音映射表"""
        return {
            "微": "wei",
            "博": "bo",
            "舆": "yu",
            "情": "qing",
            "分": "fen",
            "析": "xi",
            "系": "xi",
            "统": "tong",
            "测": "ce",
            "试": "shi",
            "用": "yong",
            "户": "hu",
            "评": "ping",
            "论": "lun",
            "关": "guan",
            "键": "jian",
            "词": "ci",
            "搜": "sou",
            "索": "suo",
            "数": "shu",
            "据": "ju",
            "展": "zhan",
            "示": "shi",
            "图": "tu",
            "表": "biao",
            "热": "re",
            "点": "dian",
            "话": "hua",
            "题": "ti",
            "新": "xin",
            "闻": "wen",
            "报": "bao",
            "道": "dao",
            "转": "zhuan",
            "发": "fa",
            "赞": "zan",
            "正": "zheng",
            "负": "fu",
            "面": "mian",
            "中": "zhong",
            "性": "xing",
            "北": "bei",
            "京": "jing",
            "上": "shang",
            "海": "hai",
            "广": "guang",
            "州": "zhou",
            "深": "shen",
            "圳": "zhen",
            "杭": "hang",
            "南": "nan",
            "东": "dong",
            "西": "xi",
            "好": "hao",
            "坏": "huai",
            "是": "shi",
            "不": "bu",
            "有": "you",
            "无": "wu",
            "大": "da",
            "小": "xiao",
            "多": "duo",
            "少": "shao",
            "高": "gao",
            "低": "di",
            "快": "kuai",
            "慢": "man",
            "人": "ren",
            "事": "shi",
            "物": "wu",
        }

    def to_pinyin(self, text: str) -> str:
        """转换为拼音首字母"""
        result = []
        for char in text:
            if char in self._pinyin_map:
                result.append(self._pinyin_map[char][0])
            elif char.isalpha():
                result.append(char.lower())
            elif char.isdigit():
                result.append(char)
        return "".join(result)

    def to_full_pinyin(self, text: str) -> str:
        """转换为完整拼音"""
        result = []
        for char in text:
            if char in self._pinyin_map:
                result.append(self._pinyin_map[char])
            elif char.isalpha():
                result.append(char.lower())
            elif char.isdigit():
                result.append(char)
        return " ".join(result)


class AdvancedSearchEngine:
    """高级搜索引擎"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(
            Path(__file__).parent.parent.parent / "data" / "search.db"
        )
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.pinyin = PinyinConverter()
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """初始化搜索数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS search_index (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    content TEXT,
                    source_type TEXT,
                    author TEXT,
                    created_at TEXT,
                    pinyin_title TEXT,
                    pinyin_content TEXT
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_content ON search_index(content)
            """)

            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS search_fts USING fts5(
                    id, title, content, author,
                    tokenize='unicode61'
                )
            """)

            conn.commit()

    def index_document(
        self,
        doc_id: str,
        title: str,
        content: str,
        source_type: str = "article",
        author: str = "",
        created_at: str = None,
    ):
        """索引文档"""
        if created_at is None:
            created_at = datetime.now().isoformat()

        pinyin_title = self.pinyin.to_full_pinyin(title)
        pinyin_content = self.pinyin.to_full_pinyin(content)

        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO search_index
                    (id, title, content, source_type, author, created_at, pinyin_title, pinyin_content)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        doc_id,
                        title,
                        content,
                        source_type,
                        author,
                        created_at,
                        pinyin_title,
                        pinyin_content,
                    ),
                )

                conn.execute(
                    """
                    INSERT OR REPLACE INTO search_fts (id, title, content, author)
                    VALUES (?, ?, ?, ?)
                """,
                    (doc_id, title, content, author),
                )

                conn.commit()

    def batch_index(self, documents: List[Dict]):
        """批量索引文档"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                for doc in documents:
                    doc_id = doc.get("id", "")
                    title = doc.get("title", "")
                    content = doc.get("content", "")
                    source_type = doc.get("source_type", "article")
                    author = doc.get("author", "")
                    created_at = doc.get("created_at", datetime.now().isoformat())

                    pinyin_title = self.pinyin.to_full_pinyin(title)
                    pinyin_content = self.pinyin.to_full_pinyin(content)

                    conn.execute(
                        """
                        INSERT OR REPLACE INTO search_index
                        (id, title, content, source_type, author, created_at, pinyin_title, pinyin_content)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            doc_id,
                            title,
                            content,
                            source_type,
                            author,
                            created_at,
                            pinyin_title,
                            pinyin_content,
                        ),
                    )

                    conn.execute(
                        """
                        INSERT OR REPLACE INTO search_fts (id, title, content, author)
                        VALUES (?, ?, ?, ?)
                    """,
                        (doc_id, title, content, author),
                    )

                conn.commit()

        logger.info(f"批量索引完成: {len(documents)} 条文档")

    def search(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        source_type: str = None,
        order_by: str = "relevance",
    ) -> List[SearchResult]:
        """搜索"""
        results = []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            fts_query = self._build_fts_query(query)

            sql = """
                SELECT s.id, s.title, s.content, s.source_type, s.author, s.created_at,
                       search_fts.rank as score
                FROM search_fts
                JOIN search_index s ON search_fts.id = s.id
                WHERE search_fts MATCH ?
            """
            params = [fts_query]

            if source_type:
                sql += " AND s.source_type = ?"
                params.append(source_type)

            if order_by == "relevance":
                sql += " ORDER BY score"
            elif order_by == "date":
                sql += " ORDER BY s.created_at DESC"

            sql += f" LIMIT {limit} OFFSET {offset}"

            try:
                cursor = conn.execute(sql, params)
                for row in cursor.fetchall():
                    highlights = self._extract_highlights(row["content"], query)
                    results.append(
                        SearchResult(
                            id=row["id"],
                            title=row["title"],
                            content=row["content"],
                            source_type=row["source_type"],
                            author=row["author"],
                            created_at=row["created_at"],
                            score=abs(row["score"]),
                            highlights=highlights,
                        )
                    )
            except sqlite3.OperationalError as e:
                logger.warning(f"FTS 搜索失败，使用 LIKE 搜索: {e}")
                results = self._fallback_search(query, limit, offset, source_type)

        return results

    def _build_fts_query(self, query: str) -> str:
        """构建 FTS 查询"""
        query = query.strip()
        if not query:
            return "*"

        words = query.split()
        fts_words = [f'"{word}"*' for word in words if len(word) > 0]
        return " OR ".join(fts_words)

    def _fallback_search(
        self, query: str, limit: int, offset: int, source_type: str = None
    ) -> List[SearchResult]:
        """回退搜索（LIKE）"""
        results = []
        like_query = f"%{query}%"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            sql = """
                SELECT id, title, content, source_type, author, created_at
                FROM search_index
                WHERE (title LIKE ? OR content LIKE ? OR pinyin_title LIKE ? OR pinyin_content LIKE ?)
            """
            params = [like_query, like_query, like_query, like_query]

            if source_type:
                sql += " AND source_type = ?"
                params.append(source_type)

            sql += f" LIMIT {limit} OFFSET {offset}"

            cursor = conn.execute(sql, params)
            for row in cursor.fetchall():
                highlights = self._extract_highlights(row["content"], query)
                results.append(
                    SearchResult(
                        id=row["id"],
                        title=row["title"],
                        content=row["content"],
                        source_type=row["source_type"],
                        author=row["author"],
                        created_at=row["created_at"],
                        score=1.0,
                        highlights=highlights,
                    )
                )

        return results

    def _extract_highlights(
        self, content: str, query: str, max_length: int = 100
    ) -> List[str]:
        """提取高亮片段"""
        highlights = []
        words = query.split()

        for word in words:
            if len(word) < 2:
                continue

            idx = content.lower().find(word.lower())
            if idx >= 0:
                start = max(0, idx - 30)
                end = min(len(content), idx + len(word) + 30)
                snippet = content[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(content):
                    snippet = snippet + "..."
                highlights.append(snippet)

                if len(highlights) >= 3:
                    break

        return highlights

    def get_suggestions(self, prefix: str, limit: int = 10) -> List[SearchSuggestion]:
        """获取搜索建议"""
        suggestions = []

        if len(prefix) < 1:
            return suggestions

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            like_query = f"{prefix}%"

            cursor = conn.execute(
                """
                SELECT title, COUNT(*) as cnt
                FROM search_index
                WHERE title LIKE ?
                GROUP BY title
                ORDER BY cnt DESC
                LIMIT ?
            """,
                (like_query, limit),
            )

            for row in cursor.fetchall():
                suggestions.append(
                    SearchSuggestion(text=row["title"], type="title", count=row["cnt"])
                )

            if len(suggestions) < limit:
                cursor = conn.execute(
                    """
                    SELECT author, COUNT(*) as cnt
                    FROM search_index
                    WHERE author LIKE ?
                    GROUP BY author
                    ORDER BY cnt DESC
                    LIMIT ?
                """,
                    (like_query, limit - len(suggestions)),
                )

                for row in cursor.fetchall():
                    suggestions.append(
                        SearchSuggestion(
                            text=row["author"], type="author", count=row["cnt"]
                        )
                    )

        return suggestions

    def search_by_pinyin(
        self, pinyin_query: str, limit: int = 20
    ) -> List[SearchResult]:
        """拼音搜索"""
        results = []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            like_query = f"%{pinyin_query}%"

            cursor = conn.execute(
                """
                SELECT id, title, content, source_type, author, created_at
                FROM search_index
                WHERE pinyin_title LIKE ? OR pinyin_content LIKE ?
                LIMIT ?
            """,
                (like_query, like_query, limit),
            )

            for row in cursor.fetchall():
                results.append(
                    SearchResult(
                        id=row["id"],
                        title=row["title"],
                        content=row["content"],
                        source_type=row["source_type"],
                        author=row["author"],
                        created_at=row["created_at"],
                        score=1.0,
                    )
                )

        return results

    def get_stats(self) -> Dict:
        """获取索引统计"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM search_index")
            total_docs = cursor.fetchone()[0]

            cursor = conn.execute(
                "SELECT COUNT(DISTINCT source_type) FROM search_index"
            )
            source_types = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(DISTINCT author) FROM search_index")
            authors = cursor.fetchone()[0]

            return {
                "total_documents": total_docs,
                "source_types": source_types,
                "unique_authors": authors,
            }

    def clear_index(self):
        """清空索引"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM search_index")
            conn.execute("DELETE FROM search_fts")
            conn.commit()

    def remove_document(self, doc_id: str):
        """删除文档索引"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM search_index WHERE id = ?", (doc_id,))
            conn.execute("DELETE FROM search_fts WHERE id = ?", (doc_id,))
            conn.commit()


advanced_search = AdvancedSearchEngine()


__all__ = [
    "SearchResult",
    "SearchSuggestion",
    "PinyinConverter",
    "AdvancedSearchEngine",
    "advanced_search",
]
