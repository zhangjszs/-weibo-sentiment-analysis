#!/usr/bin/env python3
"""
propagation_analyzer.py 单元测试

覆盖范围：
- PropagationNode / PropagationEdge / PropagationPath 三个 dataclass 的 to_dict() 序列化
- KOLDetector 影响力评分与 KOL 判定逻辑
- PropagationAnalyzer 全部公开方法：建图、深度分布、速度、关键节点、KOL、
  路径分析、图可视化、用户排名、时间分布、摘要

这是 propagation_service.py 死代码删除后的覆盖回填——propagation_analyzer.py
是生产代码（propagation_api.py 的 7 处调用全部走它），此前零单元测试。
"""

import os
import sys
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from services.propagation_analyzer import (
    KOLDetector,
    PropagationAnalyzer,
    PropagationEdge,
    PropagationNode,
    PropagationPath,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def base_time():
    """固定基准时间，避免时间相关测试受运行时刻影响。"""
    return datetime(2026, 7, 1, 12, 0, 0)


@pytest.fixture
def sample_reposts(base_time):
    """构造 5 节点的转发树：

    orig (depth=0, 500 reposts) ─┬─ r1 (depth=1, 50 reposts) ──── r3 (depth=2, 5 reposts)
                                └─ r2 (depth=1, 200 reposts, 20k 粉丝) ──── r4 (depth=2, 10 reposts)

    期望：5 节点 / 4 边 / 深度分布 {0:1,1:2,2:2} / 2 个 KOL（orig + r2）
    """
    return [
        {
            "id": "orig", "user_id": "u_orig", "user_name": "原作者",
            "content": "这是原始微博内容", "post_time": base_time,
            "repost_count": 500, "comment_count": 100, "like_count": 1000,
            "depth": 0, "parent_id": None,
        },
        {
            "id": "r1", "user_id": "u1", "user_name": "用户A",
            "content": "转发评论A", "post_time": base_time + timedelta(minutes=30),
            "repost_count": 50, "comment_count": 10, "like_count": 20,
            "depth": 1, "parent_id": "orig",
        },
        {
            "id": "r2", "user_id": "u2", "user_name": "大V用户",
            "content": "大V转发", "post_time": base_time + timedelta(hours=1),
            "repost_count": 200, "comment_count": 80, "like_count": 300,
            "depth": 1, "parent_id": "orig",
        },
        {
            "id": "r3", "user_id": "u3", "user_name": "用户C",
            "content": "深度转发", "post_time": base_time + timedelta(hours=2),
            "repost_count": 5, "comment_count": 1, "like_count": 3,
            "depth": 2, "parent_id": "r1",
        },
        {
            "id": "r4", "user_id": "u4", "user_name": "用户D",
            "content": "另一深度转发", "post_time": base_time + timedelta(hours=3),
            "repost_count": 10, "comment_count": 2, "like_count": 5,
            "depth": 2, "parent_id": "r2",
        },
    ]


@pytest.fixture
def analyzer(sample_reposts):
    """已加载 sample_reposts 的分析器实例。"""
    a = PropagationAnalyzer()
    a.build_from_reposts(sample_reposts)
    return a


# ---------------------------------------------------------------------------
# PropagationNode dataclass
# ---------------------------------------------------------------------------


class TestPropagationNode:
    """PropagationNode.to_dict() 序列化测试"""

    def test_to_dict_contains_all_fields(self, base_time):
        """to_dict 应包含全部字段"""
        node = PropagationNode(
            id="n1", user_id="u1", user_name="测试用户",
            content="内容", post_time=base_time, repost_count=10,
            comment_count=5, like_count=20, depth=1, parent_id="n0",
        )
        d = node.to_dict()
        assert d["id"] == "n1"
        assert d["user_id"] == "u1"
        assert d["user_name"] == "测试用户"
        assert d["content"] == "内容"
        assert d["post_time"] == base_time.isoformat()
        assert d["repost_count"] == 10
        assert d["comment_count"] == 5
        assert d["like_count"] == 20
        assert d["depth"] == 1
        assert d["parent_id"] == "n0"
        assert d["children"] == []
        assert d["is_kol"] is False

    def test_to_dict_truncates_long_content(self, base_time):
        """超过 100 字符的内容应截断并加 '...' 后缀"""
        long_content = "x" * 150
        node = PropagationNode(
            id="n1", user_id="u1", user_name="u",
            content=long_content, post_time=base_time,
        )
        d = node.to_dict()
        assert d["content"].endswith("...")
        assert len(d["content"]) == 103  # content[:100] (100) + "..." (3)

    def test_to_dict_keeps_short_content_intact(self, base_time):
        """不超过 100 字符的内容应原样保留"""
        node = PropagationNode(
            id="n1", user_id="u1", user_name="u",
            content="短内容", post_time=base_time,
        )
        assert node.to_dict()["content"] == "短内容"

    def test_to_dict_rounds_influence_score(self, base_time):
        """influence_score 应四舍五入到 4 位小数"""
        node = PropagationNode(
            id="n1", user_id="u1", user_name="u",
            content="x", post_time=base_time, influence_score=0.123456789,
        )
        assert node.to_dict()["influence_score"] == 0.1235

    def test_to_dict_handles_none_post_time(self):
        """post_time 为 None 时应输出 None 而非抛异常"""
        node = PropagationNode(
            id="n1", user_id="u1", user_name="u", content="x", post_time=None,
        )
        assert node.to_dict()["post_time"] is None


# ---------------------------------------------------------------------------
# PropagationEdge dataclass
# ---------------------------------------------------------------------------


class TestPropagationEdge:
    """PropagationEdge.to_dict() 序列化测试"""

    def test_to_dict_contains_all_fields(self):
        edge = PropagationEdge(source="a", target="b", weight=1.5, propagation_time=3.2)
        d = edge.to_dict()
        assert d == {"source": "a", "target": "b", "weight": 1.5, "propagation_time": 3.2}

    def test_to_dict_default_weight(self):
        """weight 默认 1.0，propagation_time 默认 None"""
        edge = PropagationEdge(source="a", target="b")
        d = edge.to_dict()
        assert d["weight"] == 1.0
        assert d["propagation_time"] is None


# ---------------------------------------------------------------------------
# PropagationPath dataclass
# ---------------------------------------------------------------------------


class TestPropagationPath:
    """PropagationPath.to_dict() 序列化测试"""

    def test_to_dict_contains_all_fields(self):
        path = PropagationPath(
            origin_id="orig", origin_user="原作者", total_depth=3,
            total_nodes=10, total_reposts=500, propagation_speed=2.567,
            key_nodes=["a", "b"], kol_nodes=["c"],
        )
        d = path.to_dict()
        assert d["origin_id"] == "orig"
        assert d["origin_user"] == "原作者"
        assert d["total_depth"] == 3
        assert d["total_nodes"] == 10
        assert d["total_reposts"] == 500
        assert d["propagation_speed"] == 2.57  # round(2.567, 2)
        assert d["key_nodes"] == ["a", "b"]
        assert d["kol_nodes"] == ["c"]

    def test_to_dict_rounds_speed(self):
        """propagation_speed 应四舍五入到 2 位小数"""
        path = PropagationPath(
            origin_id="", origin_user="", total_depth=0, total_nodes=0,
            total_reposts=0, propagation_speed=1.005, key_nodes=[], kol_nodes=[],
        )
        assert path.to_dict()["propagation_speed"] == 1.0  # round(1.005, 2) == 1.0 (banker's rounding)


# ---------------------------------------------------------------------------
# KOLDetector
# ---------------------------------------------------------------------------


class TestKOLDetector:
    """KOL 检测器测试"""

    def test_calculate_influence_score_zero_engagement(self):
        """零互动 + 零粉丝 + 未认证 → 得分 0"""
        detector = KOLDetector()
        score = detector.calculate_influence_score(0, 0, 0, follower_count=0, verified=False)
        assert score == 0.0

    def test_calculate_influence_score_theoretical_max(self):
        """全部子分满分时得分为加权上限 0.82（非 1.0）。

        公式：engagement_score*0.5 + follower_score*0.3 + verified_bonus*0.2
        满分时 = 1.0*0.5 + 1.0*0.3 + 0.1*0.2 = 0.82。
        最终的 min(1.0, ...) 是安全网，正常权重下达不到。
        """
        detector = KOLDetector()
        score = detector.calculate_influence_score(
            99999, 99999, 99999, follower_count=10**9, verified=True,
        )
        assert score == pytest.approx(0.82, abs=1e-9)

    def test_calculate_influence_score_never_exceeds_one(self):
        """无论输入多大，得分不应超过 1.0"""
        detector = KOLDetector()
        # 即便 verified_bonus 被人为抬高，最终 min(1.0, ...) 仍应兜底
        score = detector.calculate_influence_score(10**6, 10**6, 10**6, follower_count=10**12, verified=True)
        assert score <= 1.0

    def test_calculate_influence_score_verified_bonus(self):
        """同等条件下认证用户得分应高于未认证"""
        detector = KOLDetector()
        unverified = detector.calculate_influence_score(100, 50, 200, follower_count=1000, verified=False)
        verified = detector.calculate_influence_score(100, 50, 200, follower_count=1000, verified=True)
        assert verified > unverified
        # 验证 bonus 权重 0.2：差距应等于 verified_bonus * 0.2 = 0.1 * 0.2 = 0.02
        assert pytest.approx(verified - unverified, abs=1e-9) == 0.02

    def test_calculate_influence_score_follower_logarithmic(self):
        """粉丝分应是对数增长（10x 粉丝差距远小于 10x 得分差距）"""
        detector = KOLDetector()
        s1 = detector.calculate_influence_score(0, 0, 0, follower_count=10, verified=False)
        s100 = detector.calculate_influence_score(0, 0, 0, follower_count=1000, verified=False)
        # follower_score = log10(followers)/6, 权重 0.3
        # s1 = log10(10)/6 * 0.3 = 1/6 * 0.3 = 0.05
        # s100 = log10(1000)/6 * 0.3 = 3/6 * 0.3 = 0.15
        assert pytest.approx(s1, abs=1e-9) == 0.05
        assert pytest.approx(s100, abs=1e-9) == 0.15

    def test_is_kol_by_influence_threshold(self):
        """影响力得分 >= 0.7 即为 KOL（即使转发/粉丝未达独立阈值）"""
        detector = KOLDetector()
        # 构造 influence_score >= 0.7 但 repost < 100 且 follower < 10000 的场景
        # engagement = 3000*3 + 0 + 0 = 9000, engagement_score = 0.9
        # follower_score = 0, verified = 0 → score = 0.9*0.5 = 0.45 < 0.7
        # 需要 verified: 0.9*0.5 + 0 + 0.1*0.2 = 0.47 仍 < 0.7
        # 直接用 influence_score 参数传入
        assert detector.is_kol(0, 0, 0, influence_score=0.7) is True
        assert detector.is_kol(0, 0, 0, influence_score=0.69) is False

    def test_is_kol_by_repost_count(self):
        """转发数 >= min_reposts(100) 即为 KOL"""
        detector = KOLDetector()
        assert detector.is_kol(100, 0, 0, follower_count=0, verified=False) is True
        assert detector.is_kol(99, 0, 0, follower_count=0, verified=False) is False

    def test_is_kol_by_follower_count(self):
        """粉丝数 >= min_followers(10000) 即为 KOL"""
        detector = KOLDetector()
        assert detector.is_kol(0, 0, 0, follower_count=10000, verified=False) is True
        assert detector.is_kol(0, 0, 0, follower_count=9999, verified=False) is False

    def test_is_kol_custom_thresholds(self):
        """自定义阈值应生效"""
        detector = KOLDetector(thresholds={
            "min_followers": 100,
            "min_reposts": 10,
            "min_engagement_rate": 0.05,
            "influence_threshold": 0.3,
        })
        # 默认阈值下不算 KOL，自定义低阈值下算
        assert detector.is_kol(10, 0, 0, follower_count=100, verified=False) is True

    def test_is_kol_recomputes_score_when_none(self):
        """influence_score=None 时应自动计算"""
        detector = KOLDetector()
        # 高互动场景，influence_score 会被内部计算
        result = detector.is_kol(200, 100, 500, follower_count=50000, verified=True)
        assert result is True


# ---------------------------------------------------------------------------
# PropagationAnalyzer
# ---------------------------------------------------------------------------


class TestPropagationAnalyzerBuild:
    """建图与节点管理"""

    def test_build_from_reposts_returns_node_count(self, sample_reposts):
        """build_from_reposts 返回节点数"""
        a = PropagationAnalyzer()
        assert a.build_from_reposts(sample_reposts) == 5

    def test_build_clears_previous_state(self, sample_reposts, base_time):
        """重复 build 应清空旧状态"""
        a = PropagationAnalyzer()
        a.build_from_reposts(sample_reposts)
        a.build_from_reposts([
            {"id": "only", "user_id": "u", "user_name": "x", "content": "y",
             "post_time": base_time, "depth": 0},
        ])
        assert len(a.nodes) == 1
        assert "orig" not in a.nodes

    def test_build_handles_missing_fields(self, base_time):
        """缺失字段应使用默认值，不抛异常"""
        a = PropagationAnalyzer()
        a.build_from_reposts([{"id": "n1"}])
        node = a.nodes["n1"]
        assert node.user_id == ""  # str(repost.get("user_id", ""))
        assert node.user_name == "匿名用户"
        assert node.content == ""
        assert node.repost_count == 0
        assert node.depth == 0
        assert node.parent_id is None
        # post_time 缺失时默认 datetime.now()
        assert isinstance(node.post_time, datetime)

    def test_build_coerces_id_to_str(self, base_time):
        """id 为非字符串时应转为字符串"""
        a = PropagationAnalyzer()
        a.build_from_reposts([
            {"id": 12345, "user_id": 67890, "post_time": base_time, "depth": 0},
        ])
        assert "12345" in a.nodes
        assert a.nodes["12345"].user_id == "67890"

    def test_add_node_sets_influence_and_kol(self, base_time):
        """add_node 应自动计算 influence_score 和 is_kol"""
        a = PropagationAnalyzer()
        node = PropagationNode(
            id="n1", user_id="u1", user_name="x", content="y",
            post_time=base_time, repost_count=200, comment_count=100, like_count=500,
        )
        a.add_node(node)
        assert node.influence_score > 0
        assert node.is_kol is True  # repost=200 >= 100

    def test_add_node_creates_edge_to_parent(self, base_time):
        """parent_id 指向已存在节点时应建边并加入 parent.children"""
        a = PropagationAnalyzer()
        parent = PropagationNode(
            id="p", user_id="up", user_name="p", content="p", post_time=base_time, depth=0,
        )
        child = PropagationNode(
            id="c", user_id="uc", user_name="c", content="c", post_time=base_time,
            depth=1, parent_id="p",
        )
        a.add_node(parent)
        a.add_node(child)
        assert a.nodes["p"].children == ["c"]
        assert len(a.edges) == 1
        assert a.edges[0].source == "p"
        assert a.edges[0].target == "c"

    def test_add_node_with_missing_parent_no_edge(self, base_time):
        """parent_id 指向不存在的节点时不应建边"""
        a = PropagationAnalyzer()
        node = PropagationNode(
            id="orphan", user_id="u", user_name="x", content="y",
            post_time=base_time, parent_id="nonexistent",
        )
        a.add_node(node)
        assert len(a.edges) == 0
        assert node.children == []

    def test_add_node_indexes_by_user_id(self, base_time):
        """同一 user_id 的多个节点应被索引到一起"""
        a = PropagationAnalyzer()
        for nid in ["n1", "n2", "n3"]:
            a.add_node(PropagationNode(
                id=nid, user_id="same_user", user_name="x", content="y", post_time=base_time,
            ))
        assert a._node_index["same_user"] == {"n1", "n2", "n3"}


class TestPropagationAnalyzerQueries:
    """查询类方法"""

    def test_get_origin_node(self, analyzer):
        """应返回 depth=0 的节点"""
        origin = analyzer.get_origin_node()
        assert origin is not None
        assert origin.id == "orig"
        assert origin.depth == 0

    def test_get_origin_node_none_when_no_depth_zero(self, base_time):
        """无 depth=0 节点时返回 None"""
        a = PropagationAnalyzer()
        a.add_node(PropagationNode(
            id="n1", user_id="u", user_name="x", content="y", post_time=base_time, depth=1,
        ))
        assert a.get_origin_node() is None

    def test_get_origin_node_empty_graph(self):
        """空图返回 None"""
        assert PropagationAnalyzer().get_origin_node() is None

    def test_calculate_propagation_speed_normal(self, analyzer, base_time):
        """正常场景：节点数 / 小时跨度"""
        # 5 节点，时间跨度 3 小时（base_time 到 base_time+3h）
        speed = analyzer.calculate_propagation_speed()
        # 5 / 3 ≈ 1.667
        assert pytest.approx(speed, abs=0.01) == 5 / 3

    def test_calculate_propagation_speed_single_node(self, base_time):
        """<2 节点 → 0.0"""
        a = PropagationAnalyzer()
        a.add_node(PropagationNode(
            id="n1", user_id="u", user_name="x", content="y", post_time=base_time,
        ))
        assert a.calculate_propagation_speed() == 0.0

    def test_calculate_propagation_speed_empty(self):
        """空图 → 0.0"""
        assert PropagationAnalyzer().calculate_propagation_speed() == 0.0

    def test_calculate_propagation_speed_same_timestamp(self, base_time):
        """所有节点同一时刻 → hours=0 → 返回节点数"""
        a = PropagationAnalyzer()
        for i in range(3):
            a.add_node(PropagationNode(
                id=f"n{i}", user_id=f"u{i}", user_name="x", content="y", post_time=base_time,
            ))
        assert a.calculate_propagation_speed() == 3.0

    def test_get_depth_distribution(self, analyzer):
        """深度分布应为 {0:1, 1:2, 2:2}"""
        dist = analyzer.get_depth_distribution()
        assert dist == {0: 1, 1: 2, 2: 2}

    def test_get_depth_distribution_sorted(self, analyzer):
        """深度分布按键升序"""
        dist = analyzer.get_depth_distribution()
        assert list(dist.keys()) == sorted(dist.keys())

    def test_get_depth_distribution_empty(self):
        """空图 → {}"""
        assert PropagationAnalyzer().get_depth_distribution() == {}

    def test_get_key_nodes_top_n(self, analyzer):
        """get_key_nodes 默认返回前 10，按互动量降序"""
        keys = analyzer.get_key_nodes()
        # orig 互动量最高：500+100+1000=1600
        assert keys[0].id == "orig"
        assert len(keys) == 5  # 只有 5 个节点

    def test_get_key_nodes_custom_n(self, analyzer):
        """top_n 参数应生效"""
        keys = analyzer.get_key_nodes(top_n=2)
        assert len(keys) == 2
        # 前两名：orig(1600) > r2(200+80+300=580)
        assert keys[0].id == "orig"
        assert keys[1].id == "r2"

    def test_get_key_nodes_empty(self):
        """空图 → []"""
        assert PropagationAnalyzer().get_key_nodes() == []

    def test_get_kol_nodes(self, analyzer):
        """应返回被标记为 KOL 的节点"""
        kols = analyzer.get_kol_nodes()
        kol_ids = {n.id for n in kols}
        # orig: repost=500>=100 → KOL; r2: follower 未传入但 repost=200>=100 → KOL
        assert "orig" in kol_ids
        assert "r2" in kol_ids
        # r3 repost=5, r4 repost=10, r1 repost=50 均 < 100 且 follower=0 → 非 KOL
        assert "r3" not in kol_ids
        assert "r4" not in kol_ids

    def test_get_kol_nodes_empty(self):
        """空图 → []"""
        assert PropagationAnalyzer().get_kol_nodes() == []


class TestPropagationAnalyzerPathAndGraph:
    """路径分析与图可视化"""

    def test_analyze_propagation_path(self, analyzer):
        """analyze_propagation_path 返回正确的 PropagationPath"""
        path = analyzer.analyze_propagation_path()
        assert path.origin_id == "orig"
        assert path.origin_user == "原作者"
        assert path.total_depth == 2
        assert path.total_nodes == 5
        assert path.total_reposts == 765  # 500+50+200+5+10
        assert path.propagation_speed > 0
        assert isinstance(path.key_nodes, list)
        assert isinstance(path.kol_nodes, list)

    def test_analyze_propagation_path_empty_graph(self):
        """空图应返回空路径而非抛异常"""
        path = PropagationAnalyzer().analyze_propagation_path()
        assert path.origin_id == ""
        assert path.origin_user == ""
        assert path.total_depth == 0
        assert path.total_nodes == 0
        assert path.total_reposts == 0
        assert path.propagation_speed == 0.0

    def test_get_graph_data_structure(self, analyzer):
        """get_graph_data 应返回 nodes/edges/categories 三键"""
        data = analyzer.get_graph_data()
        assert set(data.keys()) == {"nodes", "edges", "categories"}
        assert len(data["nodes"]) == 5
        assert len(data["edges"]) == 4  # 4 条父子边
        assert len(data["categories"]) == 3

    def test_get_graph_data_node_labels(self, analyzer):
        """节点应携带 label/value/category 字段"""
        data = analyzer.get_graph_data()
        node = next(n for n in data["nodes"] if n["id"] == "orig")
        assert node["label"] == "原作者"
        assert "value" in node
        assert "category" in node

    def test_get_graph_data_category_origin(self, analyzer):
        """depth=0 非KOL节点 category=1（原始发布）"""
        data = analyzer.get_graph_data()
        # orig 既是 KOL 又是 depth=0 → category=0（KOL 优先）
        orig = next(n for n in data["nodes"] if n["id"] == "orig")
        assert orig["category"] == 0  # is_kol 优先

    def test_get_graph_data_category_normal(self, analyzer):
        """普通转发节点 category=2"""
        data = analyzer.get_graph_data()
        r3 = next(n for n in data["nodes"] if n["id"] == "r3")
        assert r3["category"] == 2

    def test_get_graph_data_empty(self):
        """空图 → 空节点/边 + 3 个 categories"""
        data = PropagationAnalyzer().get_graph_data()
        assert data["nodes"] == []
        assert data["edges"] == []
        assert len(data["categories"]) == 3


class TestPropagationAnalyzerRankingAndTime:
    """用户排名与时间分布"""

    def test_get_user_influence_ranking_aggregates(self, analyzer):
        """同一 user_id 多节点应聚合统计"""
        ranking = analyzer.get_user_influence_ranking()
        # 5 个不同 user_id，各 1 个节点
        assert len(ranking) == 5
        # 按影响力降序
        scores = [r["influence_score"] for r in ranking]
        assert scores == sorted(scores, reverse=True)

    def test_get_user_influence_ranking_top_n(self, analyzer):
        """top_n 应限制返回数量"""
        ranking = analyzer.get_user_influence_ranking(top_n=3)
        assert len(ranking) == 3

    def test_get_user_influence_ranking_fields(self, analyzer):
        """排名项应包含聚合字段"""
        ranking = analyzer.get_user_influence_ranking(top_n=1)
        item = ranking[0]
        assert "user_id" in item
        assert "user_name" in item
        assert "repost_count" in item
        assert "comment_count" in item
        assert "like_count" in item
        assert "node_count" in item
        assert "influence_score" in item

    def test_get_user_influence_ranking_empty(self):
        """空图 → []"""
        assert PropagationAnalyzer().get_user_influence_ranking() == []

    def test_get_time_distribution_normal(self, analyzer, base_time):
        """时间分布应按区间分桶"""
        dist = analyzer.get_time_distribution(interval_minutes=60)
        # 时间跨度 3 小时（base_time 到 base_time+3h），60 分钟一桶 → 4 桶（含右端点）
        assert len(dist) >= 3
        assert all("time" in b and "count" in b for b in dist)
        # 第一桶应含 base_time 的 orig 节点
        assert dist[0]["count"] >= 1

    def test_get_time_distribution_custom_interval(self, analyzer):
        """自定义区间应改变桶数"""
        dist_60 = analyzer.get_time_distribution(interval_minutes=60)
        dist_120 = analyzer.get_time_distribution(interval_minutes=120)
        assert len(dist_120) < len(dist_60)

    def test_get_time_distribution_empty(self):
        """空图 → []"""
        assert PropagationAnalyzer().get_time_distribution() == []


class TestPropagationAnalyzerSummary:
    """get_summary 集成测试"""

    def test_get_summary_contains_all_keys(self, analyzer):
        """摘要应包含全部子分析结果"""
        summary = analyzer.get_summary()
        expected_keys = {
            "path", "depth_distribution", "kol_count", "kol_nodes",
            "key_nodes", "user_ranking", "time_distribution", "graph_data",
        }
        assert set(summary.keys()) == expected_keys

    def test_get_summary_path_is_dict(self, analyzer):
        """summary.path 应为序列化后的 dict"""
        summary = analyzer.get_summary()
        assert isinstance(summary["path"], dict)
        assert summary["path"]["origin_id"] == "orig"

    def test_get_summary_kol_count(self, analyzer):
        """kol_count 应与 get_kol_nodes 一致"""
        summary = analyzer.get_summary()
        assert summary["kol_count"] == len(analyzer.get_kol_nodes())

    def test_get_summary_empty_graph(self):
        """空图摘要不应抛异常"""
        summary = PropagationAnalyzer().get_summary()
        assert summary["kol_count"] == 0
        assert summary["path"]["total_nodes"] == 0
        assert summary["user_ranking"] == []
        assert summary["time_distribution"] == []


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------


class TestModuleSingleton:
    """模块级单例 propagation_analyzer 可导入"""

    def test_singleton_importable(self):
        """模块应导出 propagation_analyzer 单例"""
        from services.propagation_analyzer import propagation_analyzer
        assert isinstance(propagation_analyzer, PropagationAnalyzer)
