#!/usr/bin/env python3
"""
传播路径分析模块
功能：转发链路追踪、传播路径可视化、KOL影响力分析
"""

import logging
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class PropagationNode:
    """传播节点"""

    id: str
    user_id: str
    user_name: str
    content: str
    post_time: datetime
    repost_count: int = 0
    comment_count: int = 0
    like_count: int = 0
    depth: int = 0
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    influence_score: float = 0.0
    is_kol: bool = False

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "content": self.content[:100] + "..."
            if len(self.content) > 100
            else self.content,
            "post_time": self.post_time.isoformat() if self.post_time else None,
            "repost_count": self.repost_count,
            "comment_count": self.comment_count,
            "like_count": self.like_count,
            "depth": self.depth,
            "parent_id": self.parent_id,
            "children": self.children,
            "influence_score": round(self.influence_score, 4),
            "is_kol": self.is_kol,
        }


@dataclass
class PropagationEdge:
    """传播边"""

    source: str
    target: str
    weight: float = 1.0
    propagation_time: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "target": self.target,
            "weight": self.weight,
            "propagation_time": self.propagation_time,
        }


@dataclass
class PropagationPath:
    """传播路径"""

    origin_id: str
    origin_user: str
    total_depth: int
    total_nodes: int
    total_reposts: int
    propagation_speed: float
    key_nodes: List[str]
    kol_nodes: List[str]

    def to_dict(self) -> Dict:
        return {
            "origin_id": self.origin_id,
            "origin_user": self.origin_user,
            "total_depth": self.total_depth,
            "total_nodes": self.total_nodes,
            "total_reposts": self.total_reposts,
            "propagation_speed": round(self.propagation_speed, 2),
            "key_nodes": self.key_nodes,
            "kol_nodes": self.kol_nodes,
        }


class KOLDetector:
    """KOL（关键意见领袖）检测器"""

    def __init__(self, thresholds: Dict[str, float] = None):
        self.thresholds = thresholds or {
            "min_followers": 10000,
            "min_reposts": 100,
            "min_engagement_rate": 0.05,
            "influence_threshold": 0.7,
        }

    def calculate_influence_score(
        self,
        repost_count: int,
        comment_count: int,
        like_count: int,
        follower_count: int = 0,
        verified: bool = False,
    ) -> float:
        """
        计算影响力得分

        综合考虑转发、评论、点赞、粉丝数、认证状态
        """
        engagement = repost_count * 3 + comment_count * 2 + like_count

        engagement_score = min(1.0, engagement / 10000)

        follower_score = min(1.0, math.log10(max(follower_count, 1)) / 6)

        verified_bonus = 0.1 if verified else 0

        influence_score = (
            engagement_score * 0.5 + follower_score * 0.3 + verified_bonus * 0.2
        )

        return min(1.0, influence_score)

    def is_kol(
        self,
        repost_count: int,
        comment_count: int,
        like_count: int,
        follower_count: int = 0,
        verified: bool = False,
        influence_score: float = None,
    ) -> bool:
        """判断是否为KOL"""
        if influence_score is None:
            influence_score = self.calculate_influence_score(
                repost_count, comment_count, like_count, follower_count, verified
            )

        if influence_score >= self.thresholds["influence_threshold"]:
            return True

        if repost_count >= self.thresholds["min_reposts"]:
            return True

        if follower_count >= self.thresholds["min_followers"]:
            return True

        return False


class PropagationAnalyzer:
    """传播路径分析器"""

    def __init__(self):
        self.nodes: Dict[str, PropagationNode] = {}
        self.edges: List[PropagationEdge] = []
        self.kol_detector = KOLDetector()
        self._node_index: Dict[str, Set[str]] = defaultdict(set)

    def add_node(self, node: PropagationNode):
        """添加传播节点"""
        node.influence_score = self.kol_detector.calculate_influence_score(
            node.repost_count, node.comment_count, node.like_count
        )
        node.is_kol = self.kol_detector.is_kol(
            node.repost_count,
            node.comment_count,
            node.like_count,
            influence_score=node.influence_score,
        )

        self.nodes[node.id] = node
        self._node_index[node.user_id].add(node.id)

        if node.parent_id and node.parent_id in self.nodes:
            self.nodes[node.parent_id].children.append(node.id)
            self.edges.append(
                PropagationEdge(
                    source=node.parent_id,
                    target=node.id,
                    weight=node.influence_score + 0.5,
                )
            )

    def build_from_reposts(self, reposts: List[Dict]) -> int:
        """
        从转发数据构建传播图

        Args:
            reposts: 转发数据列表

        Returns:
            int: 构建的节点数量
        """
        self.nodes.clear()
        self.edges.clear()
        self._node_index.clear()

        for repost in reposts:
            node = PropagationNode(
                id=str(repost.get("id", "")),
                user_id=str(repost.get("user_id", "")),
                user_name=repost.get("user_name", "匿名用户"),
                content=repost.get("content", ""),
                post_time=repost.get("post_time") or datetime.now(),
                repost_count=repost.get("repost_count", 0),
                comment_count=repost.get("comment_count", 0),
                like_count=repost.get("like_count", 0),
                depth=repost.get("depth", 0),
                parent_id=repost.get("parent_id"),
            )
            self.add_node(node)

        return len(self.nodes)

    def get_origin_node(self) -> Optional[PropagationNode]:
        """获取原始节点（深度为0的节点）"""
        for node in self.nodes.values():
            if node.depth == 0:
                return node
        return None

    def calculate_propagation_speed(self) -> float:
        """计算传播速度（节点/小时）"""
        if len(self.nodes) < 2:
            return 0.0

        times = [n.post_time for n in self.nodes.values() if n.post_time]
        if len(times) < 2:
            return 0.0

        min_time = min(times)
        max_time = max(times)

        hours = (max_time - min_time).total_seconds() / 3600
        if hours == 0:
            return float(len(self.nodes))

        return len(self.nodes) / hours

    def get_depth_distribution(self) -> Dict[int, int]:
        """获取传播深度分布"""
        distribution = defaultdict(int)
        for node in self.nodes.values():
            distribution[node.depth] += 1
        return dict(sorted(distribution.items()))

    def get_key_nodes(self, top_n: int = 10) -> List[PropagationNode]:
        """获取关键传播节点"""
        sorted_nodes = sorted(
            self.nodes.values(),
            key=lambda n: (n.repost_count + n.comment_count + n.like_count),
            reverse=True,
        )
        return sorted_nodes[:top_n]

    def get_kol_nodes(self) -> List[PropagationNode]:
        """获取KOL节点"""
        return [n for n in self.nodes.values() if n.is_kol]

    def analyze_propagation_path(self) -> PropagationPath:
        """分析传播路径"""
        origin = self.get_origin_node()
        kol_nodes = self.get_kol_nodes()
        key_nodes = self.get_key_nodes(5)

        return PropagationPath(
            origin_id=origin.id if origin else "",
            origin_user=origin.user_name if origin else "",
            total_depth=max((n.depth for n in self.nodes.values()), default=0),
            total_nodes=len(self.nodes),
            total_reposts=sum(n.repost_count for n in self.nodes.values()),
            propagation_speed=self.calculate_propagation_speed(),
            key_nodes=[n.id for n in key_nodes],
            kol_nodes=[n.id for n in kol_nodes],
        )

    def get_graph_data(self) -> Dict[str, Any]:
        """获取图可视化数据"""
        nodes = []
        for node in self.nodes.values():
            node_data = node.to_dict()
            node_data["label"] = node.user_name
            node_data["value"] = node.influence_score
            node_data["category"] = 0 if node.is_kol else (1 if node.depth == 0 else 2)
            nodes.append(node_data)

        edges = [e.to_dict() for e in self.edges]

        return {
            "nodes": nodes,
            "edges": edges,
            "categories": [
                {"name": "KOL", "itemStyle": {"color": "#EF4444"}},
                {"name": "原始发布", "itemStyle": {"color": "#2563EB"}},
                {"name": "普通转发", "itemStyle": {"color": "#64748B"}},
            ],
        }

    def get_user_influence_ranking(self, top_n: int = 20) -> List[Dict]:
        """获取用户影响力排名"""
        user_stats = defaultdict(
            lambda: {
                "repost_count": 0,
                "comment_count": 0,
                "like_count": 0,
                "node_count": 0,
                "influence_score": 0.0,
            }
        )

        for node in self.nodes.values():
            stats = user_stats[node.user_id]
            stats["repost_count"] += node.repost_count
            stats["comment_count"] += node.comment_count
            stats["like_count"] += node.like_count
            stats["node_count"] += 1
            stats["user_name"] = node.user_name
            stats["influence_score"] = max(
                stats["influence_score"], node.influence_score
            )

        ranking = sorted(
            [
                {"user_id": uid, "user_name": stats["user_name"], **stats}
                for uid, stats in user_stats.items()
            ],
            key=lambda x: x["influence_score"],
            reverse=True,
        )

        return ranking[:top_n]

    def get_time_distribution(self, interval_minutes: int = 60) -> List[Dict]:
        """获取时间分布"""
        if not self.nodes:
            return []

        times = [n.post_time for n in self.nodes.values() if n.post_time]
        if not times:
            return []

        min_time = min(times)
        max_time = max(times)

        distribution = []
        current_time = min_time

        while current_time <= max_time:
            next_time = current_time + timedelta(minutes=interval_minutes)

            count = sum(1 for t in times if current_time <= t < next_time)

            distribution.append({"time": current_time.isoformat(), "count": count})

            current_time = next_time

        return distribution

    def get_summary(self) -> Dict[str, Any]:
        """获取传播分析摘要"""
        path = self.analyze_propagation_path()
        depth_dist = self.get_depth_distribution()
        kol_nodes = self.get_kol_nodes()
        key_nodes = self.get_key_nodes(5)
        user_ranking = self.get_user_influence_ranking(10)
        time_dist = self.get_time_distribution()

        return {
            "path": path.to_dict(),
            "depth_distribution": depth_dist,
            "kol_count": len(kol_nodes),
            "kol_nodes": [n.to_dict() for n in kol_nodes[:5]],
            "key_nodes": [n.to_dict() for n in key_nodes],
            "user_ranking": user_ranking,
            "time_distribution": time_dist,
            "graph_data": self.get_graph_data(),
        }


propagation_analyzer = PropagationAnalyzer()
