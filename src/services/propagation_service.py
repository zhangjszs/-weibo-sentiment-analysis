#!/usr/bin/env python3
"""
传播路径分析服务模块
功能：转发链路追踪、关键节点识别、传播速度分析
"""

import logging
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """节点类型"""

    ORIGIN = "origin"
    FORWARDER = "forwarder"
    KEY_NODE = "key_node"
    TERMINAL = "terminal"


@dataclass
class PropagationNode:
    """传播节点"""

    id: str
    user_id: str
    username: str
    parent_id: Optional[str] = None
    node_type: NodeType = NodeType.FORWARDER
    forward_count: int = 0
    follower_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    depth: int = 0
    children: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "parent_id": self.parent_id,
            "node_type": self.node_type.value,
            "forward_count": self.forward_count,
            "follower_count": self.follower_count,
            "created_at": self.created_at.isoformat(),
            "depth": self.depth,
            "children": self.children,
            "metadata": self.metadata,
        }


@dataclass
class PropagationEdge:
    """传播边"""

    source_id: str
    target_id: str
    timestamp: datetime
    weight: float = 1.0

    def to_dict(self) -> Dict:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "timestamp": self.timestamp.isoformat(),
            "weight": self.weight,
        }


@dataclass
class PropagationPath:
    """传播路径"""

    path_id: str
    nodes: List[str]
    edges: List[Tuple[str, str]]
    total_depth: int
    total_nodes: int
    propagation_time: float

    def to_dict(self) -> Dict:
        return {
            "path_id": self.path_id,
            "nodes": self.nodes,
            "edges": [{"source": e[0], "target": e[1]} for e in self.edges],
            "total_depth": self.total_depth,
            "total_nodes": self.total_nodes,
            "propagation_time": self.propagation_time,
        }


@dataclass
class KeyNodeInfo:
    """关键节点信息"""

    node_id: str
    user_id: str
    username: str
    degree_centrality: float
    betweenness_centrality: float
    influence_score: float
    reach_count: int
    is_key_propagator: bool

    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "user_id": self.user_id,
            "username": self.username,
            "degree_centrality": self.degree_centrality,
            "betweenness_centrality": self.betweenness_centrality,
            "influence_score": self.influence_score,
            "reach_count": self.reach_count,
            "is_key_propagator": self.is_key_propagator,
        }


@dataclass
class PropagationStats:
    """传播统计"""

    total_nodes: int
    total_edges: int
    max_depth: int
    avg_depth: float
    total_paths: int
    origin_node: str
    key_nodes: List[str]
    propagation_speed: float
    peak_time: Optional[datetime]

    def to_dict(self) -> Dict:
        return {
            "total_nodes": self.total_nodes,
            "total_edges": self.total_edges,
            "max_depth": self.max_depth,
            "avg_depth": self.avg_depth,
            "total_paths": self.total_paths,
            "origin_node": self.origin_node,
            "key_nodes": self.key_nodes,
            "propagation_speed": self.propagation_speed,
            "peak_time": self.peak_time.isoformat() if self.peak_time else None,
        }


class PropagationGraph:
    """传播图"""

    def __init__(self):
        self.nodes: Dict[str, PropagationNode] = {}
        self.edges: List[PropagationEdge] = []
        self.adjacency: Dict[str, List[str]] = defaultdict(list)
        self.reverse_adjacency: Dict[str, List[str]] = defaultdict(list)
        self._lock = threading.RLock()

    def add_node(self, node: PropagationNode):
        """添加节点"""
        with self._lock:
            self.nodes[node.id] = node

    def add_edge(self, edge: PropagationEdge):
        """添加边"""
        with self._lock:
            self.edges.append(edge)
            self.adjacency[edge.source_id].append(edge.target_id)
            self.reverse_adjacency[edge.target_id].append(edge.source_id)

            if edge.target_id in self.nodes:
                target_node = self.nodes[edge.target_id]
                if edge.source_id not in target_node.children:
                    target_node.children.append(edge.source_id)

    def get_node(self, node_id: str) -> Optional[PropagationNode]:
        """获取节点"""
        return self.nodes.get(node_id)

    def get_children(self, node_id: str) -> List[str]:
        """获取子节点（转发者）"""
        return self.adjacency.get(node_id, [])

    def get_parent(self, node_id: str) -> Optional[str]:
        """获取父节点（被转发者）"""
        parents = self.reverse_adjacency.get(node_id, [])
        return parents[0] if parents else None

    def get_node_count(self) -> int:
        """获取节点数量"""
        return len(self.nodes)

    def get_edge_count(self) -> int:
        """获取边数量"""
        return len(self.edges)


class PropagationTracer:
    """传播链路追踪器"""

    def __init__(self, graph: PropagationGraph = None):
        self.graph = graph or PropagationGraph()

    def add_propagation(
        self,
        post_id: str,
        user_id: str,
        username: str,
        parent_id: Optional[str] = None,
        follower_count: int = 0,
        created_at: datetime = None,
    ) -> PropagationNode:
        """添加传播节点"""
        if created_at is None:
            created_at = datetime.now()

        depth = 0
        node_type = NodeType.ORIGIN

        if parent_id:
            parent_node = self.graph.get_node(parent_id)
            if parent_node:
                depth = parent_node.depth + 1
                node_type = NodeType.FORWARDER

        node = PropagationNode(
            id=post_id,
            user_id=user_id,
            username=username,
            parent_id=parent_id,
            node_type=node_type,
            follower_count=follower_count,
            created_at=created_at,
            depth=depth,
        )

        self.graph.add_node(node)

        if parent_id:
            edge = PropagationEdge(
                source_id=parent_id, target_id=post_id, timestamp=created_at
            )
            self.graph.add_edge(edge)

        return node

    def trace_path(
        self, start_node_id: str, max_depth: int = 10
    ) -> List[PropagationPath]:
        """追踪从指定节点出发的所有路径"""
        paths = []

        def dfs(
            node_id: str,
            current_path: List[str],
            current_edges: List[Tuple[str, str]],
            depth: int,
        ):
            if depth > max_depth:
                return

            current_path.append(node_id)
            children = self.graph.get_children(node_id)

            if not children:
                if len(current_path) > 1:
                    origin_time = self.graph.get_node(current_path[0]).created_at
                    end_time = self.graph.get_node(current_path[-1]).created_at
                    prop_time = (end_time - origin_time).total_seconds()

                    paths.append(
                        PropagationPath(
                            path_id=f"path_{len(paths)}",
                            nodes=list(current_path),
                            edges=list(current_edges),
                            total_depth=len(current_path) - 1,
                            total_nodes=len(current_path),
                            propagation_time=prop_time,
                        )
                    )
            else:
                for child_id in children:
                    current_edges.append((node_id, child_id))
                    dfs(child_id, current_path, current_edges, depth + 1)
                    current_edges.pop()

            current_path.pop()

        dfs(start_node_id, [], [], 0)
        return paths

    def trace_upstream(self, node_id: str, max_depth: int = 10) -> List[str]:
        """追溯上游路径（找到原始发布者）"""
        path = []
        current_id = node_id

        for _ in range(max_depth):
            node = self.graph.get_node(current_id)
            if not node:
                break

            path.append(current_id)

            if node.parent_id is None:
                break

            current_id = node.parent_id

        return path

    def get_propagation_tree(self, root_id: str) -> Dict:
        """获取传播树结构"""

        def build_tree(node_id: str) -> Dict:
            node = self.graph.get_node(node_id)
            if not node:
                return {}

            children = self.graph.get_children(node_id)
            return {
                "id": node_id,
                "user_id": node.user_id,
                "username": node.username,
                "depth": node.depth,
                "children": [build_tree(child_id) for child_id in children],
            }

        return build_tree(root_id)

    def get_all_paths_to_node(self, target_id: str) -> List[List[str]]:
        """获取所有到达目标节点的路径"""
        all_paths = []

        def bfs_paths():
            queue = deque([(target_id, [target_id])])

            while queue:
                current_id, path = queue.popleft()

                parent_id = self.graph.get_parent(current_id)
                if parent_id is None:
                    all_paths.append(list(reversed(path)))
                else:
                    new_path = path + [parent_id]
                    queue.append((parent_id, new_path))

        bfs_paths()
        return all_paths


class KeyNodeIdentifier:
    """关键节点识别器"""

    def __init__(self, graph: PropagationGraph):
        self.graph = graph

    def calculate_degree_centrality(self, node_id: str) -> float:
        """计算度中心性"""
        out_degree = len(self.graph.get_children(node_id))
        in_degree = len(self.graph.reverse_adjacency.get(node_id, []))
        total_degree = out_degree + in_degree

        n = self.graph.get_node_count()
        if n <= 1:
            return 0.0

        max_degree = 2 * (n - 1)
        return total_degree / max_degree

    def calculate_betweenness_centrality(self, node_id: str) -> float:
        """计算介数中心性（简化版）"""
        node = self.graph.get_node(node_id)
        if not node:
            return 0.0

        betweenness = 0.0
        all_nodes = list(self.graph.nodes.keys())

        for source in all_nodes:
            if source == node_id:
                continue

            for target in all_nodes:
                if target == node_id or target == source:
                    continue

                paths = self._find_shortest_paths(source, target)
                if not paths:
                    continue

                paths_through_node = sum(1 for p in paths if node_id in p)
                betweenness += paths_through_node / len(paths)

        n = len(all_nodes)
        if n <= 2:
            return 0.0

        return betweenness / ((n - 1) * (n - 2))

    def _find_shortest_paths(self, source: str, target: str) -> List[List[str]]:
        """查找最短路径（BFS）"""
        paths = []
        queue = deque([(source, [source])])
        min_length = float("inf")

        while queue:
            current, path = queue.popleft()

            if len(path) > min_length:
                continue

            if current == target:
                if len(path) < min_length:
                    min_length = len(path)
                    paths = [path]
                elif len(path) == min_length:
                    paths.append(path)
                continue

            for child in self.graph.get_children(current):
                if child not in path:
                    queue.append((child, path + [child]))

            parent = self.graph.get_parent(current)
            if parent and parent not in path:
                queue.append((parent, path + [parent]))

        return paths

    def calculate_influence_score(self, node_id: str) -> float:
        """计算影响力评分"""
        node = self.graph.get_node(node_id)
        if not node:
            return 0.0

        follower_score = min(node.follower_count / 10000, 1.0)

        reach_count = self._calculate_reach(node_id)
        reach_score = min(reach_count / 100, 1.0)

        depth_score = 1.0 / (node.depth + 1)

        influence = 0.4 * follower_score + 0.4 * reach_score + 0.2 * depth_score
        return influence

    def _calculate_reach(self, node_id: str) -> int:
        """计算传播范围（下游节点数）"""
        visited = set()
        count = 0

        def dfs(current_id: str):
            nonlocal count
            visited.add(current_id)
            count += 1

            for child_id in self.graph.get_children(current_id):
                if child_id not in visited:
                    dfs(child_id)

        dfs(node_id)
        return count - 1

    def identify_key_nodes(self, threshold: float = 0.3) -> List[KeyNodeInfo]:
        """识别关键节点"""
        key_nodes = []

        for node_id, node in self.graph.nodes.items():
            degree_cent = self.calculate_degree_centrality(node_id)
            between_cent = self.calculate_betweenness_centrality(node_id)
            influence = self.calculate_influence_score(node_id)
            reach = self._calculate_reach(node_id)

            is_key = (
                degree_cent > threshold
                or between_cent > threshold
                or influence > threshold
            )

            if is_key or node.node_type == NodeType.ORIGIN:
                key_nodes.append(
                    KeyNodeInfo(
                        node_id=node_id,
                        user_id=node.user_id,
                        username=node.username,
                        degree_centrality=round(degree_cent, 4),
                        betweenness_centrality=round(between_cent, 4),
                        influence_score=round(influence, 4),
                        reach_count=reach,
                        is_key_propagator=is_key,
                    )
                )

        return sorted(key_nodes, key=lambda x: x.influence_score, reverse=True)


class PropagationSpeedAnalyzer:
    """传播速度分析器"""

    def __init__(self, graph: PropagationGraph):
        self.graph = graph

    def calculate_propagation_speed(self, time_window_minutes: int = 60) -> float:
        """计算传播速度（节点/分钟）"""
        if not self.graph.edges:
            return 0.0

        timestamps = [e.timestamp for e in self.graph.edges]
        if not timestamps:
            return 0.0

        min_time = min(timestamps)
        max_time = max(timestamps)

        duration_minutes = (max_time - min_time).total_seconds() / 60
        if duration_minutes < 1:
            duration_minutes = 1

        total_nodes = self.graph.get_node_count()
        return total_nodes / duration_minutes

    def get_propagation_timeline(self, interval_minutes: int = 5) -> List[Dict]:
        """获取传播时间线"""
        if not self.graph.nodes:
            return []

        timestamps = [n.created_at for n in self.graph.nodes.values()]
        min_time = min(timestamps)
        max_time = max(timestamps)

        timeline = []
        current_time = min_time

        while current_time <= max_time:
            next_time = current_time + timedelta(minutes=interval_minutes)

            count = sum(1 for t in timestamps if current_time <= t < next_time)

            timeline.append(
                {
                    "time": current_time.isoformat(),
                    "count": count,
                    "cumulative": sum(t["count"] for t in timeline) + count,
                }
            )

            current_time = next_time

        return timeline

    def detect_peak_time(self) -> Optional[datetime]:
        """检测传播峰值时间"""
        timeline = self.get_propagation_timeline(interval_minutes=5)
        if not timeline:
            return None

        peak = max(timeline, key=lambda x: x["count"])
        return datetime.fromisoformat(peak["time"])

    def calculate_propagation_metrics(self) -> Dict:
        """计算传播指标"""
        timeline = self.get_propagation_timeline()

        if not timeline:
            return {
                "initial_speed": 0,
                "peak_speed": 0,
                "avg_speed": 0,
                "decay_rate": 0,
                "total_duration_minutes": 0,
            }

        speeds = [t["count"] for t in timeline]
        total_duration = len(timeline) * 5

        initial_speed = sum(speeds[:3]) / 15 if len(speeds) >= 3 else speeds[0] / 5
        peak_speed = max(speeds) / 5
        avg_speed = sum(speeds) / total_duration if total_duration > 0 else 0

        decay_rate = 0
        if len(speeds) >= 2:
            peak_idx = speeds.index(max(speeds))
            if peak_idx < len(speeds) - 1:
                post_peak = speeds[peak_idx:]
                if post_peak[0] > 0:
                    decay_rate = (post_peak[0] - post_peak[-1]) / post_peak[0]

        return {
            "initial_speed": round(initial_speed, 2),
            "peak_speed": round(peak_speed, 2),
            "avg_speed": round(avg_speed, 2),
            "decay_rate": round(decay_rate, 4),
            "total_duration_minutes": total_duration,
        }

    def predict_reach(self, hours_ahead: int = 24) -> Dict:
        """预测传播范围"""
        metrics = self.calculate_propagation_metrics()
        current_nodes = self.graph.get_node_count()

        avg_speed = metrics["avg_speed"]
        decay_rate = metrics["decay_rate"]

        predicted_nodes = current_nodes
        for hour in range(hours_ahead):
            new_nodes = avg_speed * 60 * (1 - decay_rate) ** hour
            predicted_nodes += new_nodes

        return {
            "current_nodes": current_nodes,
            "predicted_nodes": int(predicted_nodes),
            "prediction_horizon_hours": hours_ahead,
            "confidence": max(0.5, 1 - decay_rate),
        }


class PropagationAnalysisService:
    """传播分析服务"""

    def __init__(self):
        self.graph = PropagationGraph()
        self.tracer = PropagationTracer(self.graph)
        self.key_identifier = KeyNodeIdentifier(self.graph)
        self.speed_analyzer = PropagationSpeedAnalyzer(self.graph)
        self._lock = threading.RLock()

    def add_propagation(
        self,
        post_id: str,
        user_id: str,
        username: str,
        parent_id: Optional[str] = None,
        follower_count: int = 0,
        created_at: datetime = None,
    ) -> PropagationNode:
        """添加传播记录"""
        with self._lock:
            return self.tracer.add_propagation(
                post_id, user_id, username, parent_id, follower_count, created_at
            )

    def trace_propagation(self, post_id: str) -> Dict:
        """追踪传播路径"""
        with self._lock:
            paths = self.tracer.trace_path(post_id)
            tree = self.tracer.get_propagation_tree(post_id)

            return {
                "post_id": post_id,
                "paths": [p.to_dict() for p in paths],
                "tree": tree,
                "total_paths": len(paths),
            }

    def identify_key_nodes(self, threshold: float = 0.3) -> List[Dict]:
        """识别关键节点"""
        with self._lock:
            key_nodes = self.key_identifier.identify_key_nodes(threshold)
            return [kn.to_dict() for kn in key_nodes]

    def analyze_speed(self) -> Dict:
        """分析传播速度"""
        with self._lock:
            metrics = self.speed_analyzer.calculate_propagation_metrics()
            timeline = self.speed_analyzer.get_propagation_timeline()
            peak_time = self.speed_analyzer.detect_peak_time()
            prediction = self.speed_analyzer.predict_reach()

            return {
                "metrics": metrics,
                "timeline": timeline,
                "peak_time": peak_time.isoformat() if peak_time else None,
                "prediction": prediction,
            }

    def get_full_analysis(self, origin_id: str = None) -> Dict:
        """获取完整分析"""
        with self._lock:
            stats = PropagationStats(
                total_nodes=self.graph.get_node_count(),
                total_edges=self.graph.get_edge_count(),
                max_depth=max((n.depth for n in self.graph.nodes.values()), default=0),
                avg_depth=sum(n.depth for n in self.graph.nodes.values())
                / max(len(self.graph.nodes), 1),
                total_paths=0,
                origin_node=origin_id or "",
                key_nodes=[],
                propagation_speed=self.speed_analyzer.calculate_propagation_speed(),
                peak_time=self.speed_analyzer.detect_peak_time(),
            )

            key_nodes = self.key_identifier.identify_key_nodes()
            stats.key_nodes = [kn.node_id for kn in key_nodes[:5]]

            return {
                "stats": stats.to_dict(),
                "key_nodes": [kn.to_dict() for kn in key_nodes],
                "speed_analysis": self.analyze_speed(),
            }

    def get_visualization_data(self, root_id: str = None) -> Dict:
        """获取可视化数据"""
        with self._lock:
            nodes = []
            edges = []

            for node_id, node in self.graph.nodes.items():
                nodes.append(
                    {
                        "id": node_id,
                        "label": node.username,
                        "depth": node.depth,
                        "type": node.node_type.value,
                        "follower_count": node.follower_count,
                    }
                )

            for edge in self.graph.edges:
                edges.append(
                    {
                        "source": edge.source_id,
                        "target": edge.target_id,
                        "timestamp": edge.timestamp.isoformat(),
                    }
                )

            return {
                "nodes": nodes,
                "edges": edges,
                "total_nodes": len(nodes),
                "total_edges": len(edges),
            }

    def clear(self):
        """清空数据"""
        with self._lock:
            self.graph = PropagationGraph()
            self.tracer = PropagationTracer(self.graph)
            self.key_identifier = KeyNodeIdentifier(self.graph)
            self.speed_analyzer = PropagationSpeedAnalyzer(self.graph)


propagation_service = PropagationAnalysisService()


__all__ = [
    "NodeType",
    "PropagationNode",
    "PropagationEdge",
    "PropagationPath",
    "KeyNodeInfo",
    "PropagationStats",
    "PropagationGraph",
    "PropagationTracer",
    "KeyNodeIdentifier",
    "PropagationSpeedAnalyzer",
    "PropagationAnalysisService",
    "propagation_service",
]
