#!/usr/bin/env python3
"""
传播路径分析服务单元测试
"""

import sys
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, "src")


class TestPropagationNode:
    """传播节点测试"""

    def test_init(self):
        """测试初始化"""
        from services.propagation_service import NodeType, PropagationNode

        node = PropagationNode(id="post-001", user_id="user-001", username="测试用户")

        assert node.id == "post-001"
        assert node.user_id == "user-001"
        assert node.node_type == NodeType.FORWARDER
        assert node.depth == 0

    def test_to_dict(self):
        """测试序列化"""
        from services.propagation_service import PropagationNode

        node = PropagationNode(
            id="post-001", user_id="user-001", username="测试用户", depth=2
        )

        result = node.to_dict()

        assert result["id"] == "post-001"
        assert result["depth"] == 2


class TestPropagationGraph:
    """传播图测试"""

    def test_init(self):
        """测试初始化"""
        from services.propagation_service import PropagationGraph

        graph = PropagationGraph()

        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_add_node(self):
        """测试添加节点"""
        from services.propagation_service import PropagationGraph, PropagationNode

        graph = PropagationGraph()
        node = PropagationNode(id="post-001", user_id="user-001", username="用户1")

        graph.add_node(node)

        assert graph.get_node_count() == 1
        assert graph.get_node("post-001") is not None

    def test_add_edge(self):
        """测试添加边"""
        from services.propagation_service import PropagationEdge, PropagationGraph

        graph = PropagationGraph()
        edge = PropagationEdge(
            source_id="post-001", target_id="post-002", timestamp=datetime.now()
        )

        graph.add_edge(edge)

        assert graph.get_edge_count() == 1
        assert "post-002" in graph.get_children("post-001")


class TestPropagationTracer:
    """传播追踪器测试"""

    @pytest.fixture
    def tracer(self):
        """创建追踪器"""
        from services.propagation_service import PropagationTracer

        return PropagationTracer()

    def test_add_origin_propagation(self, tracer):
        """测试添加原始传播"""
        node = tracer.add_propagation(
            post_id="post-001", user_id="user-001", username="原始发布者"
        )

        from services.propagation_service import NodeType

        assert node.node_type == NodeType.ORIGIN
        assert node.depth == 0
        assert node.parent_id is None

    def test_add_forward_propagation(self, tracer):
        """测试添加转发传播"""
        tracer.add_propagation(
            post_id="post-001", user_id="user-001", username="原始发布者"
        )

        node = tracer.add_propagation(
            post_id="post-002",
            user_id="user-002",
            username="转发者1",
            parent_id="post-001",
        )

        from services.propagation_service import NodeType

        assert node.node_type == NodeType.FORWARDER
        assert node.depth == 1
        assert node.parent_id == "post-001"

    def test_trace_path(self, tracer):
        """测试路径追踪"""
        tracer.add_propagation("post-001", "user-001", "用户1")
        tracer.add_propagation("post-002", "user-002", "用户2", "post-001")
        tracer.add_propagation("post-003", "user-003", "用户3", "post-002")

        paths = tracer.trace_path("post-001")

        assert len(paths) >= 1

    def test_trace_upstream(self, tracer):
        """测试上游追溯"""
        tracer.add_propagation("post-001", "user-001", "用户1")
        tracer.add_propagation("post-002", "user-002", "用户2", "post-001")
        tracer.add_propagation("post-003", "user-003", "用户3", "post-002")

        path = tracer.trace_upstream("post-003")

        assert len(path) == 3
        assert path[-1] == "post-001"

    def test_get_propagation_tree(self, tracer):
        """测试获取传播树"""
        tracer.add_propagation("post-001", "user-001", "用户1")
        tracer.add_propagation("post-002", "user-002", "用户2", "post-001")
        tracer.add_propagation("post-003", "user-003", "用户3", "post-001")

        tree = tracer.get_propagation_tree("post-001")

        assert tree["id"] == "post-001"
        assert len(tree["children"]) == 2


class TestKeyNodeIdentifier:
    """关键节点识别器测试"""

    @pytest.fixture
    def setup_graph(self):
        """设置图数据"""
        from services.propagation_service import (
            PropagationEdge,
            PropagationGraph,
            PropagationNode,
        )

        graph = PropagationGraph()

        nodes = [
            PropagationNode(
                id="post-001",
                user_id="user-001",
                username="用户1",
                follower_count=10000,
            ),
            PropagationNode(
                id="post-002", user_id="user-002", username="用户2", follower_count=5000
            ),
            PropagationNode(
                id="post-003", user_id="user-003", username="用户3", follower_count=1000
            ),
            PropagationNode(
                id="post-004", user_id="user-004", username="用户4", follower_count=500
            ),
        ]

        for node in nodes:
            graph.add_node(node)

        edges = [
            PropagationEdge("post-001", "post-002", datetime.now()),
            PropagationEdge("post-001", "post-003", datetime.now()),
            PropagationEdge("post-002", "post-004", datetime.now()),
        ]

        for edge in edges:
            graph.add_edge(edge)

        return graph

    def test_calculate_degree_centrality(self, setup_graph):
        """测试度中心性计算"""
        from services.propagation_service import KeyNodeIdentifier

        identifier = KeyNodeIdentifier(setup_graph)
        centrality = identifier.calculate_degree_centrality("post-001")

        assert centrality >= 0

    def test_calculate_influence_score(self, setup_graph):
        """测试影响力评分计算"""
        from services.propagation_service import KeyNodeIdentifier

        identifier = KeyNodeIdentifier(setup_graph)
        score = identifier.calculate_influence_score("post-001")

        assert 0 <= score <= 1

    def test_identify_key_nodes(self, setup_graph):
        """测试关键节点识别"""
        from services.propagation_service import KeyNodeIdentifier

        identifier = KeyNodeIdentifier(setup_graph)
        key_nodes = identifier.identify_key_nodes(threshold=0.1)

        assert len(key_nodes) >= 1


class TestPropagationSpeedAnalyzer:
    """传播速度分析器测试"""

    @pytest.fixture
    def setup_graph(self):
        """设置图数据"""
        from services.propagation_service import (
            PropagationEdge,
            PropagationGraph,
            PropagationNode,
        )

        graph = PropagationGraph()
        base_time = datetime.now() - timedelta(hours=2)

        for i in range(10):
            node = PropagationNode(
                id=f"post-{i:03d}",
                user_id=f"user-{i:03d}",
                username=f"用户{i}",
                created_at=base_time + timedelta(minutes=i * 10),
            )
            graph.add_node(node)

            if i > 0:
                edge = PropagationEdge(
                    f"post-{(i - 1):03d}",
                    f"post-{i:03d}",
                    base_time + timedelta(minutes=i * 10),
                )
                graph.add_edge(edge)

        return graph

    def test_calculate_propagation_speed(self, setup_graph):
        """测试传播速度计算"""
        from services.propagation_service import PropagationSpeedAnalyzer

        analyzer = PropagationSpeedAnalyzer(setup_graph)
        speed = analyzer.calculate_propagation_speed()

        assert speed >= 0

    def test_get_propagation_timeline(self, setup_graph):
        """测试传播时间线"""
        from services.propagation_service import PropagationSpeedAnalyzer

        analyzer = PropagationSpeedAnalyzer(setup_graph)
        timeline = analyzer.get_propagation_timeline()

        assert len(timeline) >= 1
        assert "time" in timeline[0]
        assert "count" in timeline[0]

    def test_detect_peak_time(self, setup_graph):
        """测试峰值时间检测"""
        from services.propagation_service import PropagationSpeedAnalyzer

        analyzer = PropagationSpeedAnalyzer(setup_graph)
        peak_time = analyzer.detect_peak_time()

        assert peak_time is not None

    def test_calculate_propagation_metrics(self, setup_graph):
        """测试传播指标计算"""
        from services.propagation_service import PropagationSpeedAnalyzer

        analyzer = PropagationSpeedAnalyzer(setup_graph)
        metrics = analyzer.calculate_propagation_metrics()

        assert "initial_speed" in metrics
        assert "peak_speed" in metrics
        assert "avg_speed" in metrics
        assert "decay_rate" in metrics

    def test_predict_reach(self, setup_graph):
        """测试传播预测"""
        from services.propagation_service import PropagationSpeedAnalyzer

        analyzer = PropagationSpeedAnalyzer(setup_graph)
        prediction = analyzer.predict_reach(hours_ahead=24)

        assert "current_nodes" in prediction
        assert "predicted_nodes" in prediction
        assert prediction["predicted_nodes"] >= prediction["current_nodes"]


class TestPropagationAnalysisService:
    """传播分析服务测试"""

    @pytest.fixture
    def service(self):
        """创建服务实例"""
        from services.propagation_service import PropagationAnalysisService

        return PropagationAnalysisService()

    def test_add_propagation(self, service):
        """测试添加传播"""
        from services.propagation_service import NodeType

        node = service.add_propagation(
            post_id="post-001", user_id="user-001", username="用户1"
        )

        assert node.node_type == NodeType.ORIGIN

    def test_trace_propagation(self, service):
        """测试追踪传播"""
        service.add_propagation("post-001", "user-001", "用户1")
        service.add_propagation("post-002", "user-002", "用户2", "post-001")

        result = service.trace_propagation("post-001")

        assert "paths" in result
        assert "tree" in result

    def test_identify_key_nodes(self, service):
        """测试识别关键节点"""
        service.add_propagation("post-001", "user-001", "用户1", follower_count=10000)
        service.add_propagation("post-002", "user-002", "用户2", "post-001")
        service.add_propagation("post-003", "user-003", "用户3", "post-001")

        key_nodes = service.identify_key_nodes()

        assert isinstance(key_nodes, list)

    def test_analyze_speed(self, service):
        """测试分析速度"""
        base_time = datetime.now() - timedelta(hours=1)

        for i in range(5):
            service.add_propagation(
                f"post-{i:03d}",
                f"user-{i:03d}",
                f"用户{i}",
                parent_id=f"post-{(i - 1):03d}" if i > 0 else None,
                created_at=base_time + timedelta(minutes=i * 10),
            )

        result = service.analyze_speed()

        assert "metrics" in result
        assert "timeline" in result

    def test_get_full_analysis(self, service):
        """测试完整分析"""
        service.add_propagation("post-001", "user-001", "用户1")
        service.add_propagation("post-002", "user-002", "用户2", "post-001")

        result = service.get_full_analysis("post-001")

        assert "stats" in result
        assert "key_nodes" in result
        assert "speed_analysis" in result

    def test_get_visualization_data(self, service):
        """测试可视化数据"""
        service.add_propagation("post-001", "user-001", "用户1")
        service.add_propagation("post-002", "user-002", "用户2", "post-001")

        result = service.get_visualization_data()

        assert "nodes" in result
        assert "edges" in result
        assert result["total_nodes"] == 2
        assert result["total_edges"] == 1

    def test_clear(self, service):
        """测试清空数据"""
        service.add_propagation("post-001", "user-001", "用户1")

        service.clear()

        result = service.get_visualization_data()
        assert result["total_nodes"] == 0


class TestIntegration:
    """集成测试"""

    def test_full_propagation_analysis(self):
        """测试完整传播分析流程"""
        from services.propagation_service import PropagationAnalysisService

        service = PropagationAnalysisService()
        base_time = datetime.now() - timedelta(hours=2)

        service.add_propagation(
            "post-000",
            "user-000",
            "KOL用户",
            follower_count=50000,
            created_at=base_time,
        )

        for i in range(1, 11):
            parent = f"post-{(i - 1):03d}"
            service.add_propagation(
                f"post-{i:03d}",
                f"user-{i:03d}",
                f"用户{i}",
                parent_id=parent,
                follower_count=1000 * (10 - i),
                created_at=base_time + timedelta(minutes=i * 5),
            )

        service.add_propagation(
            "post-011",
            "user-011",
            "分支用户1",
            parent_id="post-005",
            created_at=base_time + timedelta(minutes=30),
        )
        service.add_propagation(
            "post-012",
            "user-012",
            "分支用户2",
            parent_id="post-005",
            created_at=base_time + timedelta(minutes=35),
        )

        key_nodes = service.identify_key_nodes()
        assert len(key_nodes) >= 1

        speed_analysis = service.analyze_speed()
        assert "metrics" in speed_analysis

        full_analysis = service.get_full_analysis("post-000")
        assert full_analysis["stats"]["total_nodes"] == 13


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
