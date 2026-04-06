#!/usr/bin/env python3
"""
传播路径分析服务单元测试
测试内容：
- 空数据时图构建不报错
- 统计结果是 dict 类型
- 节点/边数量字段存在
"""

import os
import sys
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.propagation_service import (
    KeyNodeIdentifier,
    KeyNodeInfo,
    NodeType,
    PropagationAnalysisService,
    PropagationEdge,
    PropagationGraph,
    PropagationNode,
    PropagationSpeedAnalyzer,
    PropagationStats,
    PropagationTracer,
)


class TestPropagationGraph:
    """测试传播图"""

    def test_empty_graph_no_error(self):
        """空数据时图构建不报错"""
        graph = PropagationGraph()
        assert graph.get_node_count() == 0
        assert graph.get_edge_count() == 0

    def test_add_node(self):
        """应该能添加节点"""
        graph = PropagationGraph()
        node = PropagationNode(
            id="node_1",
            user_id="user_1",
            username="测试用户",
            node_type=NodeType.ORIGIN,
        )
        graph.add_node(node)
        assert graph.get_node_count() == 1
        assert graph.get_node("node_1") is not None

    def test_add_edge(self):
        """应该能添加边"""
        graph = PropagationGraph()

        # 添加两个节点
        node1 = PropagationNode(id="node_1", user_id="user_1", username="用户1")
        node2 = PropagationNode(id="node_2", user_id="user_2", username="用户2")
        graph.add_node(node1)
        graph.add_node(node2)

        # 添加边
        edge = PropagationEdge(
            source_id="node_1",
            target_id="node_2",
            timestamp=datetime.now(),
        )
        graph.add_edge(edge)
        assert graph.get_edge_count() == 1

    def test_get_children(self):
        """应该能获取子节点"""
        graph = PropagationGraph()

        node1 = PropagationNode(id="node_1", user_id="user_1", username="用户1")
        node2 = PropagationNode(id="node_2", user_id="user_2", username="用户2")
        graph.add_node(node1)
        graph.add_node(node2)

        edge = PropagationEdge(
            source_id="node_1",
            target_id="node_2",
            timestamp=datetime.now(),
        )
        graph.add_edge(edge)

        children = graph.get_children("node_1")
        assert "node_2" in children


class TestPropagationStats:
    """测试传播统计"""

    def test_stats_is_dict(self):
        """统计结果应该是 dict 类型"""
        stats = PropagationStats(
            total_nodes=10,
            total_edges=9,
            max_depth=3,
            avg_depth=1.5,
            total_paths=5,
            origin_node="node_1",
            key_nodes=["node_1", "node_2"],
            propagation_speed=2.5,
            peak_time=datetime.now(),
        )
        data = stats.to_dict()
        assert isinstance(data, dict)

    def test_stats_contains_required_fields(self):
        """统计结果应该包含必要字段"""
        stats = PropagationStats(
            total_nodes=10,
            total_edges=9,
            max_depth=3,
            avg_depth=1.5,
            total_paths=5,
            origin_node="node_1",
            key_nodes=["node_1", "node_2"],
            propagation_speed=2.5,
            peak_time=datetime.now(),
        )
        data = stats.to_dict()
        assert "total_nodes" in data
        assert "total_edges" in data
        assert "max_depth" in data
        assert "avg_depth" in data
        assert "total_paths" in data
        assert "origin_node" in data
        assert "key_nodes" in data
        assert "propagation_speed" in data


class TestPropagationNode:
    """测试传播节点"""

    def test_node_creation(self):
        """应该能创建节点"""
        node = PropagationNode(
            id="node_1",
            user_id="user_1",
            username="测试用户",
            node_type=NodeType.ORIGIN,
            forward_count=10,
            follower_count=1000,
            depth=0,
        )
        assert node.id == "node_1"
        assert node.user_id == "user_1"
        assert node.username == "测试用户"
        assert node.node_type == NodeType.ORIGIN
        assert node.forward_count == 10
        assert node.follower_count == 1000
        assert node.depth == 0

    def test_node_to_dict(self):
        """节点应该能转换为字典"""
        node = PropagationNode(
            id="node_1",
            user_id="user_1",
            username="测试用户",
            node_type=NodeType.FORWARDER,
        )
        data = node.to_dict()
        assert isinstance(data, dict)
        assert data["id"] == "node_1"
        assert data["user_id"] == "user_1"
        assert data["node_type"] == "forwarder"


class TestPropagationTracer:
    """测试传播链路追踪器"""

    def test_add_propagation_origin(self):
        """应该能添加原始节点"""
        tracer = PropagationTracer()
        node = tracer.add_propagation(
            post_id="post_1",
            user_id="user_1",
            username="用户1",
            parent_id=None,
        )
        assert node.node_type == NodeType.ORIGIN
        assert node.depth == 0
        assert node.parent_id is None

    def test_add_propagation_forward(self):
        """应该能添加转发节点"""
        tracer = PropagationTracer()

        # 先添加原始节点
        tracer.add_propagation(
            post_id="post_1",
            user_id="user_1",
            username="用户1",
            parent_id=None,
        )

        # 添加转发节点
        node = tracer.add_propagation(
            post_id="post_2",
            user_id="user_2",
            username="用户2",
            parent_id="post_1",
        )
        assert node.node_type == NodeType.FORWARDER
        assert node.depth == 1
        assert node.parent_id == "post_1"

    def test_trace_upstream(self):
        """应该能追溯上游路径"""
        tracer = PropagationTracer()

        # 构建传播链
        tracer.add_propagation("post_1", "user_1", "用户1", None)
        tracer.add_propagation("post_2", "user_2", "用户2", "post_1")
        tracer.add_propagation("post_3", "user_3", "用户3", "post_2")

        path = tracer.trace_upstream("post_3")
        assert "post_3" in path
        assert "post_2" in path
        assert "post_1" in path

    def test_trace_path_linear_chain(self):
        """DFS 应该能追踪线性传播链"""
        tracer = PropagationTracer()

        # 构建线性链: post_1 -> post_2 -> post_3
        tracer.add_propagation("post_1", "user_1", "用户1", None)
        tracer.add_propagation("post_2", "user_2", "用户2", "post_1")
        tracer.add_propagation("post_3", "user_3", "用户3", "post_2")

        paths = tracer.trace_path("post_1")

        # 应该找到一条路径
        assert len(paths) == 1
        assert paths[0].nodes == ["post_1", "post_2", "post_3"]
        assert paths[0].total_depth == 2

    def test_trace_path_branching(self):
        """DFS 应该能处理分支结构"""
        tracer = PropagationTracer()

        # 构建分支结构: post_1 -> post_2, post_3
        tracer.add_propagation("post_1", "user_1", "用户1", None)
        tracer.add_propagation("post_2", "user_2", "用户2", "post_1")
        tracer.add_propagation("post_3", "user_3", "用户3", "post_1")

        paths = tracer.trace_path("post_1")

        # 应该找到两条路径
        assert len(paths) == 2
        path_nodes = [p.nodes for p in paths]
        assert ["post_1", "post_2"] in path_nodes
        assert ["post_1", "post_3"] in path_nodes

    def test_trace_path_max_depth_limit(self):
        """DFS 应该遵守最大深度限制"""
        tracer = PropagationTracer()

        # 构建长链: post_1 -> post_2 -> post_3 -> post_4 -> post_5
        tracer.add_propagation("post_1", "user_1", "用户1", None)
        tracer.add_propagation("post_2", "user_2", "用户2", "post_1")
        tracer.add_propagation("post_3", "user_3", "用户3", "post_2")
        tracer.add_propagation("post_4", "user_4", "用户4", "post_3")
        tracer.add_propagation("post_5", "user_5", "用户5", "post_4")

        # 限制深度为 2
        paths = tracer.trace_path("post_1", max_depth=2)

        # 所有路径深度都不应该超过 2
        for path in paths:
            assert path.total_depth <= 2

    def test_trace_path_empty_graph(self):
        """DFS 在空图上应该返回空列表"""
        tracer = PropagationTracer()

        # 不添加任何节点
        paths = tracer.trace_path("non_existent")

        assert paths == []

    def test_trace_path_single_node(self):
        """DFS 对单节点应该返回空路径列表（没有边）"""
        tracer = PropagationTracer()

        # 只添加一个节点
        tracer.add_propagation("post_1", "user_1", "用户1", None)

        paths = tracer.trace_path("post_1")

        # 单节点没有路径（路径需要至少两个节点）
        assert len(paths) == 0


class TestKeyNodeIdentifier:
    """测试关键节点识别器"""

    def test_calculate_degree_centrality(self):
        """应该能计算度中心性"""
        graph = PropagationGraph()

        # 构建简单图
        node1 = PropagationNode(id="node_1", user_id="user_1", username="用户1")
        node2 = PropagationNode(id="node_2", user_id="user_2", username="用户2")
        node3 = PropagationNode(id="node_3", user_id="user_3", username="用户3")

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)

        graph.add_edge(PropagationEdge("node_1", "node_2", datetime.now()))
        graph.add_edge(PropagationEdge("node_1", "node_3", datetime.now()))

        identifier = KeyNodeIdentifier(graph)
        centrality = identifier.calculate_degree_centrality("node_1")
        assert isinstance(centrality, float)
        assert centrality >= 0

    def test_identify_key_nodes(self):
        """应该能识别关键节点"""
        graph = PropagationGraph()

        # 构建图
        node1 = PropagationNode(id="node_1", user_id="user_1", username="用户1", node_type=NodeType.ORIGIN)
        node2 = PropagationNode(id="node_2", user_id="user_2", username="用户2")
        node3 = PropagationNode(id="node_3", user_id="user_3", username="用户3")

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)

        graph.add_edge(PropagationEdge("node_1", "node_2", datetime.now()))
        graph.add_edge(PropagationEdge("node_1", "node_3", datetime.now()))

        identifier = KeyNodeIdentifier(graph)
        key_nodes = identifier.identify_key_nodes(threshold=0.1)
        assert isinstance(key_nodes, list)
        # 原始节点应该被识别为关键节点
        assert any(kn.node_id == "node_1" for kn in key_nodes)


class TestPropagationSpeedAnalyzer:
    """测试传播速度分析器"""

    def test_calculate_propagation_speed(self):
        """应该能计算传播速度"""
        graph = PropagationGraph()

        # 添加带时间戳的边
        base_time = datetime.now()
        node1 = PropagationNode(id="node_1", user_id="user_1", username="用户1")
        node2 = PropagationNode(id="node_2", user_id="user_2", username="用户2")

        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_edge(PropagationEdge("node_1", "node_2", base_time + timedelta(minutes=10)))

        analyzer = PropagationSpeedAnalyzer(graph)
        speed = analyzer.calculate_propagation_speed()
        assert isinstance(speed, float)
        assert speed >= 0

    def test_get_propagation_timeline(self):
        """应该能获取传播时间线"""
        graph = PropagationGraph()

        base_time = datetime.now()
        node1 = PropagationNode(id="node_1", user_id="user_1", username="用户1", created_at=base_time)
        node2 = PropagationNode(id="node_2", user_id="user_2", username="用户2", created_at=base_time + timedelta(minutes=10))

        graph.add_node(node1)
        graph.add_node(node2)

        analyzer = PropagationSpeedAnalyzer(graph)
        timeline = analyzer.get_propagation_timeline(interval_minutes=5)
        assert isinstance(timeline, list)


class TestPropagationAnalysisService:
    """测试传播分析服务"""

    def test_service_creation(self):
        """应该能创建服务实例"""
        service = PropagationAnalysisService()
        assert service is not None

    def test_add_propagation(self):
        """应该能添加传播记录"""
        service = PropagationAnalysisService()
        node = service.add_propagation(
            post_id="post_1",
            user_id="user_1",
            username="用户1",
            parent_id=None,
        )
        assert node.id == "post_1"
        assert node.node_type == NodeType.ORIGIN

    def test_get_full_analysis(self):
        """应该能获取完整分析"""
        service = PropagationAnalysisService()

        # 添加一些数据
        service.add_propagation("post_1", "user_1", "用户1", None)
        service.add_propagation("post_2", "user_2", "用户2", "post_1")

        analysis = service.get_full_analysis(origin_id="post_1")
        assert isinstance(analysis, dict)
        assert "stats" in analysis
        assert "key_nodes" in analysis
        assert "speed_analysis" in analysis

    def test_get_visualization_data(self):
        """应该能获取可视化数据"""
        service = PropagationAnalysisService()

        # 添加一些数据
        service.add_propagation("post_1", "user_1", "用户1", None)
        service.add_propagation("post_2", "user_2", "用户2", "post_1")

        viz_data = service.get_visualization_data(root_id="post_1")
        assert isinstance(viz_data, dict)
        assert "nodes" in viz_data
        assert "edges" in viz_data
        assert "total_nodes" in viz_data
        assert "total_edges" in viz_data

    def test_clear(self):
        """应该能清空数据"""
        service = PropagationAnalysisService()

        # 添加数据
        service.add_propagation("post_1", "user_1", "用户1", None)

        # 清空
        service.clear()

        # 验证清空
        viz_data = service.get_visualization_data()
        assert viz_data["total_nodes"] == 0
        assert viz_data["total_edges"] == 0

    def test_clear_and_readd_data(self):
        """clear() 后应该能重新添加数据并正常工作 - 回归测试"""
        service = PropagationAnalysisService()

        # 第一轮：添加数据并验证
        service.add_propagation("post_1", "user_1", "用户1", None)
        service.add_propagation("post_2", "user_2", "用户2", "post_1")

        viz_data_1 = service.get_visualization_data()
        assert viz_data_1["total_nodes"] == 2
        assert viz_data_1["total_edges"] == 1

        # 清空数据
        service.clear()

        viz_data_cleared = service.get_visualization_data()
        assert viz_data_cleared["total_nodes"] == 0
        assert viz_data_cleared["total_edges"] == 0

        # 第二轮：重新添加数据（使用不同的ID）
        service.add_propagation("new_post_1", "new_user_1", "新用户1", None)
        service.add_propagation("new_post_2", "new_user_2", "新用户2", "new_post_1")
        service.add_propagation("new_post_3", "new_user_3", "新用户3", "new_post_2")

        # 验证新数据正确
        viz_data_2 = service.get_visualization_data()
        assert viz_data_2["total_nodes"] == 3
        assert viz_data_2["total_edges"] == 2

        # 验证可以获取完整分析
        analysis = service.get_full_analysis(origin_id="new_post_1")
        assert analysis["stats"]["total_nodes"] == 3
        assert len(analysis["key_nodes"]) >= 0

    def test_clear_and_readd_same_ids(self):
        """clear() 后使用相同ID重新添加数据应该正常工作"""
        service = PropagationAnalysisService()

        # 第一轮：添加数据
        service.add_propagation("post_1", "user_1", "用户1", None)
        service.add_propagation("post_2", "user_2", "用户2", "post_1")

        # 清空
        service.clear()

        # 第二轮：使用相同ID重新添加
        service.add_propagation("post_1", "user_1_new", "用户1新", None)
        service.add_propagation("post_2", "user_2_new", "用户2新", "post_1")

        # 验证数据正确
        viz_data = service.get_visualization_data()
        assert viz_data["total_nodes"] == 2

        # 验证是新数据
        node = service.graph.get_node("post_1")
        assert node.username == "用户1新"

    def test_clear_preserves_service_state(self):
        """clear() 后服务实例应该保持可用状态"""
        service = PropagationAnalysisService()

        # 添加数据后清空
        for i in range(10):
            service.add_propagation(f"post_{i}", f"user_{i}", f"用户{i}",
                                   parent_id=None if i == 0 else f"post_{i-1}")

        service.clear()

        # 验证所有方法仍然可用
        # 1. 可以添加新数据
        service.add_propagation("test_1", "test_user", "测试用户", None)

        # 2. 可以获取可视化数据
        viz = service.get_visualization_data()
        assert viz["total_nodes"] == 1

        # 3. 可以获取完整分析
        analysis = service.get_full_analysis(origin_id="test_1")
        assert "stats" in analysis

        # 4. 可以追踪传播
        trace = service.trace_propagation("test_1")
        assert "post_id" in trace


class TestKeyNodeInfo:
    """测试关键节点信息"""

    def test_key_node_info_creation(self):
        """应该能创建关键节点信息"""
        info = KeyNodeInfo(
            node_id="node_1",
            user_id="user_1",
            username="测试用户",
            degree_centrality=0.5,
            betweenness_centrality=0.3,
            influence_score=0.8,
            reach_count=100,
            is_key_propagator=True,
        )
        assert info.node_id == "node_1"
        assert info.influence_score == 0.8
        assert info.is_key_propagator is True

    def test_key_node_info_to_dict(self):
        """关键节点信息应该能转换为字典"""
        info = KeyNodeInfo(
            node_id="node_1",
            user_id="user_1",
            username="测试用户",
            degree_centrality=0.5,
            betweenness_centrality=0.3,
            influence_score=0.8,
            reach_count=100,
            is_key_propagator=True,
        )
        data = info.to_dict()
        assert isinstance(data, dict)
        assert data["node_id"] == "node_1"
        assert data["influence_score"] == 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
